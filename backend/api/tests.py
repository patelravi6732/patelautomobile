from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from api.models import (
    UserProfile, InventoryItem, ServiceJob, JobPart, Customer, Invoice, Attendance
)
from apps.settings_app.models import RecycleBinItem

class GarageLogicTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', password='adminpassword')
        UserProfile.objects.create(user=self.admin, role='ADMIN')
        
        self.staff = User.objects.create_user(username='staff', password='staffpassword')
        UserProfile.objects.create(user=self.staff, role='STAFF')
        
        self.item = InventoryItem.objects.create(
            part_name='Engine Oil 1L',
            category='Engine Oil',
            price=450.00,
            current_stock=10,
            min_stock_alert=3
        )
        
        self.job = ServiceJob.objects.create(
            customer_name='Test Customer',
            mobile_number='9876543210',
            vehicle_number='GJ-07-TEST-100',
            bike_model='Activa 6G',
            labour_charge=300.00,
            status='IN_PROGRESS'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_staged_part_does_not_reduce_stock(self):
        # Add staged part
        response = self.client.post(f'/api/workshop/{self.job.id}/add_staged_part/', {
            'inventory_id': self.item.id,
            'quantity': 2
        })
        self.assertEqual(response.status_code, 200)
        
        # Verify Inventory stock remains untouched (10)
        self.item.refresh_from_db()
        self.assertEqual(self.item.current_stock, 10)
        
        # Verify JobPart is STAGED
        part = JobPart.objects.get(job=self.job, inventory_item=self.item)
        self.assertEqual(part.status, 'STAGED')

    def test_confirm_parts_deducts_stock_atomically(self):
        # Add staged part
        self.client.post(f'/api/workshop/{self.job.id}/add_staged_part/', {
            'inventory_id': self.item.id,
            'quantity': 2
        })
        
        # Confirm parts
        response = self.client.post(f'/api/workshop/{self.job.id}/confirm_parts/')
        self.assertEqual(response.status_code, 200)
        
        # Verify Inventory stock decreased by 2 (10 -> 8)
        self.item.refresh_from_db()
        self.assertEqual(self.item.current_stock, 8)
        
        # Verify JobPart is CONFIRMED
        part = JobPart.objects.get(job=self.job, inventory_item=self.item)
        self.assertEqual(part.status, 'CONFIRMED')

    def test_cancel_service_leaves_inventory_untouched_for_staged_parts(self):
        # Add staged part
        self.client.post(f'/api/workshop/{self.job.id}/add_staged_part/', {
            'inventory_id': self.item.id,
            'quantity': 3
        })
        
        # Cancel service
        response = self.client.post(f'/api/workshop/{self.job.id}/cancel_service/')
        self.assertEqual(response.status_code, 200)
        
        # Stock remains 10
        self.item.refresh_from_db()
        self.assertEqual(self.item.current_stock, 10)

    def test_finish_service_creates_invoice_customer_and_khata_due(self):
        self.job.assigned_mechanic = 'Amitbhai Mechanic'
        self.job.save()
        self.client.post(f'/api/workshop/{self.job.id}/add_staged_part/', {
            'inventory_id': self.item.id,
            'quantity': 2
        })

        response = self.client.post(f'/api/workshop/{self.job.id}/finish_service/', {
            'labour_charge': 300,
            'discount_amount': 0,
            'paid_amount': 1000,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Invoice.objects.count(), 1)
        invoice = Invoice.objects.get(service_job=self.job)
        self.assertEqual(float(invoice.grand_total), 1200.0)
        self.assertEqual(float(invoice.pending_amount), 200.0)
        customer = Customer.objects.get(vehicle_number=self.job.vehicle_number)
        self.assertEqual(float(customer.pending_amount), 200.0)
        khata = self.client.get('/api/khata-book/')
        self.assertEqual(khata.status_code, 200)
        self.assertEqual(float(khata.data['total_pending_amount']), 200.0)

    def test_delete_attendance_removes_active_record_and_creates_recycle_item(self):
        attendance = Attendance.objects.create(mechanic_name='Amitbhai Mechanic')
        response = self.client.post(
            f'/api/attendance/{attendance.id}/delete_with_password/',
            {'admin_password': 'adminpassword'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Attendance.objects.filter(id=attendance.id).exists())
        self.assertTrue(RecycleBinItem.objects.filter(item_type='ATTENDANCE').exists())
