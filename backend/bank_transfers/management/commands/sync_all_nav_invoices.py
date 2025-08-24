#!/usr/bin/env python3
"""
Django management command to sync all NAV invoices from 2020-01-01 to today, month by month.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from datetime import datetime, date, timedelta
import calendar
import logging
import traceback
import os

from bank_transfers.services.invoice_sync_service import InvoiceSyncService
from bank_transfers.models import Company


class Command(BaseCommand):
    help = 'Sync all NAV invoices from 2020-01-01 to today, processing month by month'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            default='2020-01-01',
            help='Start date in YYYY-MM-DD format (default: 2020-01-01)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            default=None,
            help='End date in YYYY-MM-DD format (default: today)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually syncing'
        )
        parser.add_argument(
            '--continue-on-error',
            action='store_true',
            help='Continue processing other months if one month fails'
        )
        parser.add_argument(
            '--log-level',
            type=str,
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            default='INFO',
            help='Logging level (default: INFO)'
        )
        parser.add_argument(
            '--no-file-log',
            action='store_true',
            help='Disable file logging (production safe)'
        )
        parser.add_argument(
            '--environment',
            type=str,
            choices=['production', 'test'],
            help='Force specific NAV environment (production or test)'
        )
        parser.add_argument(
            '--prefer-test',
            action='store_true',
            help='Prefer test environment over production when auto-selecting'
        )

    def handle(self, *args, **options):
        self.setup_logging(options)
        
        # Parse dates
        start_date = self.parse_date(options['start_date'])
        end_date = self.parse_date(options['end_date']) if options['end_date'] else date.today()
        
        if start_date > end_date:
            raise CommandError("Start date cannot be after end date")
        
        # Production-safe output (less emojis in production)
        is_production = getattr(settings, 'DEBUG', True) is False
        
        if is_production:
            self.stdout.write(f"NAV Invoice Sync: {start_date} to {end_date}")
        else:
            self.stdout.write(
                self.style.SUCCESS(f"🎯 NAV Invoice Sync: {start_date} to {end_date}")
            )
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No actual syncing"))
        
        # Initialize sync service and get company
        try:
            sync_service = InvoiceSyncService()
            company = Company.objects.first()  # Use first company (can be made configurable)
            if not company:
                raise CommandError("No companies found. Please create a company first.")
        except Exception as e:
            raise CommandError(f"Failed to initialize NAV sync service: {e}")
        
        # Generate month ranges
        month_ranges = self.generate_month_ranges(start_date, end_date)
        
        self.stdout.write(f"Processing {len(month_ranges)} months")
        
        total_success = 0
        total_errors = 0
        
        for i, (month_start, month_end) in enumerate(month_ranges, 1):
            if is_production:
                self.stdout.write(f"[{i}/{len(month_ranges)}] Processing {month_start.strftime('%Y-%m')}")
            else:
                self.stdout.write(f"\n🗓️  [{i}/{len(month_ranges)}] Processing {month_start.strftime('%Y-%m')}")
            
            try:
                if not options['dry_run']:
                    # Sync INBOUND invoices for this month with environment selection
                    result = sync_service.sync_company_invoices(
                        company=company,
                        date_from=month_start,
                        date_to=month_end,
                        direction='INBOUND',
                        environment=options['environment'],
                        prefer_production=not options['prefer_test']
                    )
                    
                    success_count = result.get('success_count', 0)
                    error_count = result.get('error_count', 0)
                    
                    total_success += success_count
                    total_errors += error_count
                    
                    if is_production:
                        self.stdout.write(f"  Success: {success_count}, Errors: {error_count}")
                    else:
                        self.stdout.write(f"   ✅ Success: {success_count}, ❌ Errors: {error_count}")
                    
                    # Show errors (limit in production)
                    if result.get('errors'):
                        error_limit = 1 if is_production else 3
                        for error in result['errors'][:error_limit]:
                            if is_production:
                                self.stdout.write(f"  WARNING: {error}")
                            else:
                                self.stdout.write(self.style.WARNING(f"   ⚠️  {error}"))
                else:
                    self.stdout.write(f"  [DRY RUN] Would sync {month_start} to {month_end}")
                    
            except Exception as e:
                error_msg = f"Failed to sync month {month_start.strftime('%Y-%m')}: {str(e)}"
                self.stdout.write(self.style.ERROR(f"  ERROR: {error_msg}"))
                logging.error(f"{error_msg}\n{traceback.format_exc()}")
                
                total_errors += 1
                
                if not options['continue_on_error']:
                    raise CommandError(f"Stopping due to error: {error_msg}")
        
        # Final summary
        self.stdout.write("\n" + "="*50)
        if is_production:
            self.stdout.write("SYNC COMPLETE")
        else:
            self.stdout.write(self.style.SUCCESS("🎉 SYNC COMPLETE"))
        
        self.stdout.write(f"Total Success: {total_success}")
        self.stdout.write(f"Total Errors: {total_errors}")
        
        if total_errors == 0:
            if is_production:
                self.stdout.write("All months processed successfully")
            else:
                self.stdout.write(self.style.SUCCESS("✨ All months processed successfully!"))
        else:
            self.stdout.write(f"WARNING: {total_errors} months had errors - check logs")

    def parse_date(self, date_str):
        """Parse date string to date object."""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise CommandError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

    def generate_month_ranges(self, start_date, end_date):
        """Generate list of (month_start, month_end) tuples."""
        ranges = []
        current = start_date.replace(day=1)  # Start of month
        
        while current <= end_date:
            # Calculate month end using calendar
            _, last_day = calendar.monthrange(current.year, current.month)
            month_end = current.replace(day=last_day)
            
            # Don't go beyond end_date
            if month_end > end_date:
                month_end = end_date
            
            ranges.append((current, month_end))
            
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
            
            # Stop if we've reached the end
            if current > end_date:
                break
        
        return ranges

    def setup_logging(self, options):
        """Setup production-safe logging for the command."""
        log_level = getattr(logging, options['log_level'])
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        handlers = [logging.StreamHandler()]
        
        # Add file logging if not disabled (and not in production by default)
        if not options['no_file_log']:
            is_production = getattr(settings, 'DEBUG', True) is False
            if not is_production:  # Only log to file in development by default
                log_filename = f"nav_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                handlers.append(logging.FileHandler(log_filename))
                print(f"Logging to file: {log_filename}")
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=handlers,
            force=True  # Reset existing loggers
        )