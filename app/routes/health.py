"""
Health-check route
"""
from fastapi import APIRouter, HTTPException
from app.models.data_model import HealthResponse
from app.db.mongodb import get_database
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
        # Check database connection
        database_status = "healthy"
        try:
            db = get_database()
            if db is None:
                database_status = "disconnected"
            else:
                # Try to ping the database
                await db.command("ping")
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            database_status = "unhealthy"
        
        # Check scheduler status
        scheduler_status = "healthy"
        try:
            scheduler = get_scheduler()
            if not scheduler.running:
                scheduler_status = "stopped"
        except Exception as e:
            logger.error(f"Scheduler health check failed: {e}")
            scheduler_status = "unhealthy"
        
        # Determine overall status
        overall_status = "healthy"
        if database_status != "healthy" or scheduler_status != "healthy":
            overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            database_status=database_status,
            scheduler_status=scheduler_status
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/health/database")
async def database_health():
    """
    Database-specific health check
    """
    try:
        db = get_database()
        if db is None:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        # Try to ping the database
        await db.command("ping")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "message": "Database connection is working"
        }
    
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database health check failed: {str(e)}")

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