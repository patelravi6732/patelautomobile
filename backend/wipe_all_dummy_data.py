import os
import pymongo
from pymongo import MongoClient

ATLAS_URI = "mongodb+srv://rockpatel6732_db_user:FYwO0vlU8Vehe3DM@cluster0.zh8vtin.mongodb.net/patel_automobiles_db?retryWrites=true&w=majority&appName=Cluster0"

def wipe_dummy_data():
    try:
        client = MongoClient(ATLAS_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
        db = client['patel_automobiles_db']
        
        # 1. Clear operational collections
        collections_to_wipe = ['bookings', 'jobs', 'inventory', 'customers', 'billing', 'recycle_bin', 'messages', 'khata_entries', 'attendance', 'salary_payments']
        for col_name in collections_to_wipe:
            col = db[col_name]
            deleted_res = col.delete_many({})
            print(f"Cleared collection '{col_name}': {deleted_res.deleted_count} records removed.")

        print("MongoDB Atlas patel_automobiles_db operational data wiped successfully!")

        return True
    except Exception as e:
        print(f"Error wiping MongoDB Atlas data: {e}")
        return False

if __name__ == '__main__':
    wipe_dummy_data()
