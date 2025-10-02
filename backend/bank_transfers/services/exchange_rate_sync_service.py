"""
Exchange Rate Synchronization Service

Handles synchronization of MNB exchange rates to the database,
including current rates and historical data management.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

from django.db import transaction
from django.utils import timezone

from ..models import ExchangeRate, ExchangeRateSyncLog
from .mnb_client import MNBClient, MNBClientError

logger = logging.getLogger(__name__)


class ExchangeRateSyncService:
    """
    Service for synchronizing exchange rates from MNB to the database.

    Supports:
    - Current rate synchronization (for scheduled tasks)
    - Historical data backfill
    - Rate lookups with caching
    - Currency conversion
    """

    DEFAULT_CURRENCIES = ['USD', 'EUR']

    def __init__(self):
        """Initialize the sync service"""
        self.client = MNBClient()

    def sync_current_rates(self, currencies: Optional[List[str]] = None) -> ExchangeRateSyncLog:
        """
        Synchronize current day's exchange rates from MNB.

        This method is designed for scheduled tasks that run multiple times daily.
        Uses GetCurrentExchangeRates SOAP method for better performance.

        Args:
            currencies: List of currency codes to sync (default: USD, EUR)

        Returns:
            ExchangeRateSyncLog with sync statistics

        Raises:
            MNBClientError: If MNB API call fails
        """
        if currencies is None:
            currencies = self.DEFAULT_CURRENCIES

        logger.info(f"Starting current rate sync for {','.join(currencies)}")

        try:
            # Fetch current rates using dedicated SOAP method
            # Returns tuple: (date_str, rates_dict) - use MNB's actual date!
            rate_date_str, current_rates = self.client.get_current_exchange_rates(currencies)

            # Parse the date string from MNB
            rate_date = datetime.strptime(rate_date_str, '%Y-%m-%d').date()

            # Create sync log with MNB's actual date
            sync_log = ExchangeRateSyncLog.objects.create(
                sync_start_time=timezone.now(),
                currencies_synced=','.join(currencies),
                date_range_start=rate_date,
                date_range_end=rate_date,
                sync_status='RUNNING'
            )

            # Convert to format expected by _save_rates_to_database
            rates_data = {rate_date_str: current_rates} if current_rates else {}

            # Process and save rates
            created_count, updated_count = self._save_rates_to_database(rates_data)

            # Update sync log with success
            sync_log.rates_created = created_count
            sync_log.rates_updated = updated_count
            sync_log.sync_status = 'SUCCESS'
            sync_log.sync_end_time = timezone.now()
            sync_log.save()

            logger.info(
                f"Current rate sync completed: {created_count} created, "
                f"{updated_count} updated"
            )

            return sync_log

        except MNBClientError as e:
            error_msg = f"MNB API error: {str(e)}"
            logger.error(error_msg)

            sync_log.sync_status = 'FAILED'
            sync_log.error_message = error_msg
            sync_log.sync_end_time = timezone.now()
            sync_log.save()

            raise

        except Exception as e:
            error_msg = f"Unexpected error during current rate sync: {str(e)}"
            logger.error(error_msg, exc_info=True)

            sync_log.sync_status = 'FAILED'
            sync_log.error_message = error_msg
            sync_log.sync_end_time = timezone.now()
            sync_log.save()

            raise

    def sync_historical_rates(
        self,
        days_back: int = 30,
        currencies: Optional[List[str]] = None
    ) -> ExchangeRateSyncLog:
        """
        Synchronize historical exchange rates from MNB.

        Useful for:
        - Initial data population
        - Backfilling missing dates
        - Data recovery

        Args:
            days_back: Number of days to sync backwards from today
            currencies: List of currency codes (default: USD, EUR)

        Returns:
            ExchangeRateSyncLog with sync statistics
        """
        if currencies is None:
            currencies = self.DEFAULT_CURRENCIES

        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)

        logger.info(
            f"Starting historical sync from {start_date} to {end_date} "
            f"for {','.join(currencies)}"
        )

        return self.sync_rates_for_date_range(
            start_date=start_date,
            end_date=end_date,
            currencies=currencies
        )

    @transaction.atomic
    def sync_rates_for_date_range(
        self,
        start_date: date,
        end_date: date,
        currencies: Optional[List[str]] = None
    ) -> ExchangeRateSyncLog:
        """
        Synchronize exchange rates for a specific date range.

        Creates or updates ExchangeRate records in the database.
        All operations are wrapped in a database transaction.

        Args:
            start_date: Start date for sync
            end_date: End date for sync
            currencies: List of currency codes (default: USD, EUR)

        Returns:
            ExchangeRateSyncLog with detailed statistics
        """
        if currencies is None:
            currencies = self.DEFAULT_CURRENCIES

        # Create sync log
        sync_log = ExchangeRateSyncLog.objects.create(
            sync_start_time=timezone.now(),
            currencies_synced=','.join(currencies),
            date_range_start=start_date,
            date_range_end=end_date,
            sync_status='RUNNING'
        )

        try:
            # Fetch rates from MNB
            rates_data = self.client.get_exchange_rates(
                start_date=start_date,
                end_date=end_date,
                currencies=currencies
            )

            # Process and save rates
            created_count, updated_count = self._save_rates_to_database(rates_data)

            # Update sync log with success
            sync_log.rates_created = created_count
            sync_log.rates_updated = updated_count
            sync_log.sync_status = 'SUCCESS'
            sync_log.sync_end_time = timezone.now()
            sync_log.save()

            logger.info(
                f"Sync completed successfully: {created_count} created, "
                f"{updated_count} updated"
            )

            return sync_log

        except MNBClientError as e:
            # MNB API error
            error_msg = f"MNB API error: {str(e)}"
            logger.error(error_msg)

            sync_log.sync_status = 'FAILED'
            sync_log.error_message = error_msg
            sync_log.sync_end_time = timezone.now()
            sync_log.save()

            raise

        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error during sync: {str(e)}"
            logger.error(error_msg, exc_info=True)

            sync_log.sync_status = 'FAILED'
            sync_log.error_message = error_msg
            sync_log.sync_end_time = timezone.now()
            sync_log.save()

            raise

    def _save_rates_to_database(
        self,
        rates_data: Dict[str, Dict[str, Decimal]]
    ) -> Tuple[int, int]:
        """
        Save exchange rates to database with upsert logic.

        Args:
            rates_data: Nested dict {date_str: {currency: rate}}

        Returns:
            Tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0

        for date_str, day_rates in rates_data.items():
            # Parse date string
            try:
                rate_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Invalid date format: {date_str}, skipping")
                continue

            for currency, rate in day_rates.items():
                # Get or create exchange rate
                rate_obj, created = ExchangeRate.objects.get_or_create(
                    rate_date=rate_date,
                    currency=currency,
                    defaults={
                        'rate': rate,
                        'unit': 1,
                        'source': 'MNB'
                    }
                )

                if created:
                    created_count += 1
                    logger.debug(
                        f"Created rate: {currency} on {rate_date} = {rate} HUF"
                    )
                else:
                    # Update existing rate if different
                    if rate_obj.rate != rate:
                        rate_obj.rate = rate
                        rate_obj.save(update_fields=['rate', 'updated_at'])
                        updated_count += 1
                        logger.debug(
                            f"Updated rate: {currency} on {rate_date} = {rate} HUF"
                        )

        return created_count, updated_count

    @staticmethod
    def get_rate_for_date(
        target_date: date,
        currency: str,
        fallback_to_latest: bool = True
    ) -> Optional[Decimal]:
        """
        Get exchange rate for a specific date and currency from database.

        Includes smart fallback logic:
        1. Try exact date match
        2. If fallback_to_latest=True, find latest rate before target date
        3. Return None if no rate found

        Args:
            target_date: Date to get rate for
            currency: Currency code (USD or EUR)
            fallback_to_latest: If True, use latest available rate if exact date not found

        Returns:
            Exchange rate as Decimal, or None if not available
        """
        try:
            # Try exact date match first
            rate_obj = ExchangeRate.objects.get(
                rate_date=target_date,
                currency=currency
            )
            return rate_obj.rate

        except ExchangeRate.DoesNotExist:
            if fallback_to_latest:
                # Fall back to latest rate before target date
                rate_obj = ExchangeRate.objects.filter(
                    rate_date__lte=target_date,
                    currency=currency
                ).order_by('-rate_date').first()

                if rate_obj:
                    logger.info(
                        f"No exact rate for {currency} on {target_date}, "
                        f"using rate from {rate_obj.rate_date}"
                    )
                    return rate_obj.rate

            logger.warning(
                f"No exchange rate found for {currency} on {target_date}"
            )
            return None

    @staticmethod
    def convert_to_huf(
        amount: Decimal,
        currency: str,
        conversion_date: date,
        fallback_to_latest: bool = True
    ) -> Optional[Decimal]:
        """
        Convert foreign currency amount to HUF using exchange rate.

        Args:
            amount: Amount in foreign currency
            currency: Currency code (USD or EUR)
            conversion_date: Date to use for exchange rate lookup
            fallback_to_latest: If True, use latest rate if exact date not found

        Returns:
            Amount in HUF, or None if rate not available
        """
        rate = ExchangeRateSyncService.get_rate_for_date(
            conversion_date,
            currency,
            fallback_to_latest
        )

        if rate is None:
            return None

        return amount * rate

    @staticmethod
    def get_latest_rates(currencies: Optional[List[str]] = None) -> Dict[str, Tuple[Decimal, date]]:
        """
        Get the latest available exchange rates for specified currencies.

        Args:
            currencies: List of currency codes (default: USD, EUR)

        Returns:
            Dictionary mapping currency to (rate, date) tuple
            Example: {'USD': (Decimal('385.5'), date(2025, 1, 15))}
        """
        if currencies is None:
            currencies = ['USD', 'EUR']

        latest_rates = {}

        for currency in currencies:
            rate_obj = ExchangeRate.objects.filter(
                currency=currency
            ).order_by('-rate_date').first()

            if rate_obj:
                latest_rates[currency] = (rate_obj.rate, rate_obj.rate_date)

        return latest_rates

    @staticmethod
    def get_rate_history(
        currency: str,
        days: int = 30
    ) -> List[Dict[str, any]]:
        """
        Get exchange rate history for charting/analysis.

        Args:
            currency: Currency code
            days: Number of days of history to retrieve

        Returns:
            List of dictionaries with date and rate
            Example: [{'date': '2025-01-15', 'rate': 385.5}, ...]
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        rates = ExchangeRate.objects.filter(
            currency=currency,
            rate_date__gte=start_date,
            rate_date__lte=end_date
        ).order_by('rate_date')

        return [
            {
                'date': rate.rate_date.strftime('%Y-%m-%d'),
                'rate': float(rate.rate)
            }
            for rate in rates
        ]


# Convenience functions for common operations

def sync_current_rates() -> ExchangeRateSyncLog:
    """Quick helper to sync current rates"""
    service = ExchangeRateSyncService()
    return service.sync_current_rates()


def sync_historical_rates(days_back: int = 30) -> ExchangeRateSyncLog:
    """Quick helper to sync historical rates"""
    service = ExchangeRateSyncService()
    return service.sync_historical_rates(days_back)


def get_current_usd_rate() -> Optional[Decimal]:
    """Get current USD/HUF rate"""
    return ExchangeRateSyncService.get_rate_for_date(date.today(), 'USD')


def get_current_eur_rate() -> Optional[Decimal]:
    """Get current EUR/HUF rate"""
    return ExchangeRateSyncService.get_rate_for_date(date.today(), 'EUR')
