"""
Simple print job for testing scheduler
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def hello_world_job():
    """Simple job that prints Hello World to the console"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Hello World! Current time: {current_time}"
        
        print(message)  # In ra console
        logger.info(message)  # Ghi vào log
        
        return {"status": "success", "message": message}
    except Exception as e:
        error_msg = f"Hello World job failed: {e}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

def add_print_jobs(scheduler):
    """Add print jobs to scheduler"""
    # Run hello world job every minute for testing
    scheduler.add_job(
        hello_world_job,
        'interval',
        seconds=30,  # Chạy mỗi 30 giây để dễ kiểm tra
        id='hello_world_job',
        replace_existing=True
    )
    
    logger.info("Print jobs added to scheduler")
