"""
Gunicorn/Uvicorn entrypoint
"""
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging để hiển thị logs trong Docker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger(__name__)

# Import after adding to path
from app.main import app
from app.core.config import settings
from app.db.mongodb import mongodb
from pymongo import ASCENDING

async def startup():
    """Application startup"""
    collection = mongodb.get_collection(settings.NAME_COLLECTION_MODEL_SEND_MAIL)
    
    # Danh sách các trường cần được đánh index
    fields_to_index = ["email_id", "created_at"]
    
    collection.create_index("email_id", unique=True) # Trường email_id phải là duy nhất

    # --- Lấy danh sách index hiện có ---
    indexes = collection.index_information()
    existing_fields = [index["key"][0][0] for index in indexes.values() if "key" in index]

    # --- Tạo index cho những trường chưa có ---
    for field in fields_to_index:
        if field not in existing_fields:
            print(f"Tạo index cho trường '{field}' ...")
            collection.create_index(
                [(field, ASCENDING)],
                name=f"{field}_idx",
                background=True
            )

async def shutdown():
    """Application shutdown"""

# Add startup and shutdown events
app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)

if __name__ == "__main__":
    import uvicorn
    
    # Run with uvicorn
    uvicorn.run(
        "run:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )