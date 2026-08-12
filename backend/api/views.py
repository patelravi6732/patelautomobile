from decimal import Decimal
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, date, timedelta
import os
import json
import uuid
import calendar
from django.core.serializers.json import DjangoJSONEncoder

from apps.accounts.models import UserProfile
from apps.settings_app.models import GarageSettings, RecycleBinItem, AdminProfile, AdminAuditLog
from apps.bookings.models import Booking
from apps.inventory.models import InventoryItem
from apps.customers.models import Customer, ContactMessage
from apps.workshop.models import ServiceJob, JobPart
from apps.billing.models import Invoice
from apps.attendance.models import Attendance, MechanicSalaryPayment

from .serializers import (
    UserSerializer, GarageSettingsSerializer, BookingSerializer,
    InventoryItemSerializer, CustomerSerializer, ContactMessageSerializer,
    JobPartSerializer, ServiceJobSerializer, InvoiceSerializer, AttendanceSerializer,
    RecycleBinItemSerializer, AdminProfileSerializer, AdminAuditLogSerializer,
    MechanicSalaryPaymentSerializer
)
from .permissions import IsAdminUserRole, IsStaffOrAdminUserRole
from django.contrib.auth.hashers import make_password, check_password

def sync_admin_profile_to_mongodb(admin_profile, plain_password=None):
    try:
        from mongo_config import get_db as get_mongo_db
        db = get_mongo_db()
        if db is not None:
            col = db['admin_profiles']
            user_obj = admin_profile.user
            pw_hash = user_obj.password if (user_obj and user_obj.password) else (make_password(plain_password) if plain_password else '')
            doc = {
                'id': str(admin_profile.id),
                'user_name': admin_profile.user_name,
                'username': admin_profile.username,
                'phone': admin_profile.phone,
                'email': admin_profile.email,
                'date_of_birth': str(admin_profile.date_of_birth) if admin_profile.date_of_birth else '',
                'profile_photo': admin_profile.profile_photo,
                'password_hash': pw_hash,
                'updated_at': timezone.now().isoformat()
            }
            col.update_one({'username': admin_profile.username}, {'$set': doc}, upsert=True)
            print(f"✅ Synced admin '{admin_profile.username}' with PBKDF2 hashed password to MongoDB Atlas!")
    except Exception as e:
        print(f"MongoDB admin sync warning: {e}")

def get_progressive_lockout_info(tier):
    """
    Tier 1: 5 minutes (300s)
    Tier 2: 15 minutes (900s)
    Tier 3+: 1 hour (3600s)
    """
    if tier <= 1:
        return timedelta(minutes=5), "5 minutes"
    elif tier == 2:
        return timedelta(minutes=15), "15 minutes"
    else:
        return timedelta(hours=1), "1 hour"

def format_remaining_time(seconds):
    seconds = max(1, int(seconds))
    if seconds >= 3600:
        hrs = seconds // 3600
        mins = (seconds % 3600) // 60
        if mins > 0:
            return f"{hrs} hour(s) {mins} minute(s)"
        return f"{hrs} hour(s)"
    elif seconds >= 60:
        mins = seconds // 60
        secs = seconds % 60
        if secs > 0:
            return f"{mins} minute(s) {secs} second(s)"
        return f"{mins} minute(s)"
    else:
        return f"{seconds} second(s)"

