"""
Health-check route
"""
from fastapi import APIRouter, HTTPException
from app.models.data_model import HealthResponse
from app.core.scheduler import get_scheduler
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns the status of the API, database, and scheduler
    """
    try:
        try:
            scheduler = get_scheduler()
            if not scheduler.running:
                scheduler_status = "stopped"
        except Exception as e:
            logger.error(f"Scheduler health check failed: {e}")
            scheduler_status = "unhealthy"
        
        # Determine overall status
        overall_status = "healthy"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            scheduler_status=scheduler_status
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")
@router.get("/health/scheduler")
async def scheduler_health():
    """
    Scheduler-specific health check
    """
    try:
        scheduler = get_scheduler()
        
        return {
            "status": "healthy" if scheduler.running else "stopped",
            "timestamp": datetime.now().isoformat(),
            "running": scheduler.running,
            "jobs_count": len(scheduler.get_jobs()),
            "message": "Scheduler is running" if scheduler.running else "Scheduler is stopped"
        }
    
    except Exception as e:
        logger.error(f"Scheduler health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Scheduler health check failed: {str(e)}")