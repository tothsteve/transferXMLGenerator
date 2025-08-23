"""
Django management command for NAV invoice synchronization.

This command provides READ-ONLY synchronization of invoice data from NAV.
It can be run manually or scheduled via cron for automated invoice sync.

Usage:
    python manage.py sync_nav_invoices                    # Sync all companies, last 30 days
    python manage.py sync_nav_invoices --company "Company Name"  # Specific company
    python manage.py sync_nav_invoices --days 7           # Last 7 days
    python manage.py sync_nav_invoices --date-from 2025-01-01 --date-to 2025-01-31
    python manage.py sync_nav_invoices --direction INBOUND  # Only inbound invoices
    python manage.py sync_nav_invoices --test             # Test mode (dry run)

CRITICAL: This command only QUERIES data from NAV. It never modifies NAV data.
"""

import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from bank_transfers.models import Company
from bank_transfers.services.invoice_sync_service import InvoiceSyncService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management command for READ-ONLY NAV invoice synchronization.
    
    This command orchestrates the invoice synchronization process for one or more
    companies. It provides comprehensive logging and error handling suitable for
    both manual execution and automated scheduling.
    """
    
    help = 'Synchronize invoices from NAV system (READ-ONLY operation)'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        
        parser.add_argument(
            '--company',
            type=str,
            help='Specific company name to sync (default: all companies)'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to sync from today backwards (default: 30)'
        )
        
        parser.add_argument(
            '--date-from',
            type=str,
            help='Start date for sync (YYYY-MM-DD format)'
        )
        
        parser.add_argument(
            '--date-to',
            type=str,
            help='End date for sync (YYYY-MM-DD format)'
        )
        
        parser.add_argument(
            '--direction',
            type=str,
            choices=['OUTBOUND', 'INBOUND', 'BOTH'],
            default='BOTH',
            help='Invoice direction to sync (default: BOTH)'
        )
        
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test mode - validate configurations but do not sync'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output with detailed logging'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync even if recent sync exists'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        
        # Configure logging level
        if options['verbose']:
            logging.getLogger('bank_transfers').setLevel(logging.DEBUG)
            self.stdout.write('Részletes naplózás bekapcsolva')
        
        # Parse date range
        date_from, date_to = self._parse_date_range(options)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'NAV számla szinkronizáció indítása: {date_from.date()} - {date_to.date()}'
            )
        )
        
        # Initialize sync service
        sync_service = InvoiceSyncService()
        
        if options['test']:
            # Test mode - validate configurations
            self._run_test_mode(sync_service, options)
        else:
            # Production sync
            self._run_sync(sync_service, options, date_from, date_to)
    
    def _parse_date_range(self, options):
        """Parse and validate date range from options."""
        
        if options['date_from'] and options['date_to']:
            # Explicit date range provided
            try:
                date_from = datetime.strptime(options['date_from'], '%Y-%m-%d')
                date_to = datetime.strptime(options['date_to'], '%Y-%m-%d')
                date_from = timezone.make_aware(date_from)
                date_to = timezone.make_aware(date_to)
            except ValueError:
                raise CommandError('Hibás dátum formátum. Használj YYYY-MM-DD formátumot.')
        else:
            # Use days parameter
            days = options['days']
            date_to = timezone.now()
            date_from = date_to - timedelta(days=days)
        
        if date_from >= date_to:
            raise CommandError('A kezdő dátum nem lehet későbbi a végdátumnál.')
        
        return date_from, date_to
    
    def _run_test_mode(self, sync_service, options):
        """Run in test mode - validate configurations without syncing."""
        
        self.stdout.write(self.style.WARNING('TESZT MÓD - Nincs tényleges szinkronizáció'))
        
        # Get companies to test
        companies = self._get_companies_to_process(options['company'])
        
        if not companies:
            self.stdout.write(self.style.ERROR('Nincs feldolgozandó cég'))
            return
        
        success_count = 0
        
        for company in companies:
            self.stdout.write(f'\nNAV konfiguráció tesztelése: {company.name}')
            
            # Get NAV configuration
            nav_config = sync_service._get_nav_configuration(company)
            if not nav_config:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Nincs aktív NAV konfiguráció: {company.name}')
                )
                continue
            
            self.stdout.write(f'  ✅ NAV konfiguráció található')
            self.stdout.write(f'  📋 Adószám: {nav_config.tax_number}')
            self.stdout.write(f'  🌐 Környezet: {nav_config.api_environment}')
            self.stdout.write(f'  👤 Technikai felhasználó: {nav_config.technical_user_login[:5]}...')
            
            try:
                # Test NAV connection
                nav_client = sync_service._initialize_nav_client(nav_config)
                if nav_client.test_connection():
                    self.stdout.write(self.style.SUCCESS(f'  ✅ NAV kapcsolat sikeres'))
                    success_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f'  ❌ NAV kapcsolat sikertelen'))
            except Exception as e:
                error_msg = str(e) if str(e) else f"{type(e).__name__}"
                self.stdout.write(
                    self.style.ERROR(f'  ❌ NAV kliens hiba: {error_msg}')
                )
                if options['verbose']:
                    import traceback
                    self.stdout.write(traceback.format_exc())
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTeszt befejezve: {success_count}/{len(companies)} cég sikeres')
        )
    
    def _run_sync(self, sync_service, options, date_from, date_to):
        """Run actual invoice synchronization."""
        
        company_name = options['company']
        direction = options['direction']
        
        if company_name:
            # Sync specific company
            companies = self._get_companies_to_process(company_name)
            if not companies:
                raise CommandError(f'Cég nem található: {company_name}')
            
            for company in companies:
                self._sync_company(sync_service, company, date_from, date_to, direction)
        else:
            # Sync all companies
            self.stdout.write('Összes cég szinkronizációja...')
            results = sync_service.sync_all_companies(date_from, date_to)
            self._display_sync_results(results)
    
    def _sync_company(self, sync_service, company, date_from, date_to, direction):
        """Sync invoices for a specific company."""
        
        self.stdout.write(f'\nCég szinkronizáció: {company.name}')
        
        if direction == 'BOTH':
            directions = ['OUTBOUND', 'INBOUND']
        else:
            directions = [direction]
        
        total_created = 0
        total_updated = 0
        
        for sync_direction in directions:
            self.stdout.write(f'  Irány: {sync_direction}')
            
            result = sync_service.sync_company_invoices(
                company=company,
                date_from=date_from,
                date_to=date_to,
                direction=sync_direction
            )
            
            if result['success']:
                created = result['invoices_created']
                updated = result['invoices_updated']
                processed = result['invoices_processed']
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'    ✅ Feldolgozva: {processed}, Új: {created}, Frissítve: {updated}'
                    )
                )
                
                total_created += created
                total_updated += updated
            else:
                errors = result.get('errors', ['Ismeretlen hiba'])
                self.stdout.write(
                    self.style.ERROR(f'    ❌ Hiba: {"; ".join(errors)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Cég szinkronizáció befejezve: {company.name} - '
                f'Új: {total_created}, Frissítve: {total_updated}'
            )
        )
    
    def _get_companies_to_process(self, company_name=None):
        """Get list of companies to process."""
        
        if company_name:
            companies = Company.objects.filter(name__icontains=company_name)
            if not companies.exists():
                return Company.objects.none()
        else:
            # Get all companies with active NAV configurations
            companies = Company.objects.filter(
                nav_configs__is_active=True,
                nav_configs__sync_enabled=True
            ).distinct()
        
        return companies
    
    def _display_sync_results(self, results):
        """Display comprehensive sync results."""
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('NAV SZINKRONIZÁCIÓ ÖSSZESÍTŐ'))
        self.stdout.write('='*50)
        
        # Summary statistics
        self.stdout.write(f'Feldolgozott cégek: {results["companies_processed"]}')
        self.stdout.write(f'Sikeres cégek: {results["companies_succeeded"]}')
        self.stdout.write(f'Hibás cégek: {results["companies_failed"]}')
        self.stdout.write(f'Összes új számla: {results["total_invoices_created"]}')
        self.stdout.write(f'Összes frissített számla: {results["total_invoices_updated"]}')
        
        # Detailed company results
        if results["company_results"]:
            self.stdout.write('\nCég részletek:')
            self.stdout.write('-'*30)
            
            for company_result in results["company_results"]:
                company_name = company_result["company_name"]
                direction = company_result.get("direction", "N/A")
                success = company_result["success"]
                
                if success:
                    created = company_result.get("invoices_created", 0)
                    updated = company_result.get("invoices_updated", 0)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ {company_name} ({direction}): +{created} új, ~{updated} frissítve'
                        )
                    )
                else:
                    errors = company_result.get("errors", ["Ismeretlen hiba"])
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ {company_name} ({direction}): {"; ".join(errors[:2])}'
                        )
                    )
        
        # Success/failure summary
        if results["companies_failed"] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  {results["companies_failed"]} cég szinkronizációja sikertelen volt'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Minden cég sikeresen szinkronizálva!')
            )
        
        self.stdout.write('='*50)