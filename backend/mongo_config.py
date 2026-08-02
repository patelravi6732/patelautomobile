"""
Patel Automobiles - Python PyMongo / MongoEngine Connection Configuration
Use this to connect Python Django / FastAPI / Flask to MongoDB Atlas on Vercel or cloud hosts.
"""

import os
try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None

MONGODB_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI", "")

def get_db():
    if not MongoClient:
        return None
    if not MONGODB_URI:
        print("MongoDB connection warning: MONGODB_URI is not configured")
        return None
    try:
        client = MongoClient(MONGODB_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
        return client['patel_automobiles_db']
    except Exception as e:
        print(f"MongoDB connection warning: {e}")
        return None

def init_mongo_collections():
    db = get_db()
    if db is None:
        return False
    collections = ['bookings', 'jobs', 'inventory', 'customers', 'billing', 'recycle_bin', 'messages', 'settings']
    for col in collections:
        if col not in db.list_collection_names():
            db.create_collection(col)
    print("✅ MongoDB Atlas collections initialized successfully!")
    return True

if __name__ == '__main__':
    init_mongo_collections()
