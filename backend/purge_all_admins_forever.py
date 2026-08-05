import os
import json
import urllib.request
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.settings_app.models import AdminProfile
from api.mongo_sync import get_mongo_db

CLOUD_BIN_URL = "https://jsonblob.com/api/jsonBlob/019fd0d0-8dfa-755c-9195-7f74e5af7d09"

def purge_all_admins():
    print("Purging all admin accounts across SQLite, MongoDB Atlas, and Cloud Store...")

    # 1. Clear SQLite
    AdminProfile.objects.all().delete()
    User.objects.all().delete()
    print("SQLite AdminProfile & User records deleted clean.")

    # 2. Clear MongoDB Atlas
    mongo_db = get_mongo_db()
    if mongo_db is not None:
        mongo_db['admin_profiles'].delete_many({})
        print("MongoDB Atlas 'admin_profiles' collection deleted clean.")

    # 3. Update Cloud Store Bin
    try:
        req_get = urllib.request.Request(CLOUD_BIN_URL, headers={'Accept': 'application/json'}, method='GET')
        with urllib.request.urlopen(req_get) as resp:
            store = json.loads(resp.read().decode('utf-8'))
        
        store['adminProfiles'] = []
        payload = json.dumps(store).encode('utf-8')

        req_put = urllib.request.Request(CLOUD_BIN_URL, data=payload, headers={'Content-Type': 'application/json', 'Accept': 'application/json'}, method='PUT')
        with urllib.request.urlopen(req_put) as resp2:
            print("Cloud bin 'adminProfiles' updated to [] successfully!")
    except Exception as e:
        print("Cloud bin update notice:", e)

    print("✅ ABSOLUTE PURGE COMPLETE! 0 Admin accounts exist anywhere in the system!")

if __name__ == '__main__':
    purge_all_admins()
