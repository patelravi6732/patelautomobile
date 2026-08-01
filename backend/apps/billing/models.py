from django.db import models
from apps.workshop.models import ServiceJob

class Invoice(models.Model):
    service_job = models.OneToOneField(ServiceJob, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=20)
    vehicle_number = models.CharField(max_length=20)
    bike_model = models.CharField(max_length=100)
    labour_charge = models.DecimalField(max_digits=10, decimal_places=2)
    parts_total = models.DecimalField(max_digits=10, decimal_places=2)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} - ₹{self.grand_total}"
