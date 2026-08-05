import os
import django
from pymongo import MongoClient

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.settings_app.models import AdminProfile
from api.mongo_sync import get_mongo_db

def wipe_all_admins():
    print("Wiping all admin profiles clean to ZERO...")

    # 1. Clear SQLite AdminProfiles and Django Users
    AdminProfile.objects.all().delete()
    User.objects.all().delete()
    print("SQLite AdminProfile and User records wiped clean to 0.")

    # 2. Clear MongoDB Atlas admin_profiles collection
    mongo_db = get_mongo_db()
    if mongo_db is not None:
        mongo_db['admin_profiles'].delete_many({})
        print("MongoDB Atlas 'admin_profiles' collection wiped clean to 0.")

    print("All Admin accounts wiped clean to EXACTLY ZERO!")

if __name__ == '__main__':
    wipe_all_admins()
