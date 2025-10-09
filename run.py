"""
Gunicorn/Uvicorn entrypoint
"""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after adding to path
from app.main import app
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection

async def startup():
    """Application startup"""
    await connect_to_mongo()

async def shutdown():
    """Application shutdown"""
    await close_mongo_connection()

# Add startup and shutdown events
app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)

if __name__ == "__main__":
    import uvicorn
    
    # Run with uvicorn
    uvicorn.run(
        "run:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )