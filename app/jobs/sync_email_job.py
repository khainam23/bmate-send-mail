"""
Email synchronization job for reading and processing emails
"""
import logging
from datetime import datetime

from app.jobs.read_sync_mail.index import email_extarct as email_extractor
from app.core.config import settings

logger = logging.getLogger(__name__)

def sync_email_job():
    """Job that reads and processes emails from IMAP server"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"📧 Starting email sync job at {current_time}")
        
        # Initialize email extractor and process emails
        email_extractor.login()
        email_extractor.read_and_store()
        email_extractor.logout()
        
        message = f"Email sync job completed successfully at {current_time}"
        logger.info(f"✅ {message}")
        
        return {"status": "success", "message": message}
    except Exception as e:
        error_msg = f"Email sync job failed: {e}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return {"status": "error", "message": error_msg}

def add_sync_email_jobs(scheduler):
    """Add email sync jobs to scheduler"""
    scheduler.add_job(
        sync_email_job,
        'interval',
        minutes=settings.EMAIL_TIME_RANGE_MINUTES,
        id='sync_email_job',
        replace_existing=True
    )
    
    logger.info(f"📧 Email sync job added to scheduler (interval: {settings.EMAIL_TIME_RANGE_MINUTES} minutes)")