from django.conf import settings


def branding(request):
    return {
        "footer_note": getattr(settings, "FOOTER_NOTE", "A modern Django e-commerce platform built to deliver elegance, performance, and precision."),
        "brand": getattr(settings, "BRAND_NAME", "YOUR BRAND"),
        "nav_items": getattr(settings, "NAV_ITEMS", []),
    }
