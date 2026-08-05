import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.settings_app.models import AdminProfile
from api.mongo_sync import get_mongo_db

def init_master_admin():
    print("Initializing Permanent Master Admin Profile...")
    
    # 1. Create or get Django Superuser
    user, created = User.objects.get_or_create(username='Ravi Patel', defaults={
        'email': 'admin@patelautomobiles.com',
        'first_name': 'Ravi',
        'last_name': 'Patel',
        'is_staff': True,
        'is_superuser': True
    })
    user.set_password('admin123')
    user.save()

    # 2. Create or get AdminProfile
    profile, p_created = AdminProfile.objects.get_or_create(user=user, defaults={
        'user_name': 'ravi manharrai patel',
        'username': 'Ravi Patel',
        'phone': '+91 81403 71414',
        'email': 'admin@patelautomobiles.com',
        'profile_photo': '/logo.png'
    })
    profile.user_name = 'ravi manharrai patel'
    profile.phone = '+91 81403 71414'
    profile.save()

    # 3. Sync directly to MongoDB Atlas
    mongo_db = get_mongo_db()
    if mongo_db is not None:
        col = mongo_db['admin_profiles']
        col.replace_one({'_id': profile.id}, {
            '_id': profile.id,
            'id': str(profile.id),
            'user_name': profile.user_name,
            'username': profile.username,
            'phone': profile.phone,
            'email': profile.email,
            'profile_photo': profile.profile_photo,
            'role': 'ADMIN',
            'created_at': '2026-08-05T00:00:00Z'
        }, upsert=True)
        print("Permanent Master Admin Profile synced to MongoDB Atlas admin_profiles!")

    print("Master Admin Initialization Complete!")

if __name__ == '__main__':
    init_master_admin()
