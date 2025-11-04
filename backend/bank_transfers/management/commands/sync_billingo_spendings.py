"""
Django management command to sync Billingo spendings from API.

Usage:
    python manage.py sync_billingo_spendings
    python manage.py sync_billingo_spendings --company-id=1
"""

import requests
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Optional
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from bank_transfers.models import (
    Company,
    CompanyBillingoSettings,
    BillingoSpending
)
from bank_transfers.services.credential_manager import CredentialManager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync Billingo spendings from API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='Sync only for specific company ID'
        )
        parser.add_argument(
            '--full-sync',
            action='store_true',
            help='Full sync (ignore last sync date)'
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')
        full_sync = options.get('full_sync', False)

        if company_id:
            try:
                company = Company.objects.get(id=company_id, is_active=True)
                self.stdout.write(f"Syncing spendings for company: {company.name}")
                result = self.sync_company_spendings(company, full_sync)
                self.print_results(result)
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Company with ID {company_id} not found or inactive"))
        else:
            self.stdout.write("Syncing spendings for all active companies")
            companies = Company.objects.filter(
                is_active=True,
                billingo_settings__is_active=True
            ).prefetch_related('billingo_settings')

            total_created = 0
            total_updated = 0

            for company in companies:
                self.stdout.write(f"\n{'='*60}")
                self.stdout.write(f"Company: {company.name}")
                result = self.sync_company_spendings(company, full_sync)
                self.print_results(result)
                total_created += result['created']
                total_updated += result['updated']

            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(self.style.SUCCESS(
                f"\nTotal: {total_created} created, {total_updated} updated"
            ))

    def sync_company_spendings(self, company: Company, full_sync: bool = False) -> Dict:
        """Sync spendings for a single company."""
        try:
            settings = company.billingo_settings.first()
            if not settings or not settings.is_active:
                return {
                    'created': 0,
                    'updated': 0,
                    'skipped': 0,
                    'error': 'No active Billingo settings'
                }

            # Get decrypted API key
            if not settings.api_key:
                return {
                    'created': 0,
                    'updated': 0,
                    'skipped': 0,
                    'error': 'No API key configured'
                }

            credential_manager = CredentialManager()
            api_key = credential_manager.decrypt_credential(settings.api_key)

            # Delete existing spendings for full sync
            if full_sync:
                deleted_count = BillingoSpending.objects.filter(company=company).count()
                BillingoSpending.objects.filter(company=company).delete()
                self.stdout.write(self.style.WARNING(
                    f"Full sync: Deleted {deleted_count} existing spendings for {company.name}"
                ))

            # Determine start date for partial sync
            start_date = None
            if not full_sync:
                from datetime import timedelta
                # Use last sync date minus 30 days for overlap window
                if settings.last_billingo_spending_sync_date:
                    start_date = settings.last_billingo_spending_sync_date - timedelta(days=30)
                else:
                    # First sync: get last 30 days
                    start_date = date.today() - timedelta(days=30)

            # Fetch spendings from Billingo API
            spendings = self.fetch_spendings_from_api(api_key, start_date=start_date)

            if not spendings:
                return {
                    'created': 0,
                    'updated': 0,
                    'skipped': 0,
                    'error': None
                }

            # Store spendings in database
            created = 0
            updated = 0
            skipped = 0

            for spending_data in spendings:
                try:
                    spending_id = spending_data.get('id')

                    # Check if spending already exists
                    existing = BillingoSpending.objects.filter(
                        id=spending_id,
                        company=company
                    ).first()

                    spending_obj = self.create_or_update_spending(
                        spending_data,
                        company,
                        existing
                    )

                    if existing:
                        updated += 1
                    else:
                        created += 1

                except Exception as e:
                    logger.error(f"Error processing spending {spending_data.get('id')}: {e}")
                    skipped += 1

            # Update last sync date
            settings.last_billingo_spending_sync_date = date.today()
            settings.save(update_fields=['last_billingo_spending_sync_date'])

            return {
                'created': created,
                'updated': updated,
                'skipped': skipped,
                'error': None
            }

        except Exception as e:
            logger.error(f"Error syncing spendings for company {company.name}: {e}", exc_info=True)
            return {
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'error': str(e)
            }

    def fetch_spendings_from_api(self, api_key: str, start_date: Optional[date] = None) -> list:
        """Fetch spendings from Billingo API with pagination.

        Args:
            api_key: Billingo API key
            start_date: Optional start date for filtering (partial sync)
                       If None, fetches all spendings (full sync)
        """
        base_url = "https://api.billingo.hu/v3"
        headers = {
            "X-API-KEY": api_key,
            "Accept": "application/json"
        }

        all_spendings = []
        page = 1
        per_page = 100  # Max allowed by Billingo API

        while True:
            try:
                # Build query parameters
                params = {
                    'page': page,
                    'per_page': per_page
                }

                # Add start_date filter for partial sync
                if start_date:
                    params['start_date'] = start_date.strftime('%Y-%m-%d')
                    self.stdout.write(f"Fetching spendings from {start_date} onwards (partial sync)")
                else:
                    self.stdout.write("Fetching ALL spendings (full sync)")

                # Log the outgoing request
                url = f"{base_url}/spendings"
                logger.info(f"Billingo API Request: GET {url}")
                logger.info(f"Billingo API Params: {params}")
                logger.debug(f"Billingo API Headers: {dict(headers) | {'X-API-KEY': '***REDACTED***'}}")

                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=30
                )

                # Log the response
                logger.info(f"Billingo API Response: Status {response.status_code}, Page {page}")

                if response.status_code == 404:
                    # Endpoint might not exist or no data
                    self.stdout.write(self.style.WARNING(
                        "Spendings endpoint returned 404 (might not be available or no data)"
                    ))
                    break

                response.raise_for_status()
                data = response.json()

                # Handle pagination
                if isinstance(data, dict) and 'data' in data:
                    spendings = data['data']
                    all_spendings.extend(spendings)

                    # Check if there are more pages
                    if len(spendings) < per_page:
                        break
                    page += 1
                elif isinstance(data, list):
                    all_spendings.extend(data)
                    break
                else:
                    break

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    self.stdout.write(self.style.WARNING(
                        "Spendings endpoint not found (might not be available for this account)"
                    ))
                else:
                    logger.error(f"HTTP error fetching spendings: {e}")
                break
            except Exception as e:
                logger.error(f"Error fetching spendings from API: {e}")
                break

        self.stdout.write(f"Fetched {len(all_spendings)} spendings from Billingo API")
        return all_spendings

    @transaction.atomic
    def create_or_update_spending(
        self,
        data: Dict,
        company: Company,
        existing: Optional[BillingoSpending] = None
    ) -> BillingoSpending:
        """Create or update a BillingoSpending record."""

        # Parse dates
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                return None

        spending_data = {
            'id': data['id'],
            'company': company,
            'organization_id': data.get('organization_id', 0),
            'category': data.get('category', 'other'),
            'paid_at': parse_date(data.get('paid_at')),
            'fulfillment_date': parse_date(data.get('fulfillment_date')) or date.today(),
            'invoice_number': data.get('invoice_number', ''),
            'currency': data.get('currency', 'HUF'),
            'conversion_rate': Decimal(str(data.get('conversion_rate', 1.0))),
            'total_gross': Decimal(str(data.get('total_gross', 0))),
            'total_gross_local': Decimal(str(data.get('total_gross_local', 0))),
            'total_vat_amount': Decimal(str(data.get('total_vat_amount', 0))),
            'total_vat_amount_local': Decimal(str(data.get('total_vat_amount_local', 0))),
            'invoice_date': parse_date(data.get('invoice_date')) or date.today(),
            'due_date': parse_date(data.get('due_date')) or date.today(),
            'payment_method': data.get('payment_method', 'unknown'),
            'partner_id': data.get('partner', {}).get('id') if isinstance(data.get('partner'), dict) else None,
            'partner_name': data.get('partner', {}).get('name', 'Unknown') if isinstance(data.get('partner'), dict) else str(data.get('partner_name', 'Unknown')),
            'partner_tax_code': data.get('partner', {}).get('tax_code', '') if isinstance(data.get('partner'), dict) else data.get('partner_tax_code', ''),
            'partner_address': data.get('partner', {}).get('address') if isinstance(data.get('partner'), dict) else None,
            'partner_iban': data.get('partner_iban'),
            'partner_account_number': data.get('partner_account_number'),
            'comment': data.get('comment', ''),
            'is_created_by_nav': data.get('is_created_by_nav', False),
        }

        if existing:
            for key, value in spending_data.items():
                if key not in ['id', 'company']:  # Don't update PK or company FK
                    setattr(existing, key, value)
            existing.save()
            return existing
        else:
            return BillingoSpending.objects.create(**spending_data)

    def print_results(self, result: Dict):
        """Print sync results."""
        if result.get('error'):
            self.stdout.write(self.style.ERROR(f"  Error: {result['error']}"))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"  Created: {result['created']}, "
                f"Updated: {result['updated']}, "
                f"Skipped: {result['skipped']}"
            ))
