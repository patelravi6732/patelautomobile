from rest_framework import serializers
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.settings_app.models import GarageSettings, RecycleBinItem, AdminProfile, AdminAuditLog
from apps.bookings.models import Booking
from apps.inventory.models import InventoryItem
from apps.customers.models import Customer, ContactMessage
from apps.workshop.models import ServiceJob, JobPart
from apps.billing.models import Invoice
from apps.attendance.models import Attendance, MechanicSalaryPayment

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['role', 'phone']

class AdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminProfile
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    role = serializers.CharField(source='profile.role', read_only=True)
    admin_profile = AdminProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'profile', 'admin_profile']

class GarageSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GarageSettings
        fields = '__all__'

class RecycleBinItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecycleBinItem
        fields = '__all__'

class AdminAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminAuditLog
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

class InventoryItemSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = '__all__'

    def get_is_low_stock(self, obj):
        return obj.current_stock <= obj.min_stock_alert

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'

class JobPartSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = JobPart
        fields = '__all__'

class ServiceJobSerializer(serializers.ModelSerializer):
    parts = JobPartSerializer(many=True, read_only=True)
    parts_total = serializers.ReadOnlyField()
    live_total = serializers.ReadOnlyField()

    class Meta:
        model = ServiceJob
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    service_job = ServiceJobSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'

class AttendanceSerializer(serializers.ModelSerializer):
    check_in_time = serializers.SerializerMethodField()
    check_out_time = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = '__all__'

    def get_check_in_time(self, obj):
        if obj.check_in:
            return obj.check_in.strftime("%I:%M %p")
        return None

    def get_check_out_time(self, obj):
        if obj.check_out:
            return obj.check_out.strftime("%I:%M %p")
        return None

class MechanicSalaryPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MechanicSalaryPayment
        fields = '__all__'
