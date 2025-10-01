"""
Django management command for MNB exchange rate synchronization.

Usage:
    python manage.py sync_mnb_rates --current       # Sync current day rates
    python manage.py sync_mnb_rates --days=30       # Sync 30 days historical
"""

from django.core.management.base import BaseCommand
from bank_transfers.services.exchange_rate_sync_service import ExchangeRateSyncService


class Command(BaseCommand):
    help = 'Synchronize MNB (Magyar Nemzeti Bank) exchange rates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--current',
            action='store_true',
            help='Sync only current day rates (default)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help='Number of days for historical sync (e.g., --days=30)',
        )
        parser.add_argument(
            '--currencies',
            type=str,
            default='USD,EUR',
            help='Comma-separated currency codes (default: USD,EUR)',
        )

    def handle(self, *args, **options):
        service = ExchangeRateSyncService()
        currencies = options['currencies'].split(',')

        try:
            # Historical sync if --days specified
            if options['days'] is not None:
                days = options['days']
                self.stdout.write(
                    self.style.WARNING(f'Syncing {days} days of historical rates for {", ".join(currencies)}...')
                )
                log = service.sync_historical_rates(days_back=days, currencies=currencies)

            # Otherwise sync current rates (default)
            else:
                self.stdout.write(
                    self.style.WARNING(f'Syncing current rates for {", ".join(currencies)}...')
                )
                log = service.sync_current_rates(currencies=currencies)

            # Display results
            if log.sync_status == 'SUCCESS':
                self.stdout.write(self.style.SUCCESS(
                    f'✅ MNB sync completed successfully\n'
                    f'   Created: {log.rates_created} rates\n'
                    f'   Updated: {log.rates_updated} rates\n'
                    f'   Duration: {log.duration_seconds:.2f} seconds'
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f'❌ MNB sync failed: {log.error_message}'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            raise
