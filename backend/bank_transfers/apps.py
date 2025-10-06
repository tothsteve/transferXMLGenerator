from django.apps import AppConfig
from django.conf import settings
import os


class BankTransfersConfig(AppConfig):
    """
    Bank transfers application configuration with integrated schedulers.
    Automatically starts NAV invoice and MNB exchange rate synchronization in production.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bank_transfers'

    def ready(self):
        # Only start schedulers on Railway (production) and avoid starting multiple times
        railway_env = os.environ.get('RAILWAY_ENVIRONMENT_NAME')
        if (railway_env == 'production' and
            os.environ.get('RUN_MAIN') != 'true'):  # Avoid double startup in development

            self.start_nav_scheduler()
            self.start_mnb_scheduler()

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
                from django.db import close_old_connections
                try:
                    # Close any stale database connections before starting
                    close_old_connections()

                    logger.info("🔄 Starting NAV sync via scheduler...")
                    call_command('sync_nav_invoices', '--days=7')
                    logger.info("✅ NAV sync completed successfully")
                except Exception as e:
                    logger.error(f"❌ NAV sync failed: {str(e)}")
                finally:
                    # Always close connections after job completes
                    close_old_connections()
            
            # Schedule every 6 hours for production
            scheduler.add_job(
                func=sync_nav_invoices,
                trigger=CronTrigger(hour="*/6"),
                id='nav_sync_job',
                name='NAV Invoice Sync',
                replace_existing=True
            )
            
            scheduler.start()
            logger.info("📅 NAV scheduler started (every 6 hours)")

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to start NAV scheduler: {str(e)}")

    def start_mnb_scheduler(self):
        """Start the MNB exchange rate sync scheduler"""
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            from django.core.management import call_command
            import logging

            logger = logging.getLogger(__name__)

            scheduler = BackgroundScheduler()

            def sync_mnb_rates():
                from django.db import close_old_connections
                try:
                    # Close any stale database connections before starting
                    close_old_connections()

                    logger.info("💱 Starting MNB exchange rate sync...")
                    call_command('sync_mnb_rates', '--current')
                    logger.info("✅ MNB sync completed successfully")
                except Exception as e:
                    logger.error(f"❌ MNB sync failed: {str(e)}")
                finally:
                    # Always close connections after job completes
                    close_old_connections()

            # Schedule every 6 hours (same as NAV)
            scheduler.add_job(
                func=sync_mnb_rates,
                trigger=CronTrigger(hour="*/6"),
                id='mnb_sync_job',
                name='MNB Exchange Rate Sync',
                replace_existing=True
            )

            scheduler.start()
            logger.info("💱 MNB scheduler started (every 6 hours)")

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to start MNB scheduler: {str(e)}")