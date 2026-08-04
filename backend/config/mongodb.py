import os
import logging
try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI") or "mongodb+srv://rockpatel6732_db_user:FYwO0vlU8Vehe3DM@cluster0.zh8vtin.mongodb.net/patel_automobiles_db?retryWrites=true&w=majority&appName=Cluster0"
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "patel_automobiles_db")

mongo_client = None
mongo_db = None

if MONGODB_AVAILABLE:
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000, tlsAllowInvalidCertificates=True)
        mongo_db = mongo_client[MONGO_DB_NAME]
        logger.info(f"MongoDB connection initialized for database: {MONGO_DB_NAME}")
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}. Falling back to Django SQL backend.")

def get_mongo_collection(collection_name):
    if mongo_db is not None:
        return mongo_db[collection_name]
    return None

def log_to_mongo(collection_name, data):
    """
    Utility function to log document data to MongoDB collection.
    """
    coll = get_mongo_collection(collection_name)
    if coll is not None:
        try:
            coll.insert_one(data)
            return True
        except Exception as e:
            logger.error(f"Failed to log to MongoDB: {e}")
    return False
