import urllib.request
import json
import pymongo
from pymongo import MongoClient

ATLAS_URI = "mongodb+srv://rockpatel6732_db_user:FYwO0vlU8Vehe3DM@cluster0.zh8vtin.mongodb.net/patel_automobiles_db?retryWrites=true&w=majority&appName=Cluster0"
CLOUD_BIN_URL = "https://jsonblob.com/api/jsonBlob/019fea29-8149-759d-ad03-0c9b267e07b2"

def sync_cloud_to_mongodb():
    print("1. Fetching latest Master Store from Cloud Bin...")
    req = urllib.request.Request(CLOUD_BIN_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    
    print("2. Connecting to MongoDB Atlas...")
    client = MongoClient(ATLAS_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=10000)
    db = client['patel_automobiles_db']
    
    deleted_ids = [str(x) for x in (data.get('deletedIds') or [])]
    print(f"Deleted IDs count: {len(deleted_ids)}")
    
    # 1. Jobs
    jobs = [j for j in (data.get('jobs') or []) if j and str(j.get('id', '')) not in deleted_ids]
    if jobs:
        db.jobs.delete_many({})
        db.jobs.insert_many(jobs)
        print(f"[OK] Synced {len(jobs)} jobs to MongoDB Atlas 'jobs'")
        
    # 2. Invoices (Billing)
    invoices = [inv for inv in (data.get('invoices') or []) if inv and str(inv.get('id', '')) not in deleted_ids]
    if invoices:
        db.invoices.delete_many({})
        db.invoices.insert_many(invoices)
        print(f"[OK] Synced {len(invoices)} invoices to MongoDB Atlas 'invoices'")
        
    # 3. Inventory
    inventory = [i for i in (data.get('inventory') or []) if i and str(i.get('id', '')) not in deleted_ids and str(i.get('part_name', '')) not in deleted_ids]
    if inventory:
        db.inventory.delete_many({})
        db.inventory.insert_many(inventory)
        print(f"[OK] Synced {len(inventory)} inventory items to MongoDB Atlas 'inventory'")
        
    # 4. Customers
    customers = [c for c in (data.get('customers') or []) if c and str(c.get('id', '')) not in deleted_ids]
    if customers:
        db.customers.delete_many({})
        db.customers.insert_many(customers)
        print(f"[OK] Synced {len(customers)} customers to MongoDB Atlas 'customers'")
        
    # 5. Bookings
    bookings = [b for b in (data.get('bookings') or []) if b and str(b.get('id', '')) not in deleted_ids]
    if bookings:
        db.bookings.delete_many({})
        db.bookings.insert_many(bookings)
        print(f"[OK] Synced {len(bookings)} bookings to MongoDB Atlas 'bookings'")
        
    # 6. Khata Entries
    khata = [k for k in (data.get('khataEntries') or []) if k and str(k.get('id', '')) not in deleted_ids]
    if khata:
        db.khata_entries.delete_many({})
        db.khata_entries.insert_many(khata)
        print(f"[OK] Synced {len(khata)} khata entries to MongoDB Atlas 'khata_entries'")

    # 7. Messages
    messages = [m for m in (data.get('messages') or []) if m and str(m.get('id', '')) not in deleted_ids]
    if messages:
        db.messages.delete_many({})
        db.messages.insert_many(messages)
        print(f"[OK] Synced {len(messages)} messages to MongoDB Atlas 'messages'")

    print("\n[SUCCESS] ALL DATA HAS BEEN FULLY SYNCED TO MONGODB ATLAS DATABASE (patel_automobiles_db)!")

if __name__ == '__main__':
    sync_cloud_to_mongodb()
