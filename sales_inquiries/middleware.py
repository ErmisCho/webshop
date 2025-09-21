from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages

# Adjust to your real payment paths:
BLOCKED_PREFIXES = ("/paypal/", "/payments/paypal/")


class BlockPaymentsInInquiryMode:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.SHOP_ENQUIRY_MODE and request.path.startswith(BLOCKED_PREFIXES):
            messages.info(
                request, "Payments are disabled. Please send an inquiry.")
            return redirect("store")
        return self.get_response(request)
