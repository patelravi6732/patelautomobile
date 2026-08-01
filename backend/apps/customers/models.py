from django.db import models

class Customer(models.Model):
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    vehicle_number = models.CharField(max_length=20, unique=True)
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    visit_count = models.IntegerField(default=1)
    last_visit = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer_name} ({self.vehicle_number})"

class ContactMessage(models.Model):
    STATUS_CHOICES = (
        ('UNREAD', 'Unread'),
        ('READ', 'Read'),
        ('REPLIED', 'Replied'),
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='UNREAD')
    reply_text = models.TextField(blank=True, null=True)
    ai_draft_reply = models.TextField(blank=True, null=True)
    ai_approved = models.BooleanField(default=False)
    replied_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name} ({self.phone}) - {self.status}"
