import os
import pymongo
from pymongo import MongoClient

ATLAS_URI = "mongodb+srv://rockpatel6732_db_user:FYwO0vlU8Vehe3DM@cluster0.zh8vtin.mongodb.net/patel_automobiles_db?retryWrites=true&w=majority&appName=Cluster0"

def sync_to_atlas():
    try:
        client = MongoClient(ATLAS_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
        db = client['patel_automobiles_db']
        
        collections = ['bookings', 'jobs', 'inventory', 'customers', 'billing', 'recycle_bin', 'messages', 'settings', 'admin_profiles', 'khata_entries']
        for col in collections:
            if col not in db.list_collection_names():
                db.create_collection(col)
                print(f"Created collection: {col}")
                
        print("MongoDB Atlas patel_automobiles_db collections verified & ready!")
        return True
    except Exception as e:
        print(f"MongoDB Atlas Sync Error: {e}")
        return False

if __name__ == '__main__':
    sync_to_atlas()
