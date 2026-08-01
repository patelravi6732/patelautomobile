import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.settings_app.models import GarageSettings
from apps.inventory.models import InventoryItem
from apps.bookings.models import Booking
from apps.customers.models import Customer
from apps.workshop.models import ServiceJob, JobPart
from apps.billing.models import Invoice
from apps.attendance.models import Attendance

def seed_clean():
    print("Seeding production database for Patel Automobiles, Dandi, Valsad, Gujarat...")

    # Clear old data
    Booking.objects.all().delete()
    JobPart.objects.all().delete()
    Invoice.objects.all().delete()
    ServiceJob.objects.all().delete()
    Customer.objects.all().delete()
    Attendance.objects.all().delete()
    GarageSettings.objects.all().delete()

    # Ensure existing superuser/admin accounts have ADMIN role set
    for admin_user in User.objects.filter(is_superuser=True):
        prof, _ = UserProfile.objects.get_or_create(user=admin_user)
        prof.role = 'ADMIN'
        prof.failed_attempts = 0
        prof.lockout_until = None
        prof.save()

    # Garage Settings for Patel Automobiles, Dandi, Valsad, Gujarat
    GarageSettings.objects.create(
        id=1,
        garage_name='Patel Automobiles',
        address='Near Dandi Pond, Dandi, Valsad, Gujarat - 396385',
        phone='+91 81403 71414',
        whatsapp_number='+91 81403 71414',
        email='contact@patelautomobiles.com',
        timing_text='Mon - Sat: 09:00 AM - 08:30 PM, Sun: 09:00 AM - 02:00 PM',
        mechanics_list='Patel Owner, Ramesh Mechanic, Suresh Technician',
        default_labour_charge=300.00,
        default_min_stock=5
    )

    # Standard Real Two-Wheeler Spare Parts Inventory Catalog
    parts = [
        {'part_name': 'Engine Oil 4T 10W-30 (1L)', 'category': 'Engine Oil', 'price': 450.00, 'current_stock': 25, 'min_stock_alert': 5},
        {'part_name': 'Synthetic Engine Oil 15W-50', 'category': 'Engine Oil', 'price': 850.00, 'current_stock': 10, 'min_stock_alert': 3},
        {'part_name': 'Front Brake Shoe (Hero Splendor)', 'category': 'Brake', 'price': 180.00, 'current_stock': 15, 'min_stock_alert': 4},
        {'part_name': 'Rear Brake Pad Set (Honda Activa)', 'category': 'Brake', 'price': 220.00, 'current_stock': 12, 'min_stock_alert': 4},
        {'part_name': 'Clutch Cable (Bajaj Pulsar)', 'category': 'Cable', 'price': 120.00, 'current_stock': 10, 'min_stock_alert': 3},
        {'part_name': 'Spark Plug Dual Electrode', 'category': 'Electrical', 'price': 150.00, 'current_stock': 30, 'min_stock_alert': 8},
        {'part_name': 'Drive Chain & Sprocket Kit', 'category': 'Transmission', 'price': 1450.00, 'current_stock': 8, 'min_stock_alert': 2},
        {'part_name': 'Tubeless Tyre 90/90-12 (Rear)', 'category': 'Tyre', 'price': 1650.00, 'current_stock': 6, 'min_stock_alert': 2},
        {'part_name': '12V 5Ah Maintenance Free Battery', 'category': 'Battery', 'price': 1350.00, 'current_stock': 5, 'min_stock_alert': 2},
        {'part_name': 'Air Filter Cartridge', 'category': 'Filter', 'price': 210.00, 'current_stock': 20, 'min_stock_alert': 5},
    ]

    for p in parts:
        InventoryItem.objects.get_or_create(part_name=p['part_name'], defaults=p)

    print("Patel Automobiles database initialized cleanly! Location: Dandi, Valsad, Gujarat.")

if __name__ == '__main__':
    seed_clean()
