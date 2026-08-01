import os
import sys
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.inventory.models import InventoryItem
from apps.workshop.models import JobPart
from config.mongodb import log_to_mongo, get_mongo_collection

def generate_1000_items():
    print("Generating 1000 items across 20 categories with initial stock set to 6...")

    # Define the 20 exact categories requested
    categories = [
        'Engine Oil', 'Air Filter', 'Oil Filter', 'Spark Plug', 'Brake Shoe',
        'Brake Pad', 'Chain Kit', 'Clutch Plate', 'Clutch Cable', 'Accelerator Cable',
        'Bulbs', 'Battery', 'Tyres', 'Tubes', 'Fuses',
        'Horn', 'Mirrors', 'Footrest', 'Grease & Lubricants', 'Coolant / Brake Oil'
    ]

    # Models list for realistic naming
    models = [
        'Hero Splendor Plus', 'Hero HF Deluxe', 'Hero Passion Pro', 'Hero Glamour 125', 'Hero Xpulse 200', 'Hero Maestro Edge',
        'Honda Activa 3G/4G', 'Honda Activa 5G', 'Honda Activa 6G BS6', 'Honda Dio 110', 'Honda CB Shine 125', 'Honda Unicorn 160', 'Honda Hornet 2.0',
        'TVS Jupiter 110', 'TVS Jupiter 125', 'TVS XL100 HeavyDuty', 'TVS Apache RTR 160 2V', 'TVS Apache RTR 160 4V', 'TVS Apache RTR 180', 'TVS Apache RTR 200', 'TVS Raider 125', 'TVS Ntorq 125',
        'Bajaj Pulsar 125', 'Bajaj Pulsar 150', 'Bajaj Pulsar 180', 'Bajaj Pulsar 220F', 'Bajaj Pulsar NS200', 'Bajaj Platina 110 H-Gear', 'Bajaj Avenger Cruise 220', 'Bajaj CT110X',
        'Yamaha FZ-S V3', 'Yamaha R15 V3/V4', 'Yamaha MT-15 V2', 'Yamaha RayZR 125', 'Yamaha Fascino 125',
        'Royal Enfield Bullet 350', 'Royal Enfield Classic 350 Reborn', 'Royal Enfield Meteor 350', 'Royal Enfield Hunter 350', 'Royal Enfield Himalayan 411',
        'Suzuki Access 125', 'Suzuki Burgman Street 125', 'Suzuki Gixxer 150', 'KTM Duke 200', 'KTM Duke 390'
    ]

    all_items = []
    seen_names = set()

    def add_item(name, category, price):
        if name in seen_names:
            name = f"{name} ({random.randint(100, 999)})"
        seen_names.add(name)
        all_items.append({
            'part_name': name,
            'category': category,
            'price': round(float(price), 2),
            'current_stock': 6,  # User requested exact stock 6 for all items
            'min_stock_alert': 3
        })

    # 1. Engine Oil (50 items)
    oil_brands = ['Castrol Power1', 'Motul 7100', 'Motul 3100 Gold', 'Gulf Pride 4T', 'Shell Advance AX7', 'Servo 4T Synthetic', 'HP Racer 4T', 'Veedol Super 4T', 'Honda Genuine Oil', 'Hero Genuine Oil', 'Yamalube 4T', 'Bajaj DTS-i Oil', 'TVS TRU4 Oil', 'Mobil 1 Racing 4T', 'Liqui Moly 4T']
    oil_grades = ['10W-30', '20W-40', '10W-40', '15W-50', '20W-50', '5W-30', '10W-50']
    oil_vols = ['800ml', '900ml', '1L', '1.2L']
    for b in oil_brands:
        for g in oil_grades[:3]:
            for v in oil_vols[:2]:
                if len([i for i in all_items if i['category'] == 'Engine Oil']) < 50:
                    add_item(f"{b} {g} Engine Oil ({v})", 'Engine Oil', random.choice([350, 380, 420, 450, 480, 520, 650, 850]))

    # 2. Air Filter (50 items)
    filter_types = ['Foam Air Filter', 'Viscous Paper Air Filter Element', 'High Flow Performance Air Filter', 'Mesh Air Filter Cartridge']
    for m in models:
        if len([i for i in all_items if i['category'] == 'Air Filter']) < 50:
            add_item(f"{m} {random.choice(filter_types)}", 'Air Filter', random.choice([90, 110, 130, 150, 180, 220, 280, 350]))

    # 3. Oil Filter (50 items)
    of_brands = ['Bosch', 'Purolator', 'Uno Minda', 'Champion', 'Roots', 'Elofic', 'OEM Genuine', 'Sofima', 'K&N']
    for m in models:
        if len([i for i in all_items if i['category'] == 'Oil Filter']) < 50:
            b = random.choice(of_brands)
            add_item(f"{m} {b} Engine Oil Filter Cartridge", 'Oil Filter', random.choice([65, 85, 95, 120, 140, 180, 250]))

    # 4. Spark Plug (50 items)
    sp_brands = ['NGK', 'Bosch', 'Champion', 'Denso', 'Spark Minda']
    sp_types = ['Standard Copper', 'Power Spark Dual Electrode', 'Triple Spark', 'Laser Iridium High Power', 'Platinum Power']
    sp_codes = ['CPR8EA-9', 'UR4AC', 'CR7HSA', 'D8EA', 'RG6YC', 'CPR7EA-9', 'LMAR9AI-8', 'BPR6ES']
    for b in sp_brands:
        for t in sp_types:
            for c in sp_codes:
                if len([i for i in all_items if i['category'] == 'Spark Plug']) < 50:
                    add_item(f"{b} {t} Spark Plug ({c})", 'Spark Plug', random.choice([95, 110, 150, 220, 350, 650]))

    # 5. Brake Shoe (50 items)
    bs_brands = ['ASK', 'KBX', 'Uno Minda', 'Endurance', 'Varroc', 'OEM Genuine', 'Brembo']
    positions = ['Front', 'Rear']
    for m in models:
        for pos in positions:
            if len([i for i in all_items if i['category'] == 'Brake Shoe']) < 50:
                b = random.choice(bs_brands)
                add_item(f"{m} {pos} Brake Shoe Set ({b})", 'Brake Shoe', random.choice([160, 180, 210, 240, 280]))

    # 6. Brake Pad (50 items)
    bp_brands = ['Endurance', 'KBX', 'ByBre / Brembo', 'ASK', 'Uno Minda', 'Nissin', 'EBC Organic']
    for m in models:
        for pos in positions:
            if len([i for i in all_items if i['category'] == 'Brake Pad']) < 50:
                b = random.choice(bp_brands)
                add_item(f"{m} {pos} Disc Brake Pad Set ({b})", 'Brake Pad', random.choice([280, 320, 380, 450, 550, 750]))

    # 7. Chain Kit (50 items)
    ck_brands = ['Rolon', 'Diamond', 'RK Japan', 'LG Chains', 'OEM Genuine']
    ck_types = ['Heavy Duty Brass Chain Kit', 'O-Ring Drive Chain & Sprocket Set', 'Standard Drive Chain Kit', 'X-Ring Gold Chain Kit']
    for m in models:
        if len([i for i in all_items if i['category'] == 'Chain Kit']) < 50:
            b = random.choice(ck_brands)
            t = random.choice(ck_types)
            add_item(f"{m} {b} {t}", 'Chain Kit', random.choice([850, 980, 1250, 1450, 1650, 1850, 2250]))

    # 8. Clutch Plate (50 items)
    cp_brands = ['FCC', 'Uno Minda', 'Endurance', 'Varroc', 'OEM Genuine', 'Makino']
    cp_types = ['Friction Clutch Plate Set', 'Steel Pressure Plate Set', 'Heavy Duty Cork Friction Plate Kit']
    for m in models:
        if len([i for i in all_items if i['category'] == 'Clutch Plate']) < 50:
            b = random.choice(cp_brands)
            t = random.choice(cp_types)
            add_item(f"{m} {b} {t}", 'Clutch Plate', random.choice([350, 420, 550, 680, 850, 1200]))

    # 9. Clutch Cable (50 items)
    cable_brands = ['Uno Minda', 'Varroc', 'Suprajit', 'Remson', 'OEM Genuine', 'Rane']
    for m in models:
        if len([i for i in all_items if i['category'] == 'Clutch Cable']) < 50:
            b = random.choice(cable_brands)
            add_item(f"{m} Heavy Duty Clutch Cable ({b})", 'Clutch Cable', random.choice([110, 130, 150, 170, 220]))

    # 10. Accelerator Cable (50 items)
    for m in models:
        if len([i for i in all_items if i['category'] == 'Accelerator Cable']) < 50:
            b = random.choice(cable_brands)
            add_item(f"{m} Accelerator Throttle Cable ({b})", 'Accelerator Cable', random.choice([100, 120, 140, 160, 190]))

    # 11. Bulbs (50 items)
    bulb_brands = ['Philips', 'Osram', 'Phoenix', 'Bosch', 'Lumax', 'Fiem', 'Roots']
    bulb_specs = [
        'Halogen 12V 35/35W HS1 Headlight Bulb', '12V 55/60W H4 Headlight Bulb',
        'LED 12V High Beam Matrix Bulb', '12V 10W Amber Indicator Bulb Set (4 Pcs)',
        '12V 21/5W Dual Filament Tail Light Bulb', 'T10 12V LED Position Light Bulb Pair',
        'Blue Vision 12V 35W Xenon Effect Bulb'
    ]
    for b in bulb_brands:
        for s in bulb_specs:
            if len([i for i in all_items if i['category'] == 'Bulbs']) < 50:
                add_item(f"{b} {s}", 'Bulbs', random.choice([40, 85, 120, 150, 220, 350, 480]))

    # 12. Battery (50 items)
    bat_brands = ['Exide Rider', 'Amaron Beta', 'Amaron Pro Rider', 'Tata Green Velocity', 'SF Sonic Mobiker', 'Base Power', 'Dynex']
    bat_specs = ['12V 2.5Ah Kick Start', '12V 4Ah Maintenance Free (XLTZ4)', '12V 5Ah VRLA (Activa/Jupiter)', '12V 7Ah VRLA (Pulsar/FZ)', '12V 9Ah Heavy Duty (Bullet/Pulsar 220)', '12V 14Ah Heavy Duty']
    for b in bat_brands:
        for s in bat_specs:
            if len([i for i in all_items if i['category'] == 'Battery']) < 50:
                add_item(f"{b} {s} Battery", 'Battery', random.choice([880, 1150, 1180, 1350, 1380, 1650, 1950, 2250]))

    # 13. Tyres (50 items)
    tyre_brands = ['MRF Zapper', 'CEAT Gripp X3', 'CEAT Secura Zoom', 'TVS Eurogrip', 'Apollo ActiGrip', 'JK Tyre Blaze', 'Ralco Speed Blaster', 'Michelin City Pro', 'Pirelli Angel City']
    tyre_sizes = [
        '90/90-12 Tubeless Scooter Tyre', '100/90-10 Scooter Tubeless Tyre', '2.75-18 Tube Type Front Tyre',
        '3.00-18 Tube Type Rear Tyre', '80/100-18 Tubeless Front Tyre', '100/90-17 Tubeless Rear Tyre',
        '110/80-17 Tubeless Rear Tyre', '120/80-17 Tubeless Rear Tyre', '130/70-17 Radial Rear Tyre',
        '3.25-19 Heavy Duty Bullet Tyre', '90/90-21 Dual Sport Adventure Tyre'
    ]
    for b in tyre_brands:
        for s in tyre_sizes:
            if len([i for i in all_items if i['category'] == 'Tyres']) < 50:
                add_item(f"{b} {s}", 'Tyres', random.choice([1100, 1180, 1250, 1380, 1450, 1650, 1950, 2250, 2850]))

    # 14. Tubes (50 items)
    tube_brands = ['MRF', 'CEAT', 'TVS Eurogrip', 'Apollo', 'Ralco', 'JK Tyre']
    tube_sizes = ['2.75-18 Heavy Duty Butyl Tube', '3.00-18 Heavy Duty Butyl Tube', '90/90-12 Scooter Butyl Tube', '3.25-19 Heavy Duty Bullet Tube', '2.50-17 Tube', '3.00-17 Heavy Tube']
    for b in tube_brands:
        for s in tube_sizes:
            if len([i for i in all_items if i['category'] == 'Tubes']) < 50:
                add_item(f"{b} {s}", 'Tubes', random.choice([220, 240, 280, 320, 350]))

    # 15. Fuses (50 items)
    fuse_types = ['Micro Blade Fuse 5A (Pack of 10)', 'Micro Blade Fuse 10A (Pack of 10)', 'Micro Blade Fuse 15A (Pack of 10)', 'Micro Blade Fuse 20A (Pack of 10)', 'Glass Tube Fuse 10A (Pack of 10)', 'Maxi Blade Main Fuse 30A', 'Universal Fuse Box Assortment Kit']
    fuse_brands = ['Uno Minda', 'Varroc', 'Bosch', 'Roots', 'Lumax']
    for b in fuse_brands:
        for t in fuse_types:
            if len([i for i in all_items if i['category'] == 'Fuses']) < 50:
                add_item(f"{b} {t}", 'Fuses', random.choice([30, 45, 60, 90, 120]))

    # 16. Horn (50 items)
    horn_brands = ['Roots Windtone', 'Bosch FC4 Chrome', 'Hella Midnight Black', 'Denso Dual Tone', 'Uno Minda Vibrasonic', 'Varroc Megatone', 'Spark Minda Snail']
    for m in models:
        if len([i for i in all_items if i['category'] == 'Horn']) < 50:
            b = random.choice(horn_brands)
            add_item(f"{m} {b} 12V Dual Horn Kit", 'Horn', random.choice([280, 340, 380, 450, 520, 680]))

    # 17. Mirrors (50 items)
    mirror_brands = ['Lumax', 'Fiem', 'Uno Minda', 'Varroc', 'OEM Genuine']
    for m in models:
        if len([i for i in all_items if i['category'] == 'Mirrors']) < 50:
            b = random.choice(mirror_brands)
            add_item(f"{m} Rearview Mirror Pair Left + Right ({b})", 'Mirrors', random.choice([180, 210, 240, 280, 350, 450]))

    # 18. Footrest (50 items)
    for m in models:
        if len([i for i in all_items if i['category'] == 'Footrest']) < 50:
            pos = random.choice(['Front Rider Rubber Footrest Pair', 'Rear Pillion Heavy Footrest Step Pair', 'Ladies Footrest Assembly with Saree Guard'])
            add_item(f"{m} {pos}", 'Footrest', random.choice([120, 150, 180, 220, 280, 380]))

    # 19. Grease & Lubricants (50 items)
    lube_brands = ['Motul', 'Castrol', 'SKF', 'Gulf', 'Shell', 'Servo', 'HP', 'WD-40', '3M', 'Veedol', 'Liqui Moly', 'Wurth']
    lube_types = ['AP3 High Temp Bearing Grease (500g)', 'Wheel Bearing Lithium Grease (1kg)', 'C2 Chain Lube Spray Can (150ml)', 'C2 Chain Lube Spray Can (400ml)', 'C1 Chain Cleaner Spray Can (150ml)', 'WD-40 Anti-Rust Multi Spray (100ml)', 'WD-40 Anti-Rust Multi Spray (420ml)', 'Front Fork Shock Absorber Oil (350ml)', 'Silicon Carburetor Cleaner Spray', 'RTV High Temp Silicone Gasket Sealant']
    for b in lube_brands:
        for t in lube_types:
            if len([i for i in all_items if i['category'] == 'Grease & Lubricants']) < 50:
                add_item(f"{b} {t}", 'Grease & Lubricants', random.choice([110, 140, 180, 220, 280, 350, 450, 650]))

    # 20. Coolant / Brake Oil (50 items)
    cool_brands = ['Motul', 'Castrol', 'Shell', 'Gulf', 'Servo', 'Sunstar', 'Bosch', 'TVS Girling', 'KBX', 'Liqui Moly', 'Waxpol']
    cool_types = ['Long Life Engine Coolant Ready Mix (1L)', 'Radiator Coolant Concentrate (1L)', 'Heavy Duty DOT 3 Brake Fluid (250ml)', 'Heavy Duty DOT 3 Brake Fluid (500ml)', 'Heavy Duty DOT 4 Brake Fluid (250ml)', 'Heavy Duty DOT 4 Brake Fluid (500ml)', 'DOT 5.1 High Performance Racing Brake Fluid']
    for b in cool_brands:
        for t in cool_types:
            if len([i for i in all_items if i['category'] == 'Coolant / Brake Oil']) < 50:
                add_item(f"{b} {t}", 'Coolant / Brake Oil', random.choice([120, 160, 220, 280, 350, 450, 650]))

    # Top up any category if under 50 to guarantee exactly 1000 items!
    for cat in categories:
        current_cat_count = len([i for i in all_items if i['category'] == cat])
        while current_cat_count < 50:
            m = random.choice(models)
            idx = len(all_items) + 1
            add_item(f"{cat} - {m} Genuine Part #{idx}", cat, random.choice([150, 250, 350, 450, 650, 950]))
            current_cat_count += 1

    print(f"Generated exactly {len(all_items)} total items across {len(categories)} categories!")

    # Delete dependent JobParts first to avoid Foreign Key Protection error
    JobPart.objects.all().delete()
    InventoryItem.objects.all().delete()

    # Bulk insert into SQL database
    sql_objects = [InventoryItem(**item) for item in all_items]
    InventoryItem.objects.bulk_create(sql_objects, batch_size=200)

    # Sync to MongoDB collection
    mongo_coll = get_mongo_collection("inventory_items")
    if mongo_coll is not None:
        mongo_coll.delete_many({})
        mongo_coll.insert_many(all_items)

    print("Successfully populated 1000 items into SQL and MongoDB database with stock=6!")

if __name__ == '__main__':
    generate_1000_items()
