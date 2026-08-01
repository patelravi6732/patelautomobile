import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.settings_app.models import GarageSettings
from config.mongodb import get_mongo_collection

def update_database_address():
    print("Updating GarageSettings in SQLite database...")
    settings_obj = GarageSettings.objects.first()
    if settings_obj:
        settings_obj.address = "Near Dandi Pond, Dandi, Valsad, Gujarat - 396385"
        settings_obj.save()
        print("Updated SQLite GarageSettings address to Near Dandi Pond!")
    else:
        GarageSettings.objects.create(address="Near Dandi Pond, Dandi, Valsad, Gujarat - 396385")
        print("Created SQLite GarageSettings with Near Dandi Pond address!")

    mongo_coll = get_mongo_collection("garage_settings")
    if mongo_coll is not None:
        mongo_coll.update_many({}, {"$set": {"address": "Near Dandi Pond, Dandi, Valsad, Gujarat - 396385"}})
        print("Updated MongoDB garage_settings collection address!")

if __name__ == '__main__':
    update_database_address()
