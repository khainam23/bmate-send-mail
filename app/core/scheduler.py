"""
APScheduler setup
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Scheduler configuration
jobstores = {
    'default': MemoryJobStore()
}

executors = {
    'default': ThreadPoolExecutor(max_workers=10)
}

job_defaults = {
    'coalesce': False,
    'max_instances': 3,
    'misfire_grace_time': 60  # Cho phép job chạy muộn tối đa 60 giây
}

# Create scheduler instance
scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=settings.SCHEDULER_TIMEZONE
)

def start_scheduler():
    """Start the scheduler"""
    try:
        # Import and add jobs
        from app.jobs.sync_email_job import add_sync_email_jobs
        from app.jobs.send_mail_job import add_send_mail_jobs
        
        logger.info("🔧 Adding jobs to scheduler...")
        add_sync_email_jobs(scheduler)
        add_send_mail_jobs(scheduler)
        
        scheduler.start()
        logger.info("✅ Scheduler started successfully")
        
        # Log all scheduled jobs
        jobs = scheduler.get_jobs()
        logger.info(f"📋 Total jobs scheduled: {len(jobs)}")
        for job in jobs:
            logger.info(f"  - {job.id}: {job.trigger}")
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}", exc_info=True)

def stop_scheduler():
    """Stop the scheduler"""
    try:
        scheduler.shutdown()
        logger.info("Scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")

def get_scheduler():
    """Get scheduler instance"""
    return scheduler