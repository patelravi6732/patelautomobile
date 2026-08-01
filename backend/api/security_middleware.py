import re
from django.http import HttpResponseBadRequest

class SecurityHardeningMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Malicious Injection Patterns (SQLi, XSS, NoSQLi)
        self.dangerous_patterns = re.compile(
            r"(<script\b[^>]*>|javascript:|union\s+select|select\s+\*|drop\s+table|delete\s+from|insert\s+into|exec\s*\(|eval\s*\(|\$where|\$gt|\$ne)",
            re.IGNORECASE
        )

    def __call__(self, request):
        # 1. Sanitize GET Query Parameters
        for key, val in request.GET.items():
            if self.dangerous_patterns.search(val):
                return HttpResponseBadRequest("Security Warning: Potential malicious code or payload detected.")

        # 2. Process Request
        response = self.get_response(request)

        # 3. Attach Bank-Grade Security Headers to all responses
        response["X-Frame-Options"] = "DENY"
        response["X-Content-Type-Options"] = "nosniff"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response
