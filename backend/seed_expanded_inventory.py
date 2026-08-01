import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.inventory.models import InventoryItem
from config.mongodb import log_to_mongo

def seed_expanded_inventory():
    print("Seeding expanded Indian two-wheeler inventory catalog across all categories...")

    items = [
        # --- 1. ENGINE OIL ---
        {'part_name': 'Castrol Power1 4T 10W-30 (1L)', 'category': 'Engine Oil', 'price': 450.00, 'current_stock': 30, 'min_stock_alert': 5},
        {'part_name': 'Motul 7100 4T 20W-50 Fully Synthetic (1L)', 'category': 'Engine Oil', 'price': 850.00, 'current_stock': 12, 'min_stock_alert': 3},
        {'part_name': 'Motul 3100 4T Gold 20W-40 (1L)', 'category': 'Engine Oil', 'price': 420.00, 'current_stock': 20, 'min_stock_alert': 5},
        {'part_name': 'Gulf Pride 4T Plus 10W-30 (900ml)', 'category': 'Engine Oil', 'price': 380.00, 'current_stock': 25, 'min_stock_alert': 5},
        {'part_name': 'Shell Advance AX7 10W-40 4T (1L)', 'category': 'Engine Oil', 'price': 460.00, 'current_stock': 18, 'min_stock_alert': 4},
        {'part_name': 'Servo 4T Synthetic 10W-30 (900ml)', 'category': 'Engine Oil', 'price': 360.00, 'current_stock': 22, 'min_stock_alert': 5},
        {'part_name': 'HP Racer 4T 20W-40 (1L)', 'category': 'Engine Oil', 'price': 350.00, 'current_stock': 15, 'min_stock_alert': 4},
        {'part_name': 'Honda Genuine Engine Oil 10W-30 (800ml)', 'category': 'Engine Oil', 'price': 390.00, 'current_stock': 40, 'min_stock_alert': 8},
        {'part_name': 'Hero Genuine Engine Oil 10W-30 (900ml)', 'category': 'Engine Oil', 'price': 380.00, 'current_stock': 35, 'min_stock_alert': 8},
        {'part_name': 'Yamalube 4T 10W-40 (1L)', 'category': 'Engine Oil', 'price': 440.00, 'current_stock': 15, 'min_stock_alert': 4},

        # --- 2. BRAKE ---
        {'part_name': 'Hero Splendor / Passion Front Brake Shoe (ASK)', 'category': 'Brake', 'price': 180.00, 'current_stock': 35, 'min_stock_alert': 8},
        {'part_name': 'Hero Splendor / Passion Rear Brake Shoe (ASK)', 'category': 'Brake', 'price': 180.00, 'current_stock': 35, 'min_stock_alert': 8},
        {'part_name': 'Honda Activa 3G/4G/5G/6G Front Brake Shoe (Minda)', 'category': 'Brake', 'price': 210.00, 'current_stock': 40, 'min_stock_alert': 10},
        {'part_name': 'Honda Activa Rear Brake Shoe (Minda)', 'category': 'Brake', 'price': 210.00, 'current_stock': 40, 'min_stock_alert': 10},
        {'part_name': 'Bajaj Pulsar 150/180/220 Front Disc Brake Pads (Endurance)', 'category': 'Brake', 'price': 320.00, 'current_stock': 20, 'min_stock_alert': 5},
        {'part_name': 'TVS Apache RTR 160/180 Front Disc Brake Pads', 'category': 'Brake', 'price': 350.00, 'current_stock': 18, 'min_stock_alert': 4},
        {'part_name': 'TVS Jupiter Front / Rear Brake Shoe', 'category': 'Brake', 'price': 200.00, 'current_stock': 25, 'min_stock_alert': 5},
        {'part_name': 'Royal Enfield Classic 350 Front Disc Pads (ByBre)', 'category': 'Brake', 'price': 550.00, 'current_stock': 12, 'min_stock_alert': 3},
        {'part_name': 'Yamaha FZ / R15 Front Disc Pads', 'category': 'Brake', 'price': 450.00, 'current_stock': 15, 'min_stock_alert': 3},
        {'part_name': 'Suzuki Access 125 Front Disc Pads', 'category': 'Brake', 'price': 280.00, 'current_stock': 15, 'min_stock_alert': 4},
        {'part_name': 'Brake Fluid DOT 4 (250ml)', 'category': 'Brake', 'price': 120.00, 'current_stock': 20, 'min_stock_alert': 5},

        # --- 3. CABLE ---
        {'part_name': 'Hero Splendor Clutch Cable (Uno Minda)', 'category': 'Cable', 'price': 120.00, 'current_stock': 25, 'min_stock_alert': 5},
        {'part_name': 'Hero Splendor Accelerator Cable', 'category': 'Cable', 'price': 110.00, 'current_stock': 20, 'min_stock_alert': 5},
        {'part_name': 'Hero Splendor Front Brake Cable', 'category': 'Cable', 'price': 110.00, 'current_stock': 20, 'min_stock_alert': 5},
        {'part_name': 'Honda Activa Accelerator Throttle Cable', 'category': 'Cable', 'price': 140.00, 'current_stock': 25, 'min_stock_alert': 5},
        {'part_name': 'Honda Activa Front Brake Cable', 'category': 'Cable', 'price': 150.00, 'current_stock': 25, 'min_stock_alert': 5},
        {'part_name': 'Honda Activa Speedometer Cable', 'category': 'Cable', 'price': 90.00, 'current_stock': 30, 'min_stock_alert': 6},
        {'part_name': 'Bajaj Pulsar 150 Heavy Clutch Cable', 'category': 'Cable', 'price': 160.00, 'current_stock': 15, 'min_stock_alert': 4},
        {'part_name': 'TVS Apache RTR Clutch Cable', 'category': 'Cable', 'price': 170.00, 'current_stock': 15, 'min_stock_alert': 4},
        {'part_name': 'TVS Jupiter Speedometer Cable', 'category': 'Cable', 'price': 95.00, 'current_stock': 20, 'min_stock_alert': 5},
        {'part_name': 'Royal Enfield Classic 350 Clutch Cable', 'category': 'Cable', 'price': 220.00, 'current_stock': 10, 'min_stock_alert': 3},

        # --- 4. ELECTRICAL ---
        {'part_name': 'Spark Plug Bosch UR4AC (Splendor/HF Deluxe)', 'category': 'Electrical', 'price': 95.00, 'current_stock': 50, 'min_stock_alert': 10},
        {'part_name': 'Spark Plug NGK CPR8EA-9 (Activa/Shine)', 'category': 'Electrical', 'price': 110.00, 'current_stock': 50, 'min_stock_alert': 10},
        {'part_name': 'Spark Plug NGK Laser Iridium (High Performance)', 'category': 'Electrical', 'price': 650.00, 'current_stock': 10, 'min_stock_alert': 2},
        {'part_name': 'Headlight Bulb Halogen 12V 35/35W HS1 (Philips)', 'category': 'Electrical', 'price': 140.00, 'current_stock': 30, 'min_stock_alert': 6},
        {'part_name': 'LED Headlight Bulb 12V Universal High Beam', 'category': 'Electrical', 'price': 350.00, 'current_stock': 15, 'min_stock_alert': 4},
        {'part_name': 'Dual Tone Horn 12V Set (Roots / Bosch)', 'category': 'Electrical', 'price': 380.00, 'current_stock': 12, 'min_stock_alert': 3},
        {'part_name': 'Indicator Light Assembly Universal (Clear Lens)', 'category': 'Electrical', 'price': 85.00, 'current_stock': 40, 'min_stock_alert': 8},
        {'part_name': 'Tail Light Bulb 12V (Philips)', 'category': 'Electrical', 'price': 40.00, 'current_stock': 40, 'min_stock_alert': 10},
        {'part_name': 'Ignition Coil Unit (Uno Minda)', 'category': 'Electrical', 'price': 320.00, 'current_stock': 10, 'min_stock_alert': 3},
        {'part_name': 'Flasher Relay Unit 12V (Auto Indicator)', 'category': 'Electrical', 'price': 90.00, 'current_stock': 25, 'min_stock_alert': 5},

        # --- 5. TRANSMISSION ---
        {'part_name': 'Hero Splendor Chain & Sprocket Kit (Rolon)', 'category': 'Transmission', 'price': 850.00, 'current_stock': 15, 'min_stock_alert': 3},
        {'part_name': 'Honda CB Shine Chain & Sprocket Kit (Rolon)', 'category': 'Transmission', 'price': 980.00, 'current_stock': 12, 'min_stock_alert': 3},
        {'part_name': 'Bajaj Pulsar 150 Chain & Sprocket Kit (Rolon Heavy)', 'category': 'Transmission', 'price': 1250.00, 'current_stock': 10, 'min_stock_alert': 3},
        {'part_name': 'TVS Apache RTR 160 Chain Sprocket Kit', 'category': 'Transmission', 'price': 1350.00, 'current_stock': 10, 'min_stock_alert': 3},
        {'part_name': 'Royal Enfield Classic 350 Chain Sprocket Kit', 'category': 'Transmission', 'price': 1850.00, 'current_stock': 8, 'min_stock_alert': 2},
        {'part_name': 'Honda Activa Drive Belt / Variator Belt (Bando)', 'category': 'Transmission', 'price': 480.00, 'current_stock': 20, 'min_stock_alert': 5},
        {'part_name': 'TVS Jupiter Variator Clutch Rollers Set', 'category': 'Transmission', 'price': 220.00, 'current_stock': 18, 'min_stock_alert': 4},
        {'part_name': 'Clutch Friction Plate Set Hero Splendor (FCC)', 'category': 'Transmission', 'price': 380.00, 'current_stock': 15, 'min_stock_alert': 4},
        {'part_name': 'Clutch Plate Set Bajaj Pulsar 150', 'category': 'Transmission', 'price': 580.00, 'current_stock': 12, 'min_stock_alert': 3},
        {'part_name': 'Scooter Clutch Shoe Assembly (Activa 5G/6G)', 'category': 'Transmission', 'price': 1200.00, 'current_stock': 8, 'min_stock_alert': 2},

        # --- 6. TYRE (ALL POPULAR SIZES & BRANDS) ---
        {'part_name': 'MRF Zapper 90/90-12 Tubeless Scooter Tyre', 'category': 'Tyre', 'price': 1250.00, 'current_stock': 15, 'min_stock_alert': 3},
        {'part_name': 'CEAT Gripp X3 90/90-12 Tubeless Scooter Tyre', 'category': 'Tyre', 'price': 1180.00, 'current_stock': 15, 'min_stock_alert': 3},
        {'part_name': 'TVS Eurogrip 90/90-12 Tubeless Scooter Tyre', 'category': 'Tyre', 'price': 1100.00, 'current_stock': 12, 'min_stock_alert': 3},
        {'part_name': 'Apollo ActiGrip 90/90-12 Tubeless Scooter Tyre', 'category': 'Tyre', 'price': 1150.00, 'current_stock': 10, 'min_stock_alert': 3},
        {'part_name': 'MRF Nylogrip Zapper 2.75-18 Tube Type Front Tyre', 'category': 'Tyre', 'price': 1450.00, 'current_stock': 12, 'min_stock_alert': 3},
        {'part_name': 'CEAT Secura Zoom F 2.75-18 Tube Type Front Tyre', 'category': 'Tyre', 'price': 1380.00, 'current_stock': 10, 'min_stock_alert': 3},
        {'part_name': 'MRF Zapper Y 3.00-18 Tube Type Rear Tyre', 'category': 'Tyre', 'price': 1650.00, 'current_stock': 10, 'min_stock_alert': 3},
        {'part_name': 'CEAT Gripp X3 100/90-17 Tubeless Rear Tyre (Pulsar/Apache)', 'category': 'Tyre', 'price': 1950.00, 'current_stock': 8, 'min_stock_alert': 2},
        {'part_name': 'MRF Zapper FX 120/80-17 Tubeless Rear Tyre (FZ/Pulsar 220)', 'category': 'Tyre', 'price': 2450.00, 'current_stock': 6, 'min_stock_alert': 2},
        {'part_name': 'Ralco Speed Blaster 3.25-19 Heavy Duty Bullet Tyre', 'category': 'Tyre', 'price': 2250.00, 'current_stock': 5, 'min_stock_alert': 2},
        {'part_name': 'Heavy Duty Butyl Inner Tube 2.75-18', 'category': 'Tyre', 'price': 280.00, 'current_stock': 30, 'min_stock_alert': 6},
        {'part_name': 'Heavy Duty Butyl Inner Tube 90/90-12', 'category': 'Tyre', 'price': 240.00, 'current_stock': 30, 'min_stock_alert': 6},

        # --- 7. BATTERY (EXIDE, AMARON, TATA) ---
        {'part_name': 'Exide Rider 12V 4Ah Maintenance Free Battery (XLTZ4)', 'category': 'Battery', 'price': 1150.00, 'current_stock': 15, 'min_stock_alert': 3},
        {'part_name': 'Amaron Beta 12V 4Ah Maintenance Free Battery (ABTZ4L)', 'category': 'Battery', 'price': 1180.00, 'current_stock': 15, 'min_stock_alert': 3},
        {'part_name': 'Exide Xplore 12V 5Ah Battery (Activa 5G/6G/Jupiter)', 'category': 'Battery', 'price': 1350.00, 'current_stock': 12, 'min_stock_alert': 3},
        {'part_name': 'Amaron Pro Rider 12V 5Ah Battery', 'category': 'Battery', 'price': 1380.00, 'current_stock': 12, 'min_stock_alert': 3},
        {'part_name': 'Exide Rider 12V 9Ah Heavy Duty Battery (Pulsar/Bullet)', 'category': 'Battery', 'price': 1950.00, 'current_stock': 8, 'min_stock_alert': 2},
        {'part_name': 'Amaron Pro Bike Rider 12V 9Ah Battery', 'category': 'Battery', 'price': 1980.00, 'current_stock': 8, 'min_stock_alert': 2},
        {'part_name': 'Tata Green Velocity 12V 2.5Ah Kick Start Battery', 'category': 'Battery', 'price': 880.00, 'current_stock': 10, 'min_stock_alert': 2},

        # --- 8. FILTER ---
        {'part_name': 'Hero Splendor Foam Air Filter Element', 'category': 'Filter', 'price': 90.00, 'current_stock': 40, 'min_stock_alert': 8},
        {'part_name': 'Honda Activa 3G/4G/5G Viscous Paper Air Filter', 'category': 'Filter', 'price': 160.00, 'current_stock': 35, 'min_stock_alert': 8},
        {'part_name': 'Honda Activa 6G / BS6 Paper Air Filter', 'category': 'Filter', 'price': 180.00, 'current_stock': 30, 'min_stock_alert': 6},
        {'part_name': 'Bajaj Pulsar 150 Dual Layer Air Filter Foam', 'category': 'Filter', 'price': 110.00, 'current_stock': 25, 'min_stock_alert': 5},
        {'part_name': 'TVS Apache RTR Viscous Paper Air Filter', 'category': 'Filter', 'price': 140.00, 'current_stock': 20, 'min_stock_alert': 4},
        {'part_name': 'Honda CB Shine Air Filter Element', 'category': 'Filter', 'price': 130.00, 'current_stock': 25, 'min_stock_alert': 5},
        {'part_name': 'Royal Enfield Classic 350 Air Filter Element', 'category': 'Filter', 'price': 220.00, 'current_stock': 15, 'min_stock_alert': 4},
        {'part_name': 'Engine Oil Filter Element (Pulsar/RTR/Bullet)', 'category': 'Filter', 'price': 65.00, 'current_stock': 50, 'min_stock_alert': 10},
        {'part_name': 'Fuel Filter Inline Transparent (Universal)', 'category': 'Filter', 'price': 45.00, 'current_stock': 50, 'min_stock_alert': 10},

        # --- 9. GENERAL ---
        {'part_name': 'Motul C2 Chain Lube Spray Can (150ml)', 'category': 'General', 'price': 220.00, 'current_stock': 25, 'min_stock_alert': 5},
        {'part_name': 'Motul C1 Chain Cleaner Spray Can (150ml)', 'category': 'General', 'price': 200.00, 'current_stock': 20, 'min_stock_alert': 5},
        {'part_name': 'WD-40 Anti-Rust Multi-Use Spray (100ml)', 'category': 'General', 'price': 110.00, 'current_stock': 35, 'min_stock_alert': 8},
        {'part_name': '3M Bike Wash Shampoo (250ml)', 'category': 'General', 'price': 140.00, 'current_stock': 20, 'min_stock_alert': 4},
        {'part_name': 'Liquid Polish & Shiner Wax (Formula 1)', 'category': 'General', 'price': 180.00, 'current_stock': 15, 'min_stock_alert': 4},
        {'part_name': 'Hero Splendor Rear Mirror Pair (Left + Right)', 'category': 'General', 'price': 180.00, 'current_stock': 15, 'min_stock_alert': 3},
        {'part_name': 'Honda Activa Rear Mirror Pair (Left + Right)', 'category': 'General', 'price': 210.00, 'current_stock': 15, 'min_stock_alert': 3},
        {'part_name': 'Handle Grip Rubber Pair (Soft Rubber)', 'category': 'General', 'price': 80.00, 'current_stock': 30, 'min_stock_alert': 6},
        {'part_name': 'Side Stand Assembly Heavy Duty (Splendor/Activa)', 'category': 'General', 'price': 130.00, 'current_stock': 20, 'min_stock_alert': 4},
        {'part_name': 'Main Center Stand Assembly (Hero/Honda)', 'category': 'General', 'price': 340.00, 'current_stock': 10, 'min_stock_alert': 2},
        {'part_name': 'Front Shock Absorber Oil (350ml)', 'category': 'General', 'price': 120.00, 'current_stock': 25, 'min_stock_alert': 5},
    ]

    added_count = 0
    updated_count = 0

    for item in items:
        obj, created = InventoryItem.objects.get_or_create(
            part_name=item['part_name'],
            defaults=item
        )
        if created:
            added_count += 1
            log_to_mongo("inventory_logs", {
                "event": "ITEM_CREATED",
                "part_name": item['part_name'],
                "category": item['category'],
                "price": item['price'],
                "current_stock": item['current_stock']
            })
        else:
            obj.category = item['category']
            obj.price = item['price']
            obj.min_stock_alert = item['min_stock_alert']
            obj.save()
            updated_count += 1

    print(f"Successfully seeded {added_count} new inventory items ({updated_count} existing verified) across all 9 Indian categories!")

if __name__ == '__main__':
    seed_expanded_inventory()
