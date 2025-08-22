from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from bank_transfers.models import Company, NavConfiguration
from bank_transfers.services.nav_client import NavApiClient


class Command(BaseCommand):
    help = 'Test NAV API client connectivity and authentication'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='Test NAV connection for specific company ID',
        )
        parser.add_argument(
            '--list-companies',
            action='store_true',
            help='List all companies with NAV configuration',
        )
    
    def handle(self, *args, **options):
        """Handle the test command execution."""
        
        if options['list_companies']:
            self.list_companies_with_nav_config()
            return
        
        company_id = options['company_id']
        if not company_id:
            self.stdout.write(
                self.style.ERROR('Please provide --company-id or use --list-companies')
            )
            return
        
        try:
            # Get company and NAV configuration
            company = Company.objects.get(id=company_id)
            self.stdout.write(f"Testing NAV connection for: {company.name}")
            
            try:
                nav_config = company.nav_config
            except NavConfiguration.DoesNotExist:
                raise CommandError(f"No NAV configuration found for company {company.name}")
            
            if not nav_config.is_active:
                raise CommandError(f"NAV configuration is inactive for company {company.name}")
            
            # Test NAV API connection
            self.stdout.write("Initializing NAV API client...")
            nav_client = NavApiClient(nav_config)
            
            self.stdout.write("Testing NAV API connection...")
            result = nav_client.test_connection()
            
            # Display results
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {result['message']}")
                )
                self.stdout.write(f"🌐 Environment: {result['api_environment']}")
                self.stdout.write(f"🔗 Base URL: {result['base_url']}")
                self.stdout.write(f"🎫 Token received: {result['token_received']}")
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ {result['message']}")
                )
                self.stdout.write(f"🌐 Environment: {result['api_environment']}")
                self.stdout.write(f"🔗 Base URL: {result['base_url']}")
            
        except Company.DoesNotExist:
            raise CommandError(f"Company with ID {company_id} does not exist")
        except Exception as e:
            raise CommandError(f"Test failed: {str(e)}")
    
    def list_companies_with_nav_config(self):
        """List all companies that have NAV configuration."""
        self.stdout.write("Companies with NAV configuration:")
        self.stdout.write("-" * 50)
        
        companies_with_nav = Company.objects.filter(nav_config__isnull=False)
        
        if not companies_with_nav.exists():
            self.stdout.write(
                self.style.WARNING("No companies have NAV configuration set up.")
            )
            self.stdout.write(
                "Create a NavConfiguration through Django admin first."
            )
            return
        
        for company in companies_with_nav:
            nav_config = company.nav_config
            status_icon = "✅" if nav_config.is_active else "❌"
            sync_icon = "🔄" if nav_config.sync_enabled else "⏸️"
            env_icon = "🔴" if nav_config.api_environment == 'production' else "🟡"
            
            self.stdout.write(
                f"{status_icon} ID: {company.id:2d} | "
                f"{company.name:25s} | "
                f"{env_icon} {nav_config.api_environment:10s} | "
                f"{sync_icon} Sync: {'ON' if nav_config.sync_enabled else 'OFF':3s}"
            )
        
        self.stdout.write("-" * 50)
        self.stdout.write(
            "Usage: python manage.py test_nav_client --company-id <ID>"
        )