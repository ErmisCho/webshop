# sales_inquiries/templatetags/inquiry_ui.py
from django import template
from django.conf import settings
register = template.Library()


@register.inclusion_tag("sales_inquiries/_checkout_cta.html", takes_context=True)
def checkout_cta(context):
    return {
        "SHOP_ENQUIRY_MODE": context.get("SHOP_ENQUIRY_MODE", getattr(settings, "SHOP_ENQUIRY_MODE", False)),
        "request": context.get("request"),
        "order": context.get("order"),
    }


@register.inclusion_tag("sales_inquiries/_price.html", takes_context=True)
def render_price(context, value, label_when_hidden=""):
    return {
        "SHOP_ENQUIRY_MODE": context.get("SHOP_ENQUIRY_MODE", getattr(settings, "SHOP_ENQUIRY_MODE", False)),
        "value": value,
        "label_when_hidden": label_when_hidden,
    }
