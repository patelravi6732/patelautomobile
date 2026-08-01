from decimal import Decimal
from django.db import models
from apps.inventory.models import InventoryItem

class ServiceJob(models.Model):
    STATUS_CHOICES = (
        ('IN_PROGRESS', 'In Progress'),
        ('FINISHED', 'Finished'),
        ('CANCELLED', 'Cancelled'),
    )
    customer_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=20)
    vehicle_number = models.CharField(max_length=20)
    bike_model = models.CharField(max_length=100)
    assigned_mechanic = models.CharField(max_length=100, default='Unassigned')
    secondary_mechanic = models.CharField(max_length=100, blank=True, null=True)
    labour_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    parts_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    @property
    def parts_total(self):
        tot = sum([p.unit_price * p.quantity for p in self.parts.all()])
        return Decimal(str(tot)) if tot else Decimal('0.00')

    @property
    def live_total(self):
        labour = Decimal(str(self.labour_charge or 0))
        parts = Decimal(str(self.parts_total or 0))
        return labour + parts

    def __str__(self):
        return f"Job #{self.id} - {self.vehicle_number} ({self.status})"

class JobPart(models.Model):
    STATUS_CHOICES = (
        ('STAGED', 'Staged (Temporary)'),
        ('CONFIRMED', 'Confirmed'),
    )
    job = models.ForeignKey(ServiceJob, on_delete=models.CASCADE, related_name='parts')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT)
    part_name = models.CharField(max_length=150)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='STAGED')

    def subtotal(self):
        return Decimal(str(self.unit_price or 0)) * Decimal(str(self.quantity or 1))

    def __str__(self):
        return f"{self.part_name} x {self.quantity} on Job #{self.job.id} ({self.status})"
