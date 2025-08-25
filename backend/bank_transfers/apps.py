from django.apps import AppConfig
from django.conf import settings
import os


class BankTransfersConfig(AppConfig):
    """
    Bank transfers application configuration with integrated NAV scheduler.
    Automatically starts NAV invoice synchronization in production environment.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bank_transfers'

    def ready(self):
        # Only start scheduler in production and avoid starting multiple times
        if (hasattr(settings, 'ENVIRONMENT') and 
            getattr(settings, 'ENVIRONMENT', 'local') == 'production' and
            os.environ.get('RUN_MAIN') != 'true'):  # Avoid double startup in development
            
            self.start_nav_scheduler()

    def start_nav_scheduler(self):
        """Start the NAV invoice sync scheduler"""
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            from django.core.management import call_command
            import logging
            
            logger = logging.getLogger(__name__)
            
            scheduler = BackgroundScheduler()
            
            def sync_nav_invoices():
                try:
                    logger.info("🔄 Starting NAV sync via scheduler...")
                    call_command('sync_nav_invoices', '--days=7')
                    logger.info("✅ NAV sync completed successfully")
                except Exception as e:
                    logger.error(f"❌ NAV sync failed: {str(e)}")
            
            # Schedule every 2 minutes for testing
            scheduler.add_job(
                func=sync_nav_invoices,
                trigger=CronTrigger(minute="*/2"),
                id='nav_sync_job',
                name='NAV Invoice Sync',
                replace_existing=True
            )
            
            scheduler.start()
            logger.info("📅 NAV scheduler started (every 2 minutes)")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to start NAV scheduler: {str(e)}")