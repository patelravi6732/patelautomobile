from django.db import models

class InventoryItem(models.Model):
    part_name = models.CharField(max_length=150)
    category = models.CharField(max_length=100, default='General')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    current_stock = models.IntegerField(default=0)
    min_stock_alert = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.part_name} - ₹{self.price} (Stock: {self.current_stock})"
