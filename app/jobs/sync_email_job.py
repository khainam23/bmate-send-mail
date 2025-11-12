"""
Email synchronization job for reading and processing emails
"""
import logging
from datetime import datetime

from app.jobs.read_sync_mail.index import EmailExtract
from app.core.config import settings

logger = logging.getLogger(__name__)

def sync_email_job(imap_server, email_account, email_password):
    """Job that reads and processes emails from IMAP server"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"📧 Starting email sync job at {current_time}")
        
        email_extractor = EmailExtract(
            imap_server=imap_server,
            email_account=email_account,
            email_password=email_password,
            mail=None,
            processed_emails=set(),
            queue_refresh_time=None
        )
        
        # Initialize email extractor and process emails
        email_extractor.login()
        email_extractor.create_label_if_not_exists()
        email_extractor.read_and_store()
        email_extractor.logout()
        
        message = f"Email sync job completed successfully at {current_time}"
        logger.info(f"✅ {message}")
        
        return {"status": "success", "message": message}
    except Exception as e:
        error_msg = f"Email sync job failed: {e}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return {"status": "error", "message": error_msg}

def add_sync_email_1_jobs(scheduler):
    """Add email sync jobs to scheduler"""
    scheduler.add_job(
        sync_email_job,
        'interval',
        minutes=settings.EMAIL_TIME_RANGE_MINUTES,
        id='sync_email_1_job',
        replace_existing=True,
        kwargs={
            "imap_server": settings.HOST_IMAP_1,
            "email_account": settings.EMAIL_ADDRESS_1,
            "email_password": settings.EMAIL_PASSWORD_APP_1
        }
    )
    
    logger.info(f"📧 Email 1 sync job added to scheduler (interval: {settings.EMAIL_TIME_RANGE_MINUTES} minutes)")
    
def add_sync_email_2_jobs(scheduler):
    """Add email sync jobs to scheduler"""
    scheduler.add_job(
        sync_email_job,
        'interval',
        minutes=settings.EMAIL_TIME_RANGE_MINUTES,
        id='sync_email_2_job',
        replace_existing=True,
        kwargs={
            "imap_server": settings.HOST_IMAP_2,
            "email_account": settings.EMAIL_ADDRESS_2,
            "email_password": settings.EMAIL_PASSWORD_APP_2
        }
    )
    
    logger.info(f"📧 Email sync job added to scheduler (interval: {settings.EMAIL_TIME_RANGE_MINUTES} minutes)")