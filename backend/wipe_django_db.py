import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.bookings.models import Booking
from apps.workshop.models import ServiceJob, JobPart
from apps.inventory.models import InventoryItem
from apps.customers.models import Customer, ContactMessage
from apps.billing.models import Invoice
from apps.settings_app.models import RecycleBinItem
from apps.attendance.models import Attendance, MechanicSalaryPayment

print("Wiping Django SQLite models...")
Booking.objects.all().delete()
JobPart.objects.all().delete()
ServiceJob.objects.all().delete()
InventoryItem.objects.all().delete()
Customer.objects.all().delete()
ContactMessage.objects.all().delete()
Invoice.objects.all().delete()
RecycleBinItem.objects.all().delete()
Attendance.objects.all().delete()
MechanicSalaryPayment.objects.all().delete()

print("Django SQLite models wiped clean successfully!")
