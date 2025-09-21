from django.conf import settings


def shop_flags(request):
    return {"SHOP_ENQUIRY_MODE": getattr(settings, "SHOP_ENQUIRY_MODE", False)}
