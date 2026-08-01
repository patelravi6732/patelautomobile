"""
Patel Automobiles - Python PyMongo / MongoEngine Connection Configuration
Use this to connect Python Django / FastAPI / Flask to MongoDB Atlas on Vercel or cloud hosts.
"""

import os
try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None

MONGODB_URI = os.getenv(
    "MONGODB_URI", 
    "mongodb+srv://patelautomobile:patelautomobile123@cluster0.mongodb.net/patelautomobile?retryWrites=true&w=majority"
)

def get_db():
    if not MongoClient:
        return None
    client = MongoClient(MONGODB_URI)
    return client['patelautomobile']

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
