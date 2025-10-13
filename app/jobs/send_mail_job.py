"""
Send mail job - Gửi email data lên CRM
"""
import logging
from datetime import datetime

from app.jobs.read_sync_mail.index import email_extarct as email_extractor
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_mail():
    """Gửi email data lên CRM"""
    try:
        logger.info(f"📤 Starting send_mail job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        email_extractor.call_api()
        logger.info(f"✅ Send_mail job completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        logger.error(f"❌ Error in send_mail job: {e}", exc_info=True)

def add_send_mail_jobs(scheduler):
    """Add send mail jobs to scheduler"""
    scheduler.add_job(
        send_mail,
        'interval',
        minutes=settings.EMAIL_TIME_SEND,
        id='send_mail_to_crm',
        replace_existing=True
    )
    
    logger.info(f"📤 Send mail job added to scheduler (interval: {settings.EMAIL_TIME_SEND} minutes)")
