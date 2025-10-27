"""
Django management command for Billingo invoice synchronization.

Usage:
    python manage.py sync_billingo_invoices                  # Sync all companies
    python manage.py sync_billingo_invoices --company-id=1    # Sync specific company
    python manage.py sync_billingo_invoices --verbose         # Verbose output
"""

from django.core.management.base import BaseCommand
from bank_transfers.models import Company
from bank_transfers.services.billingo_sync_service import (
    BillingoSyncService,
    BillingoAPIError
)


class Command(BaseCommand):
    help = 'Synchronize invoices from Billingo API for all active companies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            default=None,
            help='Sync only a specific company by ID',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Display detailed per-company results',
        )

    def handle(self, *args, **options):
        service = BillingoSyncService()
        company_id = options.get('company_id')
        verbose = options.get('verbose', False)

        try:
            # Sync single company if --company-id specified
            if company_id is not None:
                self._sync_single_company(service, company_id)

            # Otherwise sync all companies (default)
            else:
                self._sync_all_companies(service, verbose)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Fatal error: {str(e)}'))
            raise

    def _sync_single_company(self, service, company_id):
        """Sync invoices for a single company."""
        self.stdout.write(
            self.style.WARNING(f'Syncing Billingo invoices for company ID {company_id}...')
        )

        try:
            company = Company.objects.get(id=company_id, is_active=True)
        except Company.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Company with ID {company_id} not found or inactive')
            )
            return

        try:
            result = service.sync_company(company, sync_type='MANUAL')
            self._display_company_result(company.name, result, verbose=True)

        except BillingoAPIError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Billingo sync failed for {company.name}: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Unexpected error for {company.name}: {str(e)}')
            )
            raise

    def _sync_all_companies(self, service, verbose):
        """Sync invoices for all active companies."""
        self.stdout.write(
            self.style.WARNING('Syncing Billingo invoices for all active companies...')
        )

        results = service.sync_all_companies()

        # Display summary
        total = results['total_companies']
        successful = results['successful']
        failed = results['failed']

        self.stdout.write('')  # Blank line
        self.stdout.write(self.style.SUCCESS(
            f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
            f'  Billingo Sync Summary\n'
            f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
        ))
        self.stdout.write(f'  Total companies: {total}')
        self.stdout.write(self.style.SUCCESS(f'  ✅ Successful: {successful}'))

        if failed > 0:
            self.stdout.write(self.style.ERROR(f'  ❌ Failed: {failed}'))
        else:
            self.stdout.write(f'  ❌ Failed: {failed}')

        # Display per-company results if verbose
        if verbose and results['companies']:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Per-Company Results:'))
            self.stdout.write('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

            for company_result in results['companies']:
                company_name = company_result['company_name']
                status = company_result['status']

                if status == 'success':
                    invoices_processed = company_result.get('invoices_processed', 0)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ {company_name}: {invoices_processed} invoices processed'
                        )
                    )
                else:
                    error = company_result.get('error', 'Unknown error')
                    self.stdout.write(
                        self.style.ERROR(f'❌ {company_name}: {error}')
                    )

        self.stdout.write('')  # Blank line

    def _display_company_result(self, company_name, result, verbose=False):
        """Display detailed results for a company sync."""
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'✅ Billingo sync completed for {company_name}\n'
            f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
        ))
        self.stdout.write(f'  Invoices processed: {result["invoices_processed"]}')
        self.stdout.write(f'  Created: {result["invoices_created"]}')
        self.stdout.write(f'  Updated: {result["invoices_updated"]}')

        if result['invoices_skipped'] > 0:
            self.stdout.write(
                self.style.WARNING(f'  Skipped (errors): {result["invoices_skipped"]}')
            )

        self.stdout.write(f'  Items extracted: {result["items_extracted"]}')
        self.stdout.write(f'  API calls made: {result["api_calls"]}')
        self.stdout.write(f'  Duration: {result["duration_seconds"]} seconds')

        # Display errors if any
        if verbose and result.get('errors'):
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Errors encountered:'))
            for error in result['errors']:
                invoice_num = error.get('invoice_number', 'Unknown')
                error_msg = error.get('error', 'Unknown error')
                self.stdout.write(f'  • Invoice {invoice_num}: {error_msg}')

        self.stdout.write('')