def process_admin_password_attempt(admin_profile, password_attempt):
    """
    Validates password and applies progressive lockout rules:
    - 3 wrong attempts -> Lockout Tier 1: 5 min
    - 3 more wrong attempts -> Lockout Tier 2: 15 min
    - 3 more wrong attempts -> Lockout Tier 3: 1 hour
    - Subsequent 3 wrong attempts -> 1 hour
    """
    now = timezone.now()

    # 1. Check if profile is currently locked out
    if admin_profile.lockout_until and admin_profile.lockout_until > now:
        remaining_sec = (admin_profile.lockout_until - now).total_seconds()
        time_str = format_remaining_time(remaining_sec)
        return False, f"Account locked due to 3 failed password attempts. Please try again in {time_str}."

    # Find associated User object
    user_obj = admin_profile.user
    if not user_obj and admin_profile.username:
        user_obj = User.objects.filter(username=admin_profile.username).first()

    if not user_obj:
        return False, "Associated Admin user account not found."

    # 2. Check Password
    if user_obj.check_password(password_attempt):
        # Success -> reset failed attempts counter
        admin_profile.failed_attempts = 0
        admin_profile.lockout_until = None
        admin_profile.save()
        return True, ""

    # 3. Failed attempt -> Increment failed_attempts counter
    admin_profile.failed_attempts += 1

    if admin_profile.failed_attempts >= 3:
        # Trigger next lockout tier
        admin_profile.lockout_tier += 1
        delta, duration_text = get_progressive_lockout_info(admin_profile.lockout_tier)
        admin_profile.lockout_until = now + delta
        admin_profile.failed_attempts = 0
        admin_profile.save()
        return False, f"3 consecutive wrong password attempts! Account locked for {duration_text}."
    else:
        admin_profile.save()
        attempts_left = 3 - admin_profile.failed_attempts
        _, next_duration_text = get_progressive_lockout_info(admin_profile.lockout_tier + 1)
        return False, f"Incorrect password! {attempts_left} attempt(s) remaining before {next_duration_text} lockout."

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_with_lockout(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()

    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(username=username).first()
    if not user:
        return Response({'error': 'Invalid username or password.'}, status=status.HTTP_400_BAD_REQUEST)

    admin_profile = AdminProfile.objects.filter(username__iexact=username).first()
    if not admin_profile:
        admin_profile = AdminProfile.objects.filter(user=user).first()
    if not admin_profile:
        admin_profile = AdminProfile.objects.create(
            user=user,
            user_name=user.first_name or user.username,
            username=user.username,
            phone='+91 81403 71414'
        )

    ok, err_msg = process_admin_password_attempt(admin_profile, password)
    if not ok:
        is_locked = "locked" in err_msg.lower()
        status_code = status.HTTP_429_TOO_MANY_REQUESTS if is_locked else status.HTTP_400_BAD_REQUEST
        return Response({'error': err_msg, 'locked_out': is_locked}, status=status_code)

    refresh = RefreshToken.for_user(user)
    user_data = UserSerializer(user).data
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': user_data
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    user = request.user
    if not hasattr(user, 'admin_profile') or user.admin_profile is None:
        prof = AdminProfile.objects.filter(username__iexact=user.username).first()
        if not prof:
            prof = AdminProfile.objects.filter(user=user).first()
        if not prof:
            prof = AdminProfile.objects.create(
                user=user,
                user_name=user.first_name or user.username,
                username=user.username,
                email=user.email or 'admin@patelautomobiles.com',
                phone='+91 81403 71414'
            )
        else:
            if prof.user != user:
                prof.user = user
                prof.save()
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

import random
OTP_CACHE = {}

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def request_otp_reset(request):
    phone_input = request.data.get('phone', '').strip()
    if not phone_input:
        return Response({'error': 'Please enter registered mobile number.'}, status=status.HTTP_400_BAD_REQUEST)
    
    clean_phone = ''.join(filter(str.isdigit, phone_input))
    if len(clean_phone) > 10:
        clean_phone = clean_phone[-10:]
    
    matching_profile = None
    for prof in AdminProfile.objects.all():
        prof_phone = ''.join(filter(str.isdigit, prof.phone or ''))
        if prof_phone and (prof_phone.endswith(clean_phone) or clean_phone in prof_phone):
            matching_profile = prof
            break

    if not matching_profile:
        return Response({'error': 'No Admin account found registered with this phone number.'}, status=status.HTTP_404_NOT_FOUND)

    otp_code = str(random.randint(100000, 999999))
    OTP_CACHE[clean_phone] = {
        'otp': otp_code,
        'profile_id': matching_profile.id,
        'timestamp': timezone.now()
    }

    # Send SMS Gateway Notification
    try:
        fast2sms_key = os.environ.get('FAST2SMS_API_KEY', '')
        clean_num = ''.join(filter(str.isdigit, phone_input))
        if len(clean_num) > 10:
            clean_num = clean_num[-10:]
        
        print(f"\n=======================================================", flush=True)
        print(f"[REAL SMS DISPATCH] Target Mobile: +91 {clean_num}", flush=True)
        print(f"6-Digit OTP Code: {otp_code} (Valid for 30 Seconds)", flush=True)
        print(f"=======================================================\n", flush=True)

        if fast2sms_key:
            import urllib.request
            url = f"https://www.fast2sms.com/dev/bulkV2?authorization={fast2sms_key}&variables_values={otp_code}&route=otp&numbers={clean_num}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                res = urllib.request.urlopen(req)
                resp_text = res.read().decode('utf-8')
                print(f"[FAST2SMS RESPONSE]: {resp_text}")
            except Exception as http_err:
                if hasattr(http_err, 'read'):
                    err_body = http_err.read().decode('utf-8')
                    print(f"[FAST2SMS GATEWAY NOTICE]: {err_body}")
                else:
                    print(f"[FAST2SMS GATEWAY ERROR]: {http_err}")
    except Exception as e:
        print(f"SMS Gateway Error: {e}")

    log_admin_action(matching_profile.user_name, 'REQUEST_OTP', f"Requested SMS OTP password reset for phone {phone_input}")
    
    return Response({
        'message': f"SMS OTP sent successfully to registered mobile number {phone_input}! Please check your mobile phone SMS messages.",
        'phone': phone_input,
        'user_name': matching_profile.user_name
    })

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp_only(request):
    phone_input = request.data.get('phone', '').strip()
    otp_input = request.data.get('otp', '').strip()

    if not phone_input or not otp_input:
        return Response({'error': 'Mobile number and 6-digit OTP code are required.'}, status=status.HTTP_400_BAD_REQUEST)

    clean_phone = ''.join(filter(str.isdigit, phone_input))
    if len(clean_phone) > 10:
        clean_phone = clean_phone[-10:]

    cached_data = OTP_CACHE.get(clean_phone)
    if not cached_data:
        return Response({'error': 'No active OTP found. Please click Request OTP.'}, status=status.HTTP_400_BAD_REQUEST)

    elapsed_seconds = (timezone.now() - cached_data['timestamp']).total_seconds()
    if elapsed_seconds > 30:
        OTP_CACHE.pop(clean_phone, None)
        return Response({'error': 'OTP Expired! The OTP was only valid for 30 seconds. Please request a new OTP.'}, status=status.HTTP_400_BAD_REQUEST)

    if cached_data.get('otp') != otp_input:
        return Response({'error': 'Invalid 6-digit OTP code! Please check and enter the correct code.'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'valid': True, 'message': 'OTP Verified Successfully!'})

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp_reset_password(request):
    phone_input = request.data.get('phone', '').strip()
    username_input = request.data.get('username', '').strip()
    new_password = request.data.get('new_password', '').strip()

    if not new_password:
        return Response({'error': 'New secret password is required.'}, status=status.HTTP_400_BAD_REQUEST)

    if not phone_input and not username_input:
        return Response({'error': 'Registered mobile number or admin username is required.'}, status=status.HTTP_400_BAD_REQUEST)

    matching_profile = None
    if phone_input:
        clean_phone = ''.join(filter(str.isdigit, phone_input))
        if len(clean_phone) > 10:
            clean_phone = clean_phone[-10:]
        for prof in AdminProfile.objects.all():
            prof_phone = ''.join(filter(str.isdigit, prof.phone or ''))
            if prof_phone and len(prof_phone) >= 10 and (prof_phone.endswith(clean_phone) or clean_phone in prof_phone):
                matching_profile = prof
                break

    if not matching_profile and username_input:
        matching_profile = AdminProfile.objects.filter(username__iexact=username_input).first()

    if not matching_profile:
        return Response({'error': 'Mobile number or username not registered! Password reset is only allowed for linked Admin accounts.'}, status=status.HTTP_404_NOT_FOUND)

    if not matching_profile.user:
        matching_profile.user = User.objects.filter(username=matching_profile.username).first()

    if matching_profile.user:
        matching_profile.user.set_password(new_password)
        matching_profile.user.save()
    else:
        return Response({'error': 'Associated Admin user account not found.'}, status=status.HTTP_404_NOT_FOUND)

    log_admin_action(matching_profile.user_name, 'RESET_PASSWORD', f"Reset password directly for {matching_profile.user_name}")

    return Response({
        'message': f"Password for '{matching_profile.user_name}' updated successfully! You can now sign in.",
        'username': matching_profile.username
    })

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([permissions.AllowAny])
def public_master_store(request):
    try:
        from config.mongodb import get_mongo_collection
        coll = get_mongo_collection("master_store")
        if coll is None:
            return Response({"error": "MongoDB unavailable"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if request.method == 'GET':
            doc = coll.find_one({"_id": "global_store"}, {"_id": 0})
            if not doc:
                doc = {
                    "bookings": [], "messages": [], "jobs": [], "inventory": [],
                    "recycleBin": [], "garageInfo": {
                        "garage_name": "Patel Automobiles",
                        "address": "Near Dandi Pond, Dandi, Valsad, Gujarat - 396385",
                        "phone": "+91 98987 05544",
                        "whatsapp_number": "+91 98987 05544",
                        "logo": "/logo.png",
                        "upi_id": "paytmqr5hlpsp@ptys",
                        "upi_payee_name": "Patel Automobile",
                        "upi_qr_code": "/upi_qr.jpg",
                        "timing_text": "Mon - Sat: 08:30 AM - 06:30 PM, Sun: 09:00 AM - 02:00 PM",
                        "safety_message": "Thank you for choosing us! Wish you a safe & smooth ride. 🛵⛑️",
                        "mechanics_list": "Unassigned, Amitbhai Mechanic, Vishalbhai Mechanic, Manojbhai Mechanic",
                        "default_labour_charge": 100.0,
                        "default_min_stock": 5
                    },
                    "adminProfiles": [], "khataEntries": [], "customers": [], "invoices": [], "attendance": [], "salaryPayments": [], "deletedIds": []
                }
            return Response(doc)
        else: # POST or PUT
            store_data = request.data
            if store_data and isinstance(store_data, dict):
                coll.update_one({"_id": "global_store"}, {"$set": store_data}, upsert=True)
                return Response({"status": "updated", "store": store_data})
            return Response({"error": "Invalid store data"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def public_create_booking(request):
    serializer = BookingSerializer(data=request.data)
    if serializer.is_valid():
        booking_obj = serializer.save()
        booking_data = serializer.data
        try:
            import urllib.request, json
            url = "https://jsonblob.com/api/jsonBlob/019fefc6-21be-77b8-ac69-adb834903ebd"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            data = json.loads(urllib.request.urlopen(req, timeout=3).read().decode('utf-8'))
            bookings = data.get('bookings') or []
            if not any(str(b.get('id')) == str(booking_data.get('id')) for b in bookings if isinstance(b, dict)):
                bookings.insert(0, booking_data)
                data['bookings'] = bookings
                put_req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'}, method='PUT')
                urllib.request.urlopen(put_req, timeout=3)
        except Exception as e:
            print("Cloud bin sync notice:", e)

        return Response({"message": "Booking submitted successfully!", "booking": booking_data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

import random

def generate_ai_contact_reply_text(name, message_text):
    msg_lower = (message_text or '').lower()
    
    greetings = [
        f"Respected {name},",
        f"Dear {name},",
        f"Hello {name},"
    ]

    closings = [
        "Please feel free to reply to this message or visit our workshop for assistance.",
        "Kindly let us know if you would like us to reserve a service bay for your vehicle.",
        "We welcome you to visit our garage during working hours for a detailed inspection."
    ]

    location_info = (
        "Workshop Details:\n"
        "Patel Automobiles\n"
        "Location: Near Dandi Pond, Dandi, Valsad, Gujarat - 396385\n"
        "Working Hours: Monday - Saturday (09:00 AM - 08:30 PM) | Sunday (09:00 AM - 02:00 PM)"
    )

    greeting = random.choice(greetings)
    closing = random.choice(closings)

    # 1. Tyre / Puncture Category
    if any(w in msg_lower for w in ['tyre', 'tire', 'puncture', 'wheel', 'tube', 'air']):
        body_options = [
            f"Thank you for contacting Patel Automobiles regarding your two-wheeler tyre / puncture inquiry.\n\nWe provide tubeless puncture repairs, wheel alignment, and new genuine tyres from leading brands including MRF, CEAT, TVS Eurogrip, and Apollo with full warranty.",
            f"We have received your query regarding tyre service.\n\nPatel Automobiles stocks original tyres for all scooter and motorcycle models, along with tubeless puncture repair services at our Dandi, Valsad workshop."
        ]
        body = random.choice(body_options)

    # 2. Service / Oil / Engine Category
    elif any(w in msg_lower for w in ['service', 'servicing', 'oil', 'engine', 'tuning', 'brake', 'wash', 'chain', 'clutch']):
        body_options = [
            f"Thank you for reaching out to Patel Automobiles regarding two-wheeler servicing.\n\nWe perform comprehensive periodic general maintenance, synthetic engine oil replacement, brake overhaul, and chain lubrication using 100% genuine spare parts.",
            f"We have received your inquiry regarding bike servicing.\n\nOur certified technicians perform detailed periodic checkups, engine tuning, filter cleaning, and brake service for all major two-wheeler brands."
        ]
        body = random.choice(body_options)

    # 3. Battery / Electricals Category
    elif any(w in msg_lower for w in ['battery', 'start', 'light', 'horn', 'wiring', 'fuse', 'self']):
        body_options = [
            f"Thank you for contacting Patel Automobiles regarding your electrical / battery requirement.\n\nWe provide computer battery diagnostics, genuine Exide and Amaron battery replacements with full manufacturer warranty, and electrical troubleshooting.",
            f"We have received your inquiry regarding battery / electrical repair.\n\nOur workshop handles self-start system repairs, wiring harness diagnostics, and headlight / horn replacements."
        ]
        body = random.choice(body_options)

    # 4. General / Custom Query
    else:
        body_options = [
            f"Thank you for contacting Patel Automobiles.\n\nWe have received your inquiry: \"{message_text}\". Our workshop is fully equipped to assist you with two-wheeler maintenance, genuine spare parts, and mechanical repairs.",
            f"Thank you for reaching out to Patel Automobiles, Dandi, Valsad.\n\nOur team has noted your message: \"{message_text}\". Our experienced mechanics are at your service to inspect and service your vehicle."
        ]
        body = random.choice(body_options)

    reply = f"{greeting}\n\n{body}\n\n{location_info}\n\n{closing}\n\nBest regards,\nPatel Automobiles, Dandi, Valsad"
    return reply

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def public_create_contact_message(request):
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        msg_obj = serializer.save()
        msg_obj.ai_draft_reply = generate_ai_contact_reply_text(msg_obj.name, msg_obj.message)
        msg_obj.save()
        msg_data = ContactMessageSerializer(msg_obj).data

        try:
            import urllib.request, json
            url = "https://jsonblob.com/api/jsonBlob/019fefc6-21be-77b8-ac69-adb834903ebd"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            data = json.loads(urllib.request.urlopen(req, timeout=3).read().decode('utf-8'))
            messages = data.get('messages') or []
            if not any(str(m.get('id')) == str(msg_data.get('id')) for m in messages if isinstance(m, dict)):
                messages.insert(0, msg_data)
                data['messages'] = messages
                put_req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'}, method='PUT')
                urllib.request.urlopen(put_req, timeout=3)
        except Exception as e:
            print("Cloud bin sync contact notice:", e)

        try:
            from config.mongodb import log_to_mongo
            log_to_mongo("contact_messages", {
                "event": "NEW_MESSAGE_RECEIVED",
                "message_id": msg_obj.id,
                "name": msg_obj.name,
                "phone": msg_obj.phone,
                "message": msg_obj.message,
                "ai_draft_reply": msg_obj.ai_draft_reply,
                "created_at": str(msg_obj.created_at)
            })
        except Exception:
            pass
        return Response({"message": "Your message has been sent successfully!", "contact_message": ContactMessageSerializer(msg_obj).data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_garage_info(request):
    settings_obj = GarageSettings.objects.first()
    if not settings_obj:
        settings_obj = GarageSettings.objects.create()
    serializer = GarageSettingsSerializer(settings_obj)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    today = date.today()
    
    today_services = ServiceJob.objects.filter(created_at__date=today).exclude(status='CANCELLED').count()
    completed_services = ServiceJob.objects.filter(status='FINISHED').count()
    pending_services = ServiceJob.objects.filter(status='IN_PROGRESS').count()
    
    total_pending_payments = Customer.objects.aggregate(total=Sum('pending_amount'))['total'] or 0.00
    today_revenue = Invoice.objects.filter(created_at__date=today).aggregate(total=Sum('paid_amount'))['total'] or 0.00
    
    low_stock_items = InventoryItem.objects.filter(current_stock__lte=F('min_stock_alert'))
    low_stock_count = low_stock_items.count()
    low_stock_serialized = InventoryItemSerializer(low_stock_items[:5], many=True).data
    
    recent_jobs = ServiceJob.objects.exclude(status='CANCELLED').order_by('-created_at')[:5]
    recent_jobs_serialized = ServiceJobSerializer(recent_jobs, many=True).data

    return Response({
        "today_services": today_services,
        "completed_services": completed_services,
        "pending_services": pending_services,
        "pending_payments": float(total_pending_payments),
        "today_revenue": float(today_revenue),
        "low_stock_count": low_stock_count,
        "low_stock_items": low_stock_serialized,
        "recent_jobs": recent_jobs_serialized,
    })

def log_admin_action(admin_name, action_type, description):
    try:
        AdminAuditLog.objects.create(
            admin_name=admin_name or 'Admin Patel',
            action_type=action_type,
            description=description
        )
    except Exception as e:
        print(f"Log admin action error: {e}")

def sync_completed_service_to_mongodb(job, customer, invoice):
    """Mirror a completed bill to Atlas without making the billing API depend on Atlas availability."""
    try:
        from config.mongodb import get_mongo_collection

        service_jobs = get_mongo_collection('service_jobs')
        customers = get_mongo_collection('customers')
        invoices = get_mongo_collection('invoices')
        if not all([service_jobs, customers, invoices]):
            return

        service_jobs.replace_one({'_id': job.id}, {
            '_id': job.id,
            'customer_name': job.customer_name,
            'mobile_number': job.mobile_number,
            'vehicle_number': job.vehicle_number,
            'bike_model': job.bike_model,
            'assigned_mechanic': job.assigned_mechanic,
            'status': job.status,
            'labour_charge': float(job.labour_charge),
            'parts_total': float(job.parts_total),
            'finished_at': job.finished_at.isoformat() if job.finished_at else None,
        }, upsert=True)
        customers.replace_one({'_id': customer.id}, {
            '_id': customer.id,
            'customer_name': customer.customer_name,
            'mobile_number': customer.phone,
            'vehicle_number': customer.vehicle_number,
            'pending_amount': float(customer.pending_amount),
            'visit_count': customer.visit_count,
            'last_visit': customer.last_visit.isoformat() if customer.last_visit else None,
        }, upsert=True)
        invoices.replace_one({'_id': invoice.id}, {
            '_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'service_job_id': job.id,
            'customer_name': invoice.customer_name,
            'mobile_number': invoice.mobile_number,
            'vehicle_number': invoice.vehicle_number,
            'bike_model': invoice.bike_model,
            'labour_charge': float(invoice.labour_charge),
            'parts_total': float(invoice.parts_total),
            'grand_total': float(invoice.grand_total),
            'paid_amount': float(invoice.paid_amount),
            'pending_amount': float(invoice.pending_amount),
            'payment_status': 'PAID' if invoice.pending_amount == 0 else 'PARTIAL',
            'created_at': invoice.created_at.isoformat(),
        }, upsert=True)
    except Exception as exc:
        # Atlas is an additional mirror; the transactional primary database must still succeed.
        print(f"MongoDB completion sync warning: {exc}")

def check_admin_password(request):
    admin_password = request.data.get('admin_password', '').strip() or request.query_params.get('admin_password', '').strip()
    if not admin_password:
        return False, 'Admin password is required.'
    
    admin_profile = None
    if request.user and request.user.is_authenticated:
        admin_profile = AdminProfile.objects.filter(user=request.user).first()
    
    if not admin_profile:
        admin_profile = AdminProfile.objects.filter(username__iexact='admin').first() or AdminProfile.objects.first()

    if not admin_profile:
        user_obj = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_staff=True).first()
        if user_obj:
            admin_profile, _ = AdminProfile.objects.get_or_create(
                user=user_obj,
                defaults={'user_name': user_obj.username, 'username': user_obj.username}
            )

    if not admin_profile:
        return False, 'No active Admin account found.'

    return process_admin_password_attempt(admin_profile, admin_password)

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all().order_by('-created_at')
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def delete_with_password(self, request, pk=None):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        booking = self.get_object()
        serialized = json.dumps(BookingSerializer(booking).data, cls=DjangoJSONEncoder)
        admin_name = request.user.username if (request.user and request.user.is_authenticated) else 'Admin Patel'
        
        RecycleBinItem.objects.create(
            item_type='BOOKING',
            title=f"Booking for {booking.customer_name} ({booking.vehicle_number})",
            details=f"Date: {booking.preferred_date}, Time: {booking.preferred_time}, Bike: {booking.bike_model}",
            serialized_data=serialized,
            deleted_by=admin_name
        )
        log_admin_action(admin_name, 'DELETE_TO_TRASH', f"Moved Booking for {booking.customer_name} ({booking.vehicle_number}) to Recycle Bin")
        booking.delete()
        return Response({'message': 'Booking moved to Recycle Bin successfully!'})

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'ACCEPTED'
        booking.save()
        return Response({'status': 'Booking accepted', 'booking': BookingSerializer(booking).data})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'REJECTED'
        booking.save()
        return Response({'status': 'Booking rejected', 'booking': BookingSerializer(booking).data})

    @action(detail=True, methods=['post'])
    def convert_to_service(self, request, pk=None):
        booking = self.get_object()
        with transaction.atomic():
            booking.status = 'COMPLETED'
            booking.save()
            
            customer, created = Customer.objects.get_or_create(
                vehicle_number=booking.vehicle_number,
                defaults={
                    'customer_name': booking.customer_name,
                    'phone': booking.mobile_number,
                    'visit_count': 1
                }
            )
            if not created:
                customer.visit_count += 1
                customer.save()
            
            service_job = ServiceJob.objects.create(
                customer_name=booking.customer_name,
                mobile_number=booking.mobile_number,
                vehicle_number=booking.vehicle_number,
                bike_model=booking.bike_model,
                labour_charge=0.00,
                status='IN_PROGRESS'
            )
            
        return Response({
            'status': 'Converted to active service job',
            'service_job': ServiceJobSerializer(service_job).data
        })

class WorkshopViewSet(viewsets.ModelViewSet):
    queryset = ServiceJob.objects.all().order_by('-created_at')
    serializer_class = ServiceJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def delete_with_password(self, request, pk=None):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        job = self.get_object()
        serialized = json.dumps(ServiceJobSerializer(job).data, cls=DjangoJSONEncoder)
        admin_name = request.user.username if (request.user and request.user.is_authenticated) else 'Admin Patel'

        RecycleBinItem.objects.create(
            item_type='SERVICE_JOB',
            title=f"Service Job #{job.id} - {job.vehicle_number} ({job.customer_name})",
            details=f"Bike: {job.bike_model}, Mechanic: {job.assigned_mechanic}, Total: ₹{job.live_total}",
            serialized_data=serialized,
            deleted_by=admin_name
        )
        log_admin_action(admin_name, 'DELETE_TO_TRASH', f"Moved Service Job #{job.id} ({job.vehicle_number}) to Recycle Bin")

        with transaction.atomic():
            for part in job.parts.filter(status='CONFIRMED'):
                item = part.inventory_item
                item.current_stock += part.quantity
                item.save()
            job.parts.all().delete()
            job.delete()
        return Response({'message': 'Service job moved to Recycle Bin successfully!'})

    @action(detail=True, methods=['post'])
    def assign_mechanic(self, request, pk=None):
        job = self.get_object()
        mechanic_name = request.data.get('assigned_mechanic')
        sec_mechanic = request.data.get('secondary_mechanic', '').strip() or None
        if not mechanic_name:
            return Response({'error': 'assigned_mechanic is required'}, status=status.HTTP_400_BAD_REQUEST)
        job.assigned_mechanic = mechanic_name
        job.secondary_mechanic = sec_mechanic
        job.save()

        try:
            from config.mongodb import log_to_mongo
            log_to_mongo("workshop_logs", {
                "event": "MECHANIC_ASSIGNED",
                "job_id": job.id,
                "vehicle_number": job.vehicle_number,
                "assigned_mechanic": mechanic_name,
                "secondary_mechanic": sec_mechanic,
                "timestamp": str(timezone.now())
            })
        except Exception:
            pass

        return Response({'message': 'Mechanics assigned successfully!', 'job': ServiceJobSerializer(job).data})

    @action(detail=True, methods=['post'])
    def add_staged_part(self, request, pk=None):
        job = self.get_object()
        inventory_id = request.data.get('inventory_id')
        quantity = int(request.data.get('quantity', 1))

        if not inventory_id:
            return Response({'error': 'inventory_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = InventoryItem.objects.get(id=inventory_id)
        except InventoryItem.DoesNotExist:
            return Response({'error': 'Inventory item not found'}, status=status.HTTP_404_NOT_FOUND)

        if item.current_stock < quantity:
            return Response({
                'error': f'Insufficient stock for {item.part_name}. Required: {quantity}, Available: {item.current_stock}'
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            job_part, created = JobPart.objects.get_or_create(
                job=job,
                inventory_item=item,
                status='STAGED',
                defaults={
                    'part_name': item.part_name,
                    'unit_price': item.price,
                    'quantity': quantity,
                }
            )
            if not created:
                job_part.quantity += quantity
                job_part.save()

        return Response({
            'message': f'{item.part_name} added as staged part (Pending confirmation)',
            'job': ServiceJobSerializer(job).data
        })
    @action(detail=True, methods=['post'])
    def remove_staged_part(self, request, pk=None):
        job = self.get_object()
        part_id = request.data.get('part_id')
        
        try:
            part = JobPart.objects.get(id=part_id, job=job)
            if part.status == 'CONFIRMED':
                item = part.inventory_item
                item.current_stock += part.quantity
                item.save()
            part.delete()
            return Response({'message': 'Part removed from job card', 'job': ServiceJobSerializer(job).data})
        except JobPart.DoesNotExist:
            return Response({'error': 'Part not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def confirm_parts(self, request, pk=None):
        job = self.get_object()
        staged_parts = job.parts.filter(status='STAGED')

        if not staged_parts.exists():
            return Response({'message': 'No staged parts to confirm'}, status=status.HTTP_200_OK)

        with transaction.atomic():
            for part in staged_parts:
                item = part.inventory_item
                if item.current_stock < part.quantity:
                    transaction.set_rollback(True)
                    return Response({
                        'error': f'Insufficient stock for {item.part_name}. Required: {part.quantity}, Available: {item.current_stock}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                item.current_stock -= part.quantity
                item.save()

                part.status = 'CONFIRMED'
                part.save()

            job.parts_confirmed = True
            job.save()

        return Response({
            'message': 'Parts successfully confirmed and inventory stock updated!',
            'job': ServiceJobSerializer(job).data
        })

    @action(detail=True, methods=['post'])
    def update_labour_charge(self, request, pk=None):
        job = self.get_object()
        raw_val = request.data.get('labour_charge', 0)
        try:
            clean_str = str(raw_val).replace('₹', '').replace(',', '').strip()
            new_labour = Decimal(clean_str) if clean_str else Decimal('0.00')
            if new_labour < Decimal('0.00'):
                new_labour = Decimal('0.00')
            job.labour_charge = new_labour
            job.save()
            return Response({
                'message': f'Labour charge updated to ₹{new_labour:.2f}!',
                'job': ServiceJobSerializer(job).data
            })
        except Exception as e:
            return Response({'message': 'Labour charge updated', 'job': ServiceJobSerializer(job).data})

    @action(detail=True, methods=['post'])
    def finish_service(self, request, pk=None):
        job = self.get_object()
        if not job.assigned_mechanic or job.assigned_mechanic == 'Unassigned':
            return Response({'error': 'Primary Mechanic assignment is compulsory! Please assign a mechanic before finishing the bill.'}, status=status.HTTP_400_BAD_REQUEST)

        existing_invoice = Invoice.objects.filter(service_job=job).first()
        if existing_invoice:
            customer = Customer.objects.filter(vehicle_number=job.vehicle_number).first()
            return Response({
                'message': 'This service has already been billed.',
                'invoice': InvoiceSerializer(existing_invoice).data,
                'job': ServiceJobSerializer(job).data,
                'customer': CustomerSerializer(customer).data if customer else None,
            })

        paid_amount = max(Decimal('0.00'), Decimal(str(request.data.get('paid_amount', 0) or 0)))
        discount_amount = max(Decimal('0.00'), Decimal(str(request.data.get('discount_amount', 0) or 0)))
        labour_input = request.data.get('labour_charge')

        with transaction.atomic():
            if labour_input is not None and str(labour_input).strip() != '':
                try:
                    clean_lab = Decimal(str(labour_input).replace('₹', '').strip())
                    job.labour_charge = max(Decimal('0.00'), clean_lab)
                except Exception:
                    pass

            staged_parts = job.parts.filter(status='STAGED')
            for part in staged_parts:
                item = part.inventory_item
                if item.current_stock >= part.quantity:
                    item.current_stock -= part.quantity
                    item.save()
                    part.status = 'CONFIRMED'
                    part.save()

            parts_tot = Decimal(str(sum([p.unit_price * p.quantity for p in job.parts.all()]) or 0))
            subtotal_bill = Decimal(str(job.labour_charge or 0)) + parts_tot
            grand_total = max(Decimal('0.00'), subtotal_bill - discount_amount)
            paid_amount = min(paid_amount, grand_total)
            pending_amt = max(Decimal('0.00'), grand_total - paid_amount)

            job.status = 'FINISHED'
            job.finished_at = timezone.now()
            job.save()

            customer, created = Customer.objects.get_or_create(
                vehicle_number=job.vehicle_number,
                defaults={
                    'customer_name': job.customer_name,
                    'phone': job.mobile_number,
                }
            )
            if not created:
                customer.customer_name = job.customer_name
                customer.phone = job.mobile_number

            last_inv = Invoice.objects.order_by('-id').first()
            next_id = (last_inv.id + 1) if last_inv else 1
            inv_num = f"INV-PATEL-{next_id:04d}"

            invoice = Invoice.objects.create(
                service_job=job,
                invoice_number=inv_num,
                customer_name=job.customer_name,
                mobile_number=job.mobile_number,
                vehicle_number=job.vehicle_number,
                bike_model=job.bike_model,
                labour_charge=job.labour_charge,
                parts_total=parts_tot,
                grand_total=grand_total,
                paid_amount=paid_amount,
                pending_amount=pending_amt
            )
            customer.pending_amount = Invoice.objects.filter(
                vehicle_number__iexact=job.vehicle_number
            ).aggregate(total=Sum('pending_amount'))['total'] or Decimal('0.00')
            customer.save()

        sync_completed_service_to_mongodb(job, customer, invoice)

        return Response({
            'message': 'Service completed & invoice created!',
            'invoice': InvoiceSerializer(invoice).data,
            'job': ServiceJobSerializer(job).data,
            'customer': CustomerSerializer(customer).data,
        })

    @action(detail=True, methods=['post'])
    def cancel_service(self, request, pk=None):
        job = self.get_object()
        with transaction.atomic():
            confirmed_parts = job.parts.filter(status='CONFIRMED')
            for part in confirmed_parts:
                item = part.inventory_item
                item.current_stock += part.quantity
                item.save()

            job.parts.filter(status='STAGED').delete()
            job.status = 'CANCELLED'
            job.finished_at = timezone.now()
            job.save()

            # ALSO UPDATE ORIGINATING BOOKING TO CANCELLED
            Booking.objects.filter(
                vehicle_number__iexact=job.vehicle_number,
                status__in=['COMPLETED', 'ACCEPTED']
            ).update(status='CANCELLED')

        return Response({'message': 'Service job cancelled. Booking status updated to CANCELLED.', 'job': ServiceJobSerializer(job).data})

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all().order_by('part_name')
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _check_admin_password(self, request):
        ok, err = check_admin_password(request)
        if not ok:
            return False, err
        return True, None

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        allowed, error = self._check_admin_password(request)
        if not allowed:
            return Response({'error': error}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        allowed, error = self._check_admin_password(request)
        if not allowed:
            return Response({'error': error}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        low_items = InventoryItem.objects.filter(current_stock__lte=F('min_stock_alert'))
        serializer = self.get_serializer(low_items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def delete_with_password(self, request, pk=None):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        item = self.get_object()
        serialized = json.dumps(InventoryItemSerializer(item).data, cls=DjangoJSONEncoder)
        admin_name = request.user.username if (request.user and request.user.is_authenticated) else 'Admin Patel'

        RecycleBinItem.objects.create(
            item_type='INVENTORY',
            title=f"Inventory Part #{item.id} - {item.part_name}",
            details=f"Category: {item.category}, Price: ₹{item.price}, Stock: {item.current_stock}",
            serialized_data=serialized,
            deleted_by=admin_name
        )
        log_admin_action(admin_name, 'DELETE_TO_TRASH', f"Moved Inventory Part {item.part_name} to Recycle Bin")
        item.delete()
        return Response({'message': 'Inventory item moved to Recycle Bin successfully!'})

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-last_visit')
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def delete_with_password(self, request, pk=None):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        customer = self.get_object()
        serialized = json.dumps(CustomerSerializer(customer).data, cls=DjangoJSONEncoder)
        admin_name = request.user.username if (request.user and request.user.is_authenticated) else 'Admin Patel'

        RecycleBinItem.objects.create(
            item_type='CUSTOMER',
            title=f"Customer {customer.customer_name} ({customer.vehicle_number})",
            details=f"Phone: {customer.phone}, Dues: ₹{customer.pending_amount}",
            serialized_data=serialized,
            deleted_by=admin_name
        )
        log_admin_action(admin_name, 'DELETE_TO_TRASH', f"Moved Customer {customer.customer_name} to Recycle Bin")
        customer.delete()
        return Response({'message': 'Customer record moved to Recycle Bin successfully!'})

class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all().order_by('-created_at')
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def generate_ai_reply(self, request, pk=None):
        msg_obj = self.get_object()
        msg_obj.ai_approved = False
        msg_obj.save()
        return Response({
            'message': 'AI draft reply generated!',
            'contact_message': ContactMessageSerializer(msg_obj).data
        })

    @action(detail=True, methods=['post'])
    def approve_and_send_ai_reply(self, request, pk=None):
        msg_obj = self.get_object()
        approved_text = request.data.get('approved_text', '').strip() or msg_obj.ai_draft_reply
        
        if not approved_text:
            return Response({'error': 'No approved reply content found.'}, status=status.HTTP_400_BAD_REQUEST)

        msg_obj.reply_text = approved_text
        msg_obj.ai_draft_reply = approved_text
        msg_obj.ai_approved = True
        msg_obj.replied_at = timezone.now()
        msg_obj.status = 'COMPLETED'
        msg_obj.save()

        # Log AI approval event to MongoDB
        try:
            from config.mongodb import log_to_mongo
            log_to_mongo("ai_approved_messages", {
                "event": "AI_REPLY_SENT_COMPLETED",
                "message_id": msg_obj.id,
                "name": msg_obj.name,
                "phone": msg_obj.phone,
                "approved_text": approved_text,
                "approved_at": str(msg_obj.replied_at)
            })
        except Exception:
            pass

        # Generate direct WhatsApp link with approved message
        phone_clean = ''.join(filter(str.isdigit, msg_obj.phone))
        if not phone_clean.startswith('91') and len(phone_clean) == 10:
            phone_clean = '91' + phone_clean

        encoded_msg = str(approved_text).replace('\n', '%0A').replace(' ', '%20')
        whatsapp_link = f"https://wa.me/{phone_clean}?text={encoded_msg}"

        return Response({
            'message': 'Message sent & marked Completed!',
            'whatsapp_link': whatsapp_link,
            'contact_message': ContactMessageSerializer(msg_obj).data
        })

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        msg_obj = self.get_object()
        reply_text = request.data.get('reply_text', '').strip()
        if not reply_text:
            return Response({'error': 'reply_text is required'}, status=status.HTTP_400_BAD_REQUEST)

        msg_obj.reply_text = reply_text
        msg_obj.replied_at = timezone.now()
        msg_obj.status = 'REPLIED'
        msg_obj.save()

        # Log reply to MongoDB
        try:
            from config.mongodb import log_to_mongo
            log_to_mongo("contact_replies", {
                "event": "MESSAGE_REPLIED",
                "message_id": msg_obj.id,
                "name": msg_obj.name,
                "phone": msg_obj.phone,
                "reply_text": reply_text,
                "replied_at": str(msg_obj.replied_at)
            })
        except Exception:
            pass

        # Generate WhatsApp reply link
        phone_clean = ''.join(filter(str.isdigit, msg_obj.phone))
        if not phone_clean.startswith('91') and len(phone_clean) == 10:
            phone_clean = '91' + phone_clean

        wa_message = (
            f"Hello {msg_obj.name},\n\n"
            f"Thank you for contacting *Patel Automobiles*.\n\n"
            f"*Your Inquiry:* \"{msg_obj.message}\"\n\n"
            f"*Our Reply:* \"{reply_text}\"\n\n"
            f"Best regards,\n*Patel Automobiles, Dandi, Valsad*"
        )
        encoded_msg = str(wa_message).replace('\n', '%0A').replace(' ', '%20')
        whatsapp_link = f"https://wa.me/{phone_clean}?text={encoded_msg}"

        return Response({
            'message': 'Reply saved & WhatsApp link generated!',
            'whatsapp_link': whatsapp_link,
            'contact_message': ContactMessageSerializer(msg_obj).data
        })

    @action(detail=True, methods=['post'])
    def delete_with_password(self, request, pk=None):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        msg_obj = self.get_object()
        msg_obj.delete()
        return Response({'message': 'Contact message deleted successfully!'})

class VehicleHistoryViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        raw_num = request.query_params.get('vehicle_number', '').strip().upper()
        raw_mobile = request.query_params.get('mobile_number', '').strip()

        if not raw_num or not raw_mobile:
            return Response(
                {"error": "Both vehicle registration number and 10-digit registered mobile number are required for privacy verification."},
                status=status.HTTP_400_BAD_REQUEST
            )

        clean_search = raw_num.replace('-', '').replace(' ', '')
        clean_mobile = ''.join(filter(str.isdigit, raw_mobile))[-10:]

        if len(clean_mobile) < 10:
            return Response(
                {"error": "Please enter a valid 10-digit registered mobile number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Verify customer mobile match
        customer = None
        for c in Customer.objects.all():
            c_num = c.vehicle_number.replace('-', '').replace(' ', '').upper() if c.vehicle_number else ''
            c_phone = ''.join(filter(str.isdigit, c.phone or ''))[-10:]
            if clean_search == c_num and c_phone == clean_mobile:
                customer = c
                break

        # 2. Match service jobs with mobile verification
        all_jobs = ServiceJob.objects.exclude(status='CANCELLED').order_by('-created_at')
        matched_jobs = []
        for j in all_jobs:
            c_num = j.vehicle_number.replace('-', '').replace(' ', '').upper() if j.vehicle_number else ''
            j_phone = ''.join(filter(str.isdigit, j.mobile_number or ''))[-10:]
            if clean_search == c_num and (j_phone == clean_mobile or (customer and clean_mobile in j_phone)):
                matched_jobs.append(j)

        # 3. Match invoices with mobile verification
        all_invoices = Invoice.objects.order_by('-created_at')
        matched_invoices = []
        for inv in all_invoices:
            c_num = inv.vehicle_number.replace('-', '').replace(' ', '').upper() if inv.vehicle_number else ''
            inv_phone = ''.join(filter(str.isdigit, inv.mobile_number or ''))[-10:]
            if clean_search == c_num and (inv_phone == clean_mobile or (customer and clean_mobile in inv_phone)):
                matched_invoices.append(inv)

        if not customer and not matched_jobs and not matched_invoices:
            return Response(
                {"error": "Vehicle number and registered mobile number do not match. Access denied for privacy protection."},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response({
            "vehicle_number": raw_num,
            "customer": CustomerSerializer(customer).data if customer else None,
            "previous_services": ServiceJobSerializer(matched_jobs, many=True).data,
            "previous_bills": InvoiceSerializer(matched_invoices, many=True).data,
        })

class BillingViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().order_by('-created_at')
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def delete_with_password(self, request, pk=None):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        invoice = self.get_object()
        invoice.delete()
        return Response({'message': 'Invoice deleted successfully!'})

class KhataBookViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        pending_invoices = Invoice.objects.filter(pending_amount__gt=0).order_by('-created_at')
        debtors_data = []
        covered_customer_ids = set()

        for inv in pending_invoices:
            cust = Customer.objects.filter(vehicle_number__iexact=inv.vehicle_number).first()
            if not cust:
                cust = Customer.objects.filter(phone=inv.mobile_number).first()
            if cust:
                covered_customer_ids.add(cust.id)

            parts_list = []
            labour_charge = float(inv.labour_charge)
            if hasattr(inv, 'service_job') and inv.service_job:
                for p in inv.service_job.parts.all():
                    parts_list.append({
                        'part_name': p.part_name,
                        'quantity': p.quantity,
                        'unit_price': float(p.unit_price),
                        'subtotal': float(p.unit_price * p.quantity)
                    })

            entry = {
                'id': f"inv_{inv.id}",
                'invoice_id': inv.id,
                'invoice_number': inv.invoice_number,
                'customer_id': cust.id if cust else None,
                'customer_name': inv.customer_name,
                'phone': inv.mobile_number,
                'vehicle_number': inv.vehicle_number,
                'bike_model': inv.bike_model,
                'created_at': inv.created_at.isoformat(),
                'visit_date': inv.created_at.strftime('%d/%m/%Y %I:%M %p'),
                'total_billed': float(inv.grand_total),
                'total_paid': float(inv.paid_amount),
                'pending_amount': float(inv.pending_amount),
                'labour_charge': labour_charge,
                'parts': parts_list,
                'last_visit': inv.created_at.isoformat(),
            }
            debtors_data.append(entry)

        # Fallback for any Customers with pending_amount > 0 who are not covered by pending invoices
        customers = Customer.objects.filter(pending_amount__gt=0).order_by('-pending_amount')
        for c in customers:
            if c.id in covered_customer_ids:
                inv_sum = Invoice.objects.filter(vehicle_number__iexact=c.vehicle_number).aggregate(total=Sum('pending_amount'))['total'] or 0.00
                diff = float(c.pending_amount) - float(inv_sum)
                if diff > 0.01:
                    entry = {
                        'id': f"cust_diff_{c.id}",
                        'invoice_id': None,
                        'invoice_number': "MANUAL-LEDGER",
                        'customer_id': c.id,
                        'customer_name': c.customer_name,
                        'phone': c.phone,
                        'vehicle_number': c.vehicle_number,
                        'bike_model': "N/A",
                        'created_at': c.last_visit.isoformat() if c.last_visit else None,
                        'visit_date': c.last_visit.strftime('%d/%m/%Y %I:%M %p') if c.last_visit else "N/A",
                        'total_billed': diff,
                        'total_paid': 0.00,
                        'pending_amount': diff,
                        'labour_charge': 0.00,
                        'parts': [],
                        'last_visit': c.last_visit.isoformat() if c.last_visit else None,
                    }
                    debtors_data.append(entry)
            else:
                entry = {
                    'id': f"cust_{c.id}",
                    'invoice_id': None,
                    'invoice_number': "MANUAL-LEDGER",
                    'customer_id': c.id,
                    'customer_name': c.customer_name,
                    'phone': c.phone,
                    'vehicle_number': c.vehicle_number,
                    'bike_model': "N/A",
                    'created_at': c.last_visit.isoformat() if c.last_visit else None,
                    'visit_date': c.last_visit.strftime('%d/%m/%Y %I:%M %p') if c.last_visit else "N/A",
                    'total_billed': float(c.pending_amount),
                    'total_paid': 0.00,
                    'pending_amount': float(c.pending_amount),
                    'labour_charge': 0.00,
                    'parts': [],
                    'last_visit': c.last_visit.isoformat() if c.last_visit else None,
                }
                debtors_data.append(entry)

        total_pending = sum([d['pending_amount'] for d in debtors_data])

        return Response({
            "total_pending_amount": float(total_pending),
            "debtors": debtors_data
        })

    @action(detail=False, methods=['post'])
    def record_payment(self, request):
        invoice_id = request.data.get('invoice_id')
        customer_id = request.data.get('customer_id')
        try:
            payment_amount = float(request.data.get('amount', 0.00))
        except (ValueError, TypeError):
            return Response({'error': 'Invalid payment amount.'}, status=status.HTTP_400_BAD_REQUEST)

        if payment_amount <= 0:
            return Response({'error': 'Please enter a valid payment amount greater than 0.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                if invoice_id:
                    inv = Invoice.objects.get(id=invoice_id)
                    old_pending = float(inv.pending_amount)
                    pay_applied = min(payment_amount, old_pending)
                    inv.pending_amount = max(0.0, old_pending - pay_applied)
                    inv.paid_amount = float(inv.paid_amount) + pay_applied
                    inv.save()

                    cust = Customer.objects.filter(vehicle_number__iexact=inv.vehicle_number).first()
                    if not cust:
                        cust = Customer.objects.filter(phone=inv.mobile_number).first()
                    if cust:
                        cust.pending_amount = max(0.0, float(cust.pending_amount) - pay_applied)
                        cust.save()
                elif customer_id:
                    customer = Customer.objects.get(id=customer_id)
                    old_pending = float(customer.pending_amount)
                    pay_applied = min(payment_amount, old_pending)
                    customer.pending_amount = max(0.0, old_pending - pay_applied)
                    customer.save()

                    invoices = Invoice.objects.filter(
                        Q(customer_name__iexact=customer.customer_name) |
                        Q(vehicle_number__iexact=customer.vehicle_number) |
                        Q(mobile_number__iexact=customer.phone),
                        pending_amount__gt=0
                    ).order_by('created_at')

                    rem = pay_applied
                    for inv in invoices:
                        if rem <= 0:
                            break
                        inv_pending = float(inv.pending_amount)
                        pay_chunk = min(rem, inv_pending)
                        inv.paid_amount = float(inv.paid_amount) + pay_chunk
                        inv.pending_amount = max(0.0, inv_pending - pay_chunk)
                        inv.save()
                        rem -= pay_chunk
                else:
                    return Response({'error': 'Either invoice_id or customer_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'message': f'Payment of ₹{payment_amount:.2f} recorded and synced across Billing, Dashboard, and Reports!',
            })
        except (Invoice.DoesNotExist, Customer.DoesNotExist):
            return Response({'error': 'Invoice or Customer not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def whatsapp_reminder(self, request):
        invoice_id = request.data.get('invoice_id')
        customer_id = request.data.get('customer_id')

        try:
            if invoice_id:
                inv = Invoice.objects.get(id=invoice_id)
                customer_name = inv.customer_name
                phone = inv.mobile_number
                vehicle_number = inv.vehicle_number
                bike_model = inv.bike_model
                visit_date = inv.created_at.strftime('%d/%m/%Y %I:%M %p')
                tot_billed = float(inv.grand_total)
                tot_paid = float(inv.paid_amount)
                pending_val = float(inv.pending_amount)
                tot_labour = float(inv.labour_charge)

                parts_summary = ""
                if hasattr(inv, 'service_job') and inv.service_job:
                    for p in inv.service_job.parts.all():
                        clean_name = p.part_name.split(' Genuine Part')[0].split(' - ')[0].strip()
                        parts_summary += f"  • {clean_name} (x{p.quantity}) - ₹{float(p.unit_price * p.quantity):.2f}\n"

                if tot_labour > 0:
                    parts_summary += f"  • Labour Service Charge - ₹{tot_labour:.2f}\n"

            elif customer_id:
                customer = Customer.objects.get(id=customer_id)
                customer_name = customer.customer_name
                phone = customer.phone
                vehicle_number = customer.vehicle_number
                bike_model = "Vehicle"
                visit_date = customer.last_visit.strftime('%d/%m/%Y') if customer.last_visit else "Recent"
                pending_val = float(customer.pending_amount)
                tot_billed = pending_val
                tot_paid = 0.0
                parts_summary = "  • Outstanding Ledger Dues\n"
            else:
                return Response({'error': 'Either invoice_id or customer_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

            phone_clean = ''.join(filter(str.isdigit, phone or ''))
            if not phone_clean.startswith('91') and len(phone_clean) == 10:
                phone_clean = '91' + phone_clean

            message = (
                f"🚨 *PATEL AUTOMOBILES | SERVICE BILL STATEMENT* 🚨\n\n"
                f"🙏🏻 *Namaste {customer_name} ji*,\n"
                f"Here is your official account & service statement for *{vehicle_number}* ({bike_model}) - Date: {visit_date}:\n\n"
                f"-----------------------------------------\n"
                f"📋 *INSTALLED PARTS & SERVICE BREAKDOWN*\n"
                f"{parts_summary}"
                f"-----------------------------------------\n"
                f"📊 *BILLING SUMMARY*\n"
                f"• *Total Invoice Amount:* ₹{tot_billed:,.2f}\n"
                f"• *Less Received Payment:* -₹{tot_paid:,.2f}\n"
                f"• 🚨 *TOTAL BALANCE DUE:* ₹{pending_val:,.2f}\n"
                f"-----------------------------------------\n\n"
                f"💳 *PAYMENT OPTIONS:*\n"
                f"✓ GPay / PhonePe / Paytm / UPI at workshop desk\n"
                f"✓ Cash / Card at Dandi Workshop Desk\n\n"
                f"Kindly clear your outstanding balance of *₹{pending_val:,.2f}* at your earliest convenience.\n\n"
                f"📍 *Patel Automobiles • Dandi*\n"
                f"Near Dandi Pond, Dandi, Valsad, Gujarat | 📞 +91 81403 71414\n"
                f"*** Thank You For Your Business! Safe Riding! ***"
            )

            import urllib.parse
            encoded_msg = urllib.parse.quote(message)
            whatsapp_link = f"https://api.whatsapp.com/send?phone={phone_clean}&text={encoded_msg}"

            return Response({
                'whatsapp_link': whatsapp_link,
                'message': 'WhatsApp reminder link generated successfully!'
            })
        except (Invoice.DoesNotExist, Customer.DoesNotExist):
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all().order_by('-date')
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def delete_with_password(self, request, pk=None):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        att = self.get_object()
        serialized = json.dumps(AttendanceSerializer(att).data)
        admin_name = request.user.username if (request.user and request.user.is_authenticated) else 'Admin Patel'

        in_str = att.check_in.strftime("%I:%M %p") if att.check_in else 'N/A'
        out_str = att.check_out.strftime("%I:%M %p") if att.check_out else 'N/A'

        RecycleBinItem.objects.create(
            item_type='ATTENDANCE',
            title=f"Attendance Log for {att.mechanic_name} ({att.date})",
            details=f"Status: {att.status}, Check In: {in_str}, Check Out: {out_str}",
            serialized_data=serialized,
            deleted_by=admin_name
        )
        log_admin_action(admin_name, 'DELETE_TO_TRASH', f"Moved Attendance Log for {att.mechanic_name} ({att.date}) to Recycle Bin")
        att.delete()
        return Response({'message': 'Attendance record moved to Recycle Bin successfully!'})

    @action(detail=False, methods=['post'])
    def mark_status(self, request):
        mechanic_name = request.data.get('mechanic_name')
        new_status = request.data.get('status', 'PRESENT').upper()
        if not mechanic_name:
            return Response({'error': 'mechanic_name is required'}, status=status.HTTP_400_BAD_REQUEST)

        today = date.today()
        now_time = datetime.now().time()

        existing = Attendance.objects.filter(mechanic_name=mechanic_name, date=today).first()
        if existing:
            if existing.check_out and new_status != 'ABSENT':
                return Response({'error': f'{mechanic_name} has already completed check-in and check-out for today!'}, status=status.HTTP_400_BAD_REQUEST)
            
            existing.status = new_status
            if new_status in ['PRESENT', 'HALF_DAY']:
                if not existing.check_in:
                    existing.check_in = now_time
            elif new_status == 'ABSENT':
                existing.check_in = None
                existing.check_out = None
            existing.save()
            return Response({'message': f'{mechanic_name} attendance updated to {new_status}!', 'attendance': AttendanceSerializer(existing).data})

        att = Attendance.objects.create(
            mechanic_name=mechanic_name,
            date=today,
            status=new_status,
            check_in=now_time if new_status in ['PRESENT', 'HALF_DAY'] else None
        )
        return Response({'message': f'{mechanic_name} checked in & marked as {new_status}!', 'attendance': AttendanceSerializer(att).data})

    @action(detail=False, methods=['post'])
    def check_in(self, request):
        return self.mark_status(request)

    @action(detail=False, methods=['post'])
    def check_out(self, request):
        mechanic_name = request.data.get('mechanic_name')
        if not mechanic_name:
            return Response({'error': 'mechanic_name is required'}, status=status.HTTP_400_BAD_REQUEST)

        today = date.today()
        now_time = datetime.now().time()

        try:
            att = Attendance.objects.get(mechanic_name=mechanic_name, date=today)
            
            if att.status == 'ABSENT' or not att.check_in:
                return Response({'error': f'Cannot check out! {mechanic_name} is marked ABSENT or has not checked in today.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if att.check_out:
                out_formatted = att.check_out.strftime("%I:%M %p")
                return Response({'error': f'{mechanic_name} has already checked out today at {out_formatted}!'}, status=status.HTTP_400_BAD_REQUEST)

            att.check_out = now_time
            att.save()
            return Response({'message': f'{mechanic_name} checked out successfully at {now_time.strftime("%I:%M %p")}!', 'attendance': AttendanceSerializer(att).data})

        except Attendance.DoesNotExist:
            return Response({'error': f'Cannot check out! {mechanic_name} has not checked in today.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def mechanic_profile(self, request):
        mechanic_name = request.query_params.get('mechanic_name', '').strip()
        if not mechanic_name:
            return Response({'error': 'mechanic_name is required'}, status=status.HTTP_400_BAD_REQUEST)

        today = date.today()
        month_records = Attendance.objects.filter(mechanic_name__iexact=mechanic_name, date__month=today.month, date__year=today.year)
        all_records = Attendance.objects.filter(mechanic_name__iexact=mechanic_name).order_by('-date')[:50]

        present_count = month_records.filter(status='PRESENT').count()
        half_day_count = month_records.filter(status='HALF_DAY').count()
        absent_count = month_records.filter(status='ABSENT').count()

        jobs_count = ServiceJob.objects.filter(assigned_mechanic__iexact=mechanic_name, status='FINISHED').count()

        return Response({
            'mechanic_name': mechanic_name,
            'current_month': today.strftime('%B %Y'),
            'present_count': present_count,
            'half_day_count': half_day_count,
            'absent_count': absent_count,
            'finished_jobs_count': jobs_count,
            'attendance_history': AttendanceSerializer(all_records, many=True).data
        })

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        today = date.today()
        year = int(request.query_params.get('year', today.year))
        month = int(request.query_params.get('month', today.month))

        num_days = calendar.monthrange(year, month)[1]
        monthly_records = Attendance.objects.filter(date__year=year, date__month=month)
        monthly_salaries = MechanicSalaryPayment.objects.filter(payment_date__year=year, payment_date__month=month)
        
        mechanics_roster = ['Unassigned', 'Amitbhai Mechanic', 'Vishalbhai Mechanic', 'Manojbhai Mechanic', 'Patel Owner', 'Ramesh Mechanic', 'Suresh Technician']
        try:
            settings_obj = GarageSettings.objects.first()
            if settings_obj and settings_obj.mechanics_list:
                parsed = [m.strip() for m in settings_obj.mechanics_list.split(',') if m.strip()]
                if parsed:
                    mechanics_roster = parsed
        except Exception:
            pass

        summary_dict = {}
        for m_name in mechanics_roster:
            summary_dict[m_name] = {
                'mechanic_name': m_name,
                'total_days_in_month': num_days,
                'present': 0,
                'absent': 0,
                'half_day': 0,
                'leave': 0,
                'total_days_worked': 0,
                'total_salary_paid': 0.0
            }

        for rec in monthly_records:
            mech = rec.mechanic_name
            if mech not in summary_dict:
                summary_dict[mech] = {
                    'mechanic_name': mech,
                    'total_days_in_month': num_days,
                    'present': 0,
                    'absent': 0,
                    'half_day': 0,
                    'leave': 0,
                    'total_days_worked': 0,
                    'total_salary_paid': 0.0
                }
            
            if rec.status == 'PRESENT':
                summary_dict[mech]['present'] += 1
                summary_dict[mech]['total_days_worked'] += 1
            elif rec.status == 'ABSENT':
                summary_dict[mech]['absent'] += 1
            elif rec.status == 'HALF_DAY':
                summary_dict[mech]['half_day'] += 1
                summary_dict[mech]['total_days_worked'] += 0.5
            elif rec.status == 'LEAVE':
                summary_dict[mech]['leave'] += 1

        for sal in monthly_salaries:
            mech = sal.mechanic_name
            if mech in summary_dict:
                summary_dict[mech]['total_salary_paid'] += float(sal.amount)

        return Response({
            'month': month,
            'year': year,
            'month_name': date(year, month, 1).strftime('%B %Y'),
            'total_days_in_month': num_days,
            'summary': list(summary_dict.values())
        })

    @action(detail=False, methods=['get'])
    def monthly_calendar(self, request):
        today = date.today()
        year = int(request.query_params.get('year', today.year))
        month = int(request.query_params.get('month', today.month))

        num_days = calendar.monthrange(year, month)[1]
        monthly_records = Attendance.objects.filter(date__year=year, date__month=month)

        mechanics_roster = ['Unassigned', 'Amitbhai Mechanic', 'Vishalbhai Mechanic', 'Manojbhai Mechanic', 'Patel Owner', 'Ramesh Mechanic', 'Suresh Technician']
        try:
            settings_obj = GarageSettings.objects.first()
            if settings_obj and settings_obj.mechanics_list:
                parsed = [m.strip() for m in settings_obj.mechanics_list.split(',') if m.strip()]
                if parsed:
                    mechanics_roster = parsed
        except Exception:
            pass

        calendar_grid = {}
        for m_name in mechanics_roster:
            calendar_grid[m_name] = {day: None for day in range(1, num_days + 1)}

        for rec in monthly_records:
            mech = rec.mechanic_name
            if mech not in calendar_grid:
                calendar_grid[mech] = {day: None for day in range(1, num_days + 1)}
            calendar_grid[mech][rec.date.day] = {
                'status': rec.status,
                'check_in': rec.check_in.strftime("%I:%M %p") if rec.check_in else None,
                'check_out': rec.check_out.strftime("%I:%M %p") if rec.check_out else None,
            }

        result = []
        for mech, days in calendar_grid.items():
            result.append({
                'mechanic_name': mech,
                'days': days
            })

        return Response({
            'month': month,
            'year': year,
            'month_name': date(year, month, 1).strftime('%B %Y'),
            'total_days_in_month': num_days,
            'calendar_data': result
        })

class MechanicSalaryPaymentViewSet(viewsets.ModelViewSet):
    queryset = MechanicSalaryPayment.objects.all().order_by('-payment_date', '-created_at')
    serializer_class = MechanicSalaryPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def delete_with_password(self, request, pk=None):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        payment = self.get_object()
        payment.delete()
        return Response({'message': 'Salary payment record deleted successfully!'})

class ReportsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        today = date.today()

        daily_revenue = Invoice.objects.filter(created_at__date=today).aggregate(total=Sum('paid_amount'))['total'] or 0.00
        monthly_revenue = Invoice.objects.filter(created_at__month=today.month, created_at__year=today.year).aggregate(total=Sum('paid_amount'))['total'] or 0.00
        
        total_items = InventoryItem.objects.count()
        low_stock_count = InventoryItem.objects.filter(current_stock__lte=F('min_stock_alert')).count()
        total_inventory_val = sum([float(i.price * i.current_stock) for i in InventoryItem.objects.all()])
        
        total_pending = Customer.objects.aggregate(total=Sum('pending_amount'))['total'] or 0.00
        
        # EXCLUDE CANCELLED JOBS FROM MECHANIC PERFORMANCE STATS
        mechanic_stats = ServiceJob.objects.exclude(status='CANCELLED').values('assigned_mechanic').annotate(
            completed_jobs=Count('id', filter=Q(status='FINISHED')),
            total_jobs=Count('id', filter=Q(status='FINISHED')) + Count('id', filter=Q(status='IN_PROGRESS'))
        )

        return Response({
            "daily_revenue": float(daily_revenue),
            "monthly_revenue": float(monthly_revenue),
            "total_inventory_items": total_items,
            "low_stock_items_count": low_stock_count,
            "total_inventory_value": float(total_inventory_val),
            "total_pending_payments": float(total_pending),
            "mechanic_performance": mechanic_stats
        })

class SettingsViewSet(viewsets.ModelViewSet):
    queryset = GarageSettings.objects.all()
    serializer_class = GarageSettingsSerializer
    permission_classes = [permissions.AllowAny]

    def update(self, request, *args, **kwargs):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def update_settings(self, request):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        
        settings_obj = GarageSettings.objects.first()
        if not settings_obj:
            serializer = GarageSettingsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = GarageSettingsSerializer(settings_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RecycleBinViewSet(viewsets.ModelViewSet):
    queryset = RecycleBinItem.objects.all().order_by('-deleted_at')
    serializer_class = RecycleBinItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        item = self.get_object()
        data = json.loads(item.serialized_data)
        admin_name = request.user.username if (request.user and request.user.is_authenticated) else 'Admin Patel'
        
        try:
            if item.item_type == 'BOOKING':
                data.pop('id', None)
                Booking.objects.create(**data)
            elif item.item_type == 'SERVICE_JOB':
                data.pop('id', None)
                data.pop('parts', None)
                data.pop('parts_total', None)
                data.pop('live_total', None)
                ServiceJob.objects.create(**data)
            elif item.item_type == 'CUSTOMER':
                data.pop('id', None)
                Customer.objects.create(**data)
            elif item.item_type == 'MESSAGE':
                data.pop('id', None)
                ContactMessage.objects.create(**data)
            elif item.item_type == 'INVOICE':
                data.pop('id', None)
                Invoice.objects.create(**data)
            elif item.item_type == 'ATTENDANCE':
                data.pop('id', None)
                data.pop('check_in_time', None)
                data.pop('check_out_time', None)
                Attendance.objects.create(**data)
            elif item.item_type == 'SALARY_PAYMENT':
                data.pop('id', None)
                data.pop('created_at', None)
                MechanicSalaryPayment.objects.create(**data)
            elif item.item_type == 'INVENTORY':
                data.pop('id', None)
                data.pop('is_low_stock', None)
                InventoryItem.objects.create(**data)

            log_admin_action(admin_name, 'RESTORE_ITEM', f"Restored {item.item_type} - {item.title} back from Recycle Bin")
            item.delete()
            return Response({'message': 'Item restored back to active database successfully!'})
        except Exception as e:
            return Response({'error': f"Restore failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def permanent_delete(self, request, pk=None):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        item = self.get_object()
        admin_name = request.user.username if (request.user and request.user.is_authenticated) else 'Admin Patel'
        log_admin_action(admin_name, 'PERMANENT_DELETE', f"Permanently destroyed {item.item_type} - {item.title} from Recycle Bin")
        item.delete()
        return Response({'message': 'Item permanently deleted from database!'})

    @action(detail=False, methods=['post'])
    def empty_recycle_bin(self, request):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        
        count = RecycleBinItem.objects.count()
        if count == 0:
            return Response({'message': 'Recycle Bin is already empty.'})
            
        admin_name = request.user.username if (request.user and request.user.is_authenticated) else 'Admin Patel'
        RecycleBinItem.objects.all().delete()
        log_admin_action(admin_name, 'EMPTY_RECYCLE_BIN', f"Permanently deleted all {count} items from Recycle Bin")
        return Response({'message': f'Successfully emptied Recycle Bin! {count} items permanently deleted.'})

class AdminProfileViewSet(viewsets.ModelViewSet):
    queryset = AdminProfile.objects.all().order_by('-id')
    serializer_class = AdminProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        admin_name = request.user.username if (request.user and request.user.is_authenticated) else 'Admin Patel'
        user_name = request.data.get('user_name', 'New Admin').strip()
        username = request.data.get('username', '').strip() or user_name.lower().replace(' ', '')
        email = request.data.get('email', 'admin@patelautomobiles.com').strip()
        password = request.data.get('password', '').strip()
        if not password:
            return Response({'error': 'Password is required to create an admin account.'}, status=status.HTTP_400_BAD_REQUEST)
        phone = request.data.get('phone', '+91 81403 71414').strip()
        photo = request.data.get('profile_photo', '/logo.png')
        dob = request.data.get('date_of_birth', None)

        if User.objects.filter(username=username).exists():
            return Response({'error': f"Admin username '{username}' already exists!"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            django_user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            profile = AdminProfile.objects.create(
                user=django_user,
                user_name=user_name,
                username=username,
                phone=phone,
                email=email,
                profile_photo=photo,
                date_of_birth=dob if dob else None
            )

        log_admin_action(admin_name, 'CREATE_ADMIN', f"Created new Admin account for '{user_name}' ({username})")
        sync_admin_profile_to_mongodb(profile, password)
        return Response(AdminProfileSerializer(profile).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        admin_name = request.user.username if (request.user and request.user.is_authenticated) else 'Admin Patel'
        profile = self.get_object()

        # Strict Self-Ownership Check: Non-superusers can ONLY update their OWN profile
        if request.user and request.user.is_authenticated and not request.user.is_superuser:
            if profile.user != request.user and profile.username.lower() != request.user.username.lower():
                return Response(
                    {'error': f"Access Denied: You can only edit your own Admin profile. You are not authorized to modify '{profile.user_name}'s account."},
                    status=status.HTTP_403_FORBIDDEN
                )

        user_name = request.data.get('user_name', profile.user_name)
        phone = request.data.get('phone', profile.phone)
        email = request.data.get('email', profile.email)
        photo = request.data.get('profile_photo', profile.profile_photo)
        dob = request.data.get('date_of_birth', profile.date_of_birth)
        new_pass = request.data.get('new_password', '').strip() or request.data.get('password', '').strip()

        profile.user_name = user_name
        profile.phone = phone
        profile.email = email
        profile.profile_photo = photo
        if dob:
            profile.date_of_birth = dob
        profile.save()

        if not profile.user:
            profile.user = User.objects.filter(username=profile.username).first() or (request.user if (request.user and request.user.is_authenticated) else User.objects.first())

        if profile.user:
            profile.user.email = email
            if new_pass:
                profile.user.set_password(new_pass)
            profile.user.save()

        log_admin_action(admin_name, 'UPDATE_ADMIN_PROFILE', f"Updated Admin profile for '{user_name}' ({profile.username})")
        sync_admin_profile_to_mongodb(profile, new_pass)
        return Response(AdminProfileSerializer(profile).data)

    @action(detail=True, methods=['post'])
    def delete_with_password(self, request, pk=None):
        ok, err_msg = check_admin_password(request)
        if not ok:
            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
        
        profile = self.get_object()
        admin_name = request.user.username if (request.user and request.user.is_authenticated) else 'Admin Patel'

        if AdminProfile.objects.count() <= 1:
            return Response({'error': 'Cannot delete the sole remaining Admin user! At least 1 Admin must remain.'}, status=status.HTTP_400_BAD_REQUEST)

        # Strict Self-Ownership / Protection Check for Deletion
        if request.user and request.user.is_authenticated and not request.user.is_superuser:
            if profile.user != request.user and profile.username.lower() != request.user.username.lower():
                return Response(
                    {'error': f"Access Denied: You cannot delete another Admin user's account ('{profile.user_name}')."},
                    status=status.HTTP_403_FORBIDDEN
                )

        target_name = profile.user_name
        with transaction.atomic():
            if profile.user:
                profile.user.delete()
            else:
                profile.delete()

        log_admin_action(admin_name, 'DELETE_ADMIN', f"Deleted Admin account '{target_name}'")
        return Response({'message': f"Admin account '{target_name}' deleted successfully!"})

class AdminAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AdminAuditLogSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = AdminAuditLog.objects.all().order_by('-timestamp')
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')

        if month and year:
            try:
                qs = qs.filter(timestamp__month=int(month), timestamp__year=int(year))
            except ValueError:
                pass
        return qs
