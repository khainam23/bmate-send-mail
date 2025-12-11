"""
Send mail job - Gửi email data lên CRM
"""
import logging

from app.jobs.sync_kintone.index import sendKintone
from app.core.config import settings
from app.db.mongodb import mongodb

logger = logging.getLogger(__name__)

def send_kintone():
    """Gửi email data lên CRM"""
    try:
        collection = mongodb.get_collection(settings.NAME_COLLECTION_MODEL_SEND_MAIL)
            
        extracted_data = collection.find_one(
            {"is_sync_kintone": {"$exists": False}},
            sort=[("created_at", -1)]
        )
        
        if not extracted_data or not extracted_data.get("data"):
            logger.info("ℹ️  Không có dữ liệu để gửi API")
            return
        
        sendKintone(extracted_data.get('data'), None)
        collection.update_one({"_id": extracted_data["_id"]}, {"$set": {"is_sync_kintone": True}})
    except Exception as e:
        logger.error(f"❌ Error in send_kintone job: {e}", exc_info=True)

def add_send_kintone_jobs(scheduler):
    """Add send mail jobs to scheduler"""
    scheduler.add_job(
        send_kintone,
        'interval',
        minutes=settings.EMAIL_TIME_SEND,
        id='send_kintone_to_crm',
        replace_existing=True
    )
    
    logger.info(f"📤 Send kintone job added to scheduler (interval: {settings.EMAIL_TIME_SEND} minutes)")
