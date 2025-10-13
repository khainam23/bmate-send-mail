"""
MongoDB connection
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.core.config import settings

logger = logging.getLogger(__name__)
class MongoDBSync:
    def __init__(self, uri: str, db_name: str):
        self.client = MongoClient(uri)
        self.database = self.client[db_name]

    def get_collection(self, name: str):
        return self.database[name]

mongodb = MongoDBSync(settings.MONGODB_URL, settings.DATABASE_NAME)