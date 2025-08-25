"""
Django APScheduler management command for NAV invoice sync.

This command starts a background scheduler that automatically runs
NAV invoice synchronization at configured intervals.

Usage:
    python manage.py run_scheduler

The scheduler will run continuously and execute NAV sync every 2 minutes.
Use Ctrl+C to stop the scheduler.
"""

import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run APScheduler for automated NAV invoice synchronization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=2,
            help='Sync interval in minutes (default: 2)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days back to sync (default: 7)'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        days = options['days']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting NAV sync scheduler (every {interval} minutes, {days} days back)')
        )

        # Configure scheduler
        executors = {
            'default': ThreadPoolExecutor(20),
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }
        
        scheduler = BlockingScheduler(executors=executors, job_defaults=job_defaults)

        # Add NAV sync job
        scheduler.add_job(
            func=self.sync_nav_invoices,
            trigger=CronTrigger(minute=f'*/{interval}'),
            id='nav_sync_job',
            name='NAV Invoice Sync',
            replace_existing=True,
            kwargs={'days': days}
        )

        try:
            self.stdout.write('Scheduler started. Press Ctrl+C to exit.')
            scheduler.start()
        except KeyboardInterrupt:
            self.stdout.write('Scheduler stopped.')
            scheduler.shutdown()

    def sync_nav_invoices(self, days=7):
        """Execute NAV invoice sync"""
        try:
            self.stdout.write(f'🔄 Starting NAV sync (last {days} days)...')
            call_command('sync_nav_invoices', f'--days={days}')
            self.stdout.write('✅ NAV sync completed successfully')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ NAV sync failed: {str(e)}')
            )
            logger.error(f'NAV sync error: {str(e)}')