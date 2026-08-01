import os
import sys

def replace_pincode(root_dir):
    extensions = ('.py', '.jsx', '.js', '.json', '.html', '.md', '.css')
    replaced_files = []

    for root, dirs, files in os.walk(root_dir):
        if 'node_modules' in root or '.git' in root or 'dist' in root or '.system_generated' in root:
            continue
        for file in files:
            if file.endswith(extensions):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    new_content = content
                    new_content = new_content.replace('396385', '396385')

                    if content != new_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        replaced_files.append(filepath)
                        print(f"Updated: {filepath}")
                except Exception as e:
                    print(f"Skipped {filepath}: {e}")

    print(f"\nTotal files updated: {len(replaced_files)}")

def update_database_pincode():
    print("\nUpdating pincode in Django & MongoDB database...")
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()

    from apps.settings_app.models import GarageSettings
    from config.mongodb import get_mongo_collection

    settings_obj = GarageSettings.objects.first()
    if settings_obj:
        if '396385' in settings_obj.address:
            settings_obj.address = settings_obj.address.replace('396385', '396385')
        elif '396385' not in settings_obj.address:
            settings_obj.address = "Near Dandi Pond, Dandi, Valsad, Gujarat - 396385"
        settings_obj.save()
        print("Updated SQLite GarageSettings pincode to 396385!")

    mongo_coll = get_mongo_collection("garage_settings")
    if mongo_coll is not None:
        mongo_coll.update_many({}, {"$set": {"address": "Near Dandi Pond, Dandi, Valsad, Gujarat - 396385"}})
        print("Updated MongoDB garage_settings address to 396385!")

if __name__ == '__main__':
    root = os.path.dirname(os.path.abspath(__file__))
    replace_pincode(root)
    update_database_pincode()
