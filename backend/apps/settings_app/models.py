from django.db import models
from django.contrib.auth.models import User

class GarageSettings(models.Model):
    garage_name = models.CharField(max_length=100, default="Patel Automobiles")
    logo = models.TextField(blank=True, null=True, default="/logo.png")
    address = models.TextField(default="Near Dandi Pond, Dandi, Valsad, Gujarat - 396385")
    phone = models.CharField(max_length=20, default="+91 81403 71414")
    whatsapp_number = models.CharField(max_length=20, default="+91 81403 71414")
    email = models.EmailField(default="contact@patelautomobiles.com")
    timing_text = models.TextField(default="Mon - Sat: 09:00 AM - 08:30 PM, Sun: 09:00 AM - 02:00 PM")
    safety_message = models.TextField(default="Thank you for choosing us! Wish you a safe & smooth ride. 🛵⛑️")
    mechanics_list = models.TextField(default="Unassigned, Amitbhai Mechanic, Vishalbhai Mechanic, Manojbhai Mechanic, Patel Owner, Ramesh Mechanic, Suresh Technician")
    default_labour_charge = models.DecimalField(max_digits=10, decimal_places=2, default=300.00)
    default_min_stock = models.IntegerField(default=5)
    upi_qr_code = models.TextField(blank=True, null=True, default="/upi_qr.jpg")
    upi_id = models.CharField(max_length=100, default="pritpatel9397@oksbi")
    upi_payee_name = models.CharField(max_length=100, default="Prit Patel")

    def __str__(self):
        return self.garage_name

class RecycleBinItem(models.Model):
    item_type = models.CharField(max_length=50) # SERVICE_JOB, BOOKING, CUSTOMER, INVOICE, ATTENDANCE, MESSAGE, INVENTORY
    title = models.CharField(max_length=200)
    details = models.TextField(blank=True, null=True)
    serialized_data = models.TextField()
    deleted_by = models.CharField(max_length=100, default='Admin')
    deleted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item_type} - {self.title}"

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile', null=True, blank=True)
    user_name = models.CharField(max_length=100, default="Admin Patel")
    username = models.CharField(max_length=100, default="admin")
    phone = models.CharField(max_length=20, default="+91 81403 71414")
    email = models.EmailField(default="admin@patelautomobiles.com")
    profile_photo = models.TextField(blank=True, null=True, default="/logo.png")
    date_of_birth = models.DateField(blank=True, null=True)
    failed_attempts = models.IntegerField(default=0)
    lockout_tier = models.IntegerField(default=0)
    lockout_until = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user_name} ({self.username})"

class AdminAuditLog(models.Model):
    admin_name = models.CharField(max_length=100, default="Admin")
    action_type = models.CharField(max_length=100)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin_name} - {self.action_type} at {self.timestamp}"
