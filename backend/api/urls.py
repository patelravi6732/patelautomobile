from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    login_with_lockout, current_user, request_otp_reset, verify_otp_reset_password, verify_otp_only, public_create_booking, public_create_contact_message, public_garage_info, public_master_store, dashboard_stats,
    BookingViewSet, WorkshopViewSet, InventoryViewSet, CustomerViewSet, ContactMessageViewSet,
    VehicleHistoryViewSet, BillingViewSet, KhataBookViewSet, AttendanceViewSet,
    ReportsViewSet, SettingsViewSet, RecycleBinViewSet, AdminProfileViewSet, AdminAuditLogViewSet,
    MechanicSalaryPaymentViewSet
)

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'workshop', WorkshopViewSet, basename='workshop')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'messages', ContactMessageViewSet, basename='contact_message')
router.register(r'billing', BillingViewSet, basename='billing')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'settings', SettingsViewSet, basename='settings')
router.register(r'recycle-bin', RecycleBinViewSet, basename='recycle_bin')
router.register(r'admin-profile', AdminProfileViewSet, basename='admin_profile')
router.register(r'admin-audit-logs', AdminAuditLogViewSet, basename='admin_audit_logs')
router.register(r'salary-payments', MechanicSalaryPaymentViewSet, basename='salary_payments')

urlpatterns = [
    # JWT Auth with Lockout Security
    path('auth/token/', login_with_lockout, name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', current_user, name='current_user'),

    # Mobile OTP Password Reset
    path('auth/request-otp/', request_otp_reset, name='request_otp_reset'),
    path('auth/verify-otp-only/', verify_otp_only, name='verify_otp_only'),
    path('auth/verify-otp-reset/', verify_otp_reset_password, name='verify_otp_reset_password'),

    # Public Endpoints
    path('public/bookings/', public_create_booking, name='public_booking'),
    path('public/contact/', public_create_contact_message, name='public_contact'),
    path('public/info/', public_garage_info, name='public_garage_info'),
    path('public/master_store/', public_master_store, name='public_master_store'),

    # Dashboard & Custom Routers
    path('dashboard/stats/', dashboard_stats, name='dashboard_stats'),
    path('vehicle-history/', VehicleHistoryViewSet.as_view({'get': 'list'}), name='vehicle_history'),
    path('khata-book/', KhataBookViewSet.as_view({'get': 'list'}), name='khata_book'),
    path('khata-book/record-payment/', KhataBookViewSet.as_view({'post': 'record_payment'}), name='khata_record_payment'),
    path('khata-book/whatsapp-reminder/', KhataBookViewSet.as_view({'post': 'whatsapp_reminder'}), name='khata_whatsapp'),
    path('reports/', ReportsViewSet.as_view({'get': 'list'}), name='reports'),

    # Router URLs
    path('', include(router.urls)),
]
