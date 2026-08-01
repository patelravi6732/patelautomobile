import os
import pymongo
from pymongo import MongoClient

MONGO_URI = os.getenv(
    "MONGO_URI", 
    "mongodb+srv://rockpatel6732_db_user:FYwO0vlU8Vehe3DM@cluster0.zh8vtin.mongodb.net/patel_automobiles_db?retryWrites=true&w=majority&appName=Cluster0"
)

client = None
db = None

def get_mongo_db():
    global client, db
    if db is not None:
        return db
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client["patel_automobiles_db"]
        return db
    except Exception as e:
        print("MongoDB Atlas Connection Error:", e)
        return None

def sync_model_instance(model_name, instance_id, data_dict):
    try:
        mongo_db = get_mongo_db()
        if mongo_db is None:
            return
        collection = mongo_db[model_name]
        data_dict["_id"] = instance_id
        collection.replace_one({"_id": instance_id}, data_dict, upsert=True)
    except Exception as e:
        print(f"Error syncing {model_name} #{instance_id} to MongoDB Atlas:", e)

def delete_mongo_instance(model_name, instance_id):
    try:
        mongo_db = get_mongo_db()
        if mongo_db is None:
            return
        collection = mongo_db[model_name]
        collection.delete_one({"_id": instance_id})
    except Exception as e:
        print(f"Error deleting {model_name} #{instance_id} from MongoDB Atlas:", e)

def sync_all_database_to_mongo():
    try:
        from apps.settings_app.models import GarageSettings, AdminProfile, AdminAuditLog, RecycleBinItem
        from apps.bookings.models import Booking
        from apps.workshop.models import ServiceJob, JobPart
        from apps.inventory.models import InventoryItem
        from apps.customers.models import Customer
        from apps.billing.models import Invoice
        from apps.attendance.models import Attendance, MechanicSalaryPayment

        mongo_db = get_mongo_db()
        if mongo_db is None:
            print("MongoDB Atlas not connected.")
            return False

        # 1. Garage Settings
        for obj in GarageSettings.objects.all():
            mongo_db["garage_settings"].replace_one({"_id": obj.id}, {
                "_id": obj.id,
                "garage_name": obj.garage_name,
                "logo": obj.logo,
                "address": obj.address,
                "phone": obj.phone,
                "whatsapp_number": obj.whatsapp_number,
                "email": obj.email,
                "timing_text": obj.timing_text,
                "mechanics_list": obj.mechanics_list,
                "default_labour_charge": float(obj.default_labour_charge),
                "default_min_stock": obj.default_min_stock
            }, upsert=True)

        # 2. Admin Profiles
        for obj in AdminProfile.objects.all():
            mongo_db["admin_profiles"].replace_one({"_id": obj.id}, {
                "_id": obj.id,
                "user_name": obj.user_name,
                "username": obj.username,
                "phone": obj.phone,
                "email": obj.email,
                "profile_photo": obj.profile_photo,
                "date_of_birth": str(obj.date_of_birth) if obj.date_of_birth else None
            }, upsert=True)

        # 3. Bookings
        for obj in Booking.objects.all():
            mongo_db["bookings"].replace_one({"_id": obj.id}, {
                "_id": obj.id,
                "customer_name": obj.customer_name,
                "mobile": obj.mobile,
                "vehicle_number": obj.vehicle_number,
                "vehicle_model": obj.vehicle_model,
                "service_type": obj.service_type,
                "booking_date": str(obj.booking_date),
                "notes": obj.notes,
                "status": obj.status
            }, upsert=True)

        # 4. Service Jobs
        for obj in ServiceJob.objects.all():
            mongo_db["service_jobs"].replace_one({"_id": obj.id}, {
                "_id": obj.id,
                "job_card_number": obj.job_card_number,
                "customer_name": obj.customer_name,
                "customer_mobile": obj.customer_mobile,
                "vehicle_number": obj.vehicle_number,
                "vehicle_model": obj.vehicle_model,
                "assigned_mechanic": obj.assigned_mechanic,
                "status": obj.status,
                "labour_charge": float(obj.labour_charge),
                "created_at": str(obj.created_at)
            }, upsert=True)

        # 5. Inventory
        for obj in InventoryItem.objects.all():
            mongo_db["inventory_items"].replace_one({"_id": obj.id}, {
                "_id": obj.id,
                "part_name": obj.part_name,
                "category": obj.category,
                "price": float(obj.price),
                "current_stock": obj.current_stock,
                "min_stock_alert": obj.min_stock_alert
            }, upsert=True)

        # 6. Customers
        for obj in Customer.objects.all():
            mongo_db["customers"].replace_one({"_id": obj.id}, {
                "_id": obj.id,
                "full_name": obj.full_name,
                "mobile": obj.mobile,
                "vehicle_numbers": obj.vehicle_numbers,
                "outstanding_balance": float(obj.outstanding_balance)
            }, upsert=True)

        # 7. Invoices
        for obj in Invoice.objects.all():
            mongo_db["invoices"].replace_one({"_id": obj.id}, {
                "_id": obj.id,
                "invoice_number": obj.invoice_number,
                "customer_name": obj.customer_name,
                "grand_total": float(obj.grand_total),
                "payment_status": obj.payment_status,
                "created_at": str(obj.created_at)
            }, upsert=True)

        # 8. Attendance
        for obj in Attendance.objects.all():
            mongo_db["attendance"].replace_one({"_id": obj.id}, {
                "_id": obj.id,
                "mechanic_name": obj.mechanic_name,
                "date": str(obj.date),
                "check_in": str(obj.check_in) if obj.check_in else None,
                "check_out": str(obj.check_out) if obj.check_out else None,
                "status": obj.status
            }, upsert=True)

        # 9. Salary Payments
        for obj in MechanicSalaryPayment.objects.all():
            mongo_db["salary_payments"].replace_one({"_id": obj.id}, {
                "_id": obj.id,
                "mechanic_name": obj.mechanic_name,
                "amount": float(obj.amount),
                "payment_type": obj.payment_type,
                "payment_date": str(obj.payment_date),
                "notes": obj.notes,
                "created_at": str(obj.created_at)
            }, upsert=True)

        # 10. Audit Logs
        for obj in AdminAuditLog.objects.all():
            mongo_db["audit_logs"].replace_one({"_id": obj.id}, {
                "_id": obj.id,
                "admin_name": obj.admin_name,
                "action_type": obj.action_type,
                "description": obj.description,
                "timestamp": str(obj.timestamp)
            }, upsert=True)

        print("Full Database Sync to MongoDB Atlas completed successfully!")
        return True
    except Exception as e:
        print("Error during full MongoDB Atlas sync:", e)
        return False
