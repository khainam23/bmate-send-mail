"""
Simple print job for testing scheduler
"""
import logging

from app.jobs.read_sync_mail.index import email_extarct as email_extractor
from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_mail():
    email_extractor.call_api()

def add_send_mail_jobs(scheduler):
    """Add print jobs to scheduler"""
    scheduler.add_job(
        send_mail,
        'interval',
        minutes=1,
        id='send_mail_to_crm',
        replace_existing=True
    )
    
    logger.info("Print jobs added to scheduler")
