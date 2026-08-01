import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import (
    UserProfile, GarageSettings, Booking, InventoryItem, Customer,
    ServiceJob, JobPart, Invoice, Attendance
)

def seed():
    print("Seeding database...")
    # Ensure existing superuser/admin accounts have ADMIN role set
    for admin_user in User.objects.filter(is_superuser=True):
        UserProfile.objects.get_or_create(user=admin_user, defaults={'role': 'ADMIN', 'phone': '+918140371414'})

    # 3. Garage Settings
    settings, _ = GarageSettings.objects.get_or_create(
        id=1,
        defaults={
            'garage_name': 'Patel Automobiles',
            'address': 'Near Dandi Pond, Dandi, Valsad, Gujarat - 396385',
            'phone': '+91 81403 71414',
            'whatsapp_number': '+91 81403 71414'
        }
    )

    # 4. Inventory Items
    parts = [
        {'part_name': 'Engine Oil 4T 10W-30 (1L)', 'category': 'Engine Oil', 'price': 450.00, 'current_stock': 24, 'min_stock_alert': 5},
        {'part_name': 'Synthetic Engine Oil 15W-50', 'category': 'Engine Oil', 'price': 850.00, 'current_stock': 3, 'min_stock_alert': 5},
        {'part_name': 'Front Brake Shoe (Hero Splendor)', 'category': 'Brake', 'price': 180.00, 'current_stock': 15, 'min_stock_alert': 4},
        {'part_name': 'Rear Brake Pad Set (Honda Activa)', 'category': 'Brake', 'price': 220.00, 'current_stock': 2, 'min_stock_alert': 5},
        {'part_name': 'Clutch Cable (Bajaj Pulsar)', 'category': 'Cable', 'price': 120.00, 'current_stock': 10, 'min_stock_alert': 3},
        {'part_name': 'Spark Plug Dual Electrode', 'category': 'Electrical', 'price': 150.00, 'current_stock': 30, 'min_stock_alert': 8},
        {'part_name': 'Drive Chain & Sprocket Kit', 'category': 'Transmission', 'price': 1450.00, 'current_stock': 4, 'min_stock_alert': 2},
        {'part_name': 'Tubeless Tyre 90/90-12 (Rear)', 'category': 'Tyre', 'price': 1650.00, 'current_stock': 6, 'min_stock_alert': 2},
        {'part_name': '12V 5Ah Maintenance Free Battery', 'category': 'Battery', 'price': 1350.00, 'current_stock': 2, 'min_stock_alert': 3},
        {'part_name': 'Air Filter Cartridge', 'category': 'Filter', 'price': 210.00, 'current_stock': 18, 'min_stock_alert': 5},
    ]

    for p in parts:
        InventoryItem.objects.get_or_create(part_name=p['part_name'], defaults=p)

    # 5. Sample Bookings
    bookings = [
        {
            'customer_name': 'Vikram Patel',
            'mobile_number': '9876543210',
            'vehicle_number': 'GJ-07-AB-1234',
            'bike_model': 'Hero Splendor Plus',
            'complaint': 'Full service needed, engine noise check, oil change',
            'preferred_date': '2026-07-29',
            'preferred_time': '10:00 AM',
            'status': 'PENDING'
        },
        {
            'customer_name': 'Suresh Shah',
            'mobile_number': '9823456789',
            'vehicle_number': 'GJ-23-CD-5678',
            'bike_model': 'Honda Activa 6G',
            'complaint': 'Brake slipping and starting issue',
            'preferred_date': '2026-07-29',
            'preferred_time': '02:00 PM',
            'status': 'ACCEPTED'
        }
    ]
    for b in bookings:
        Booking.objects.get_or_create(vehicle_number=b['vehicle_number'], defaults=b)

    # 6. Sample Customer & ServiceJob
    cust1, _ = Customer.objects.get_or_create(
        vehicle_number='GJ-07-XY-9999',
        defaults={
            'customer_name': 'Anil Kumar',
            'phone': '9988776655',
            'pending_amount': 350.00,
            'visit_count': 3
        }
    )

    oil_item = InventoryItem.objects.filter(part_name__icontains='Engine Oil').first()
    brake_item = InventoryItem.objects.filter(part_name__icontains='Brake').first()

    job1, created_job = ServiceJob.objects.get_or_create(
        vehicle_number='GJ-07-XY-9999',
        status='IN_PROGRESS',
        defaults={
            'customer_name': 'Anil Kumar',
            'mobile_number': '9988776655',
            'bike_model': 'Bajaj Pulsar 150',
            'assigned_mechanic': 'Ramesh Mechanic',
            'labour_charge': 300.00,
            'parts_confirmed': False
        }
    )
    if created_job and oil_item:
        JobPart.objects.create(
            job=job1,
            inventory_item=oil_item,
            part_name=oil_item.part_name,
            unit_price=oil_item.price,
            quantity=1,
            status='STAGED'
        )

    # 7. Sample Attendance
    Attendance.objects.get_or_create(
        mechanic_name='Ramesh Mechanic',
        date='2026-07-28',
        defaults={'check_in': '09:00:00', 'status': 'PRESENT'}
    )

    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed()
