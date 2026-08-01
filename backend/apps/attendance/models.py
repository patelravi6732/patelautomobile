from django.db import models
from django.utils import timezone

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('HALF_DAY', 'Half Day'),
        ('LEAVE', 'Leave'),
    )
    mechanic_name = models.CharField(max_length=100)
    date = models.DateField(default=timezone.now)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PRESENT')

    class Meta:
        unique_together = ('mechanic_name', 'date')

    def __str__(self):
        return f"{self.mechanic_name} - {self.date} ({self.status})"

class MechanicSalaryPayment(models.Model):
    PAYMENT_TYPES = (
        ('SALARY', 'Full Salary'),
        ('ADVANCE', 'Advance Payment'),
        ('BONUS', 'Bonus / Incentive'),
    )
    mechanic_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='SALARY')
    payment_date = models.DateField(default=timezone.now)
    notes = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mechanic_name} - ₹{self.amount} ({self.payment_type}) on {self.payment_date}"
