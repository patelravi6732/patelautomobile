from django.db import models

class Booking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    )
    customer_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=20)
    vehicle_number = models.CharField(max_length=20)
    bike_model = models.CharField(max_length=100)
    complaint = models.TextField()
    preferred_date = models.DateField()
    preferred_time = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.vehicle_number} ({self.status})"
