# sales_inquiries/views.py
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from orders.models import Order
from cart.models import CartItem


def _session_cart_id(request) -> str:
    sid = request.session.session_key
    if not sid:
        sid = request.session.create()
    return sid


def _cart_items_qs(request):
    qs = CartItem.objects.select_related(
        "product").prefetch_related("variations")
    if request.user.is_authenticated:
        return qs.filter(user=request.user)
    return qs.filter(cart__cart_id=_session_cart_id(request))


def _cart_snapshot(request):
    items = []
    for ci in _cart_items_qs(request):
        items.append({
            "product": getattr(ci.product, "product_name", str(ci.product)),
            "sku": getattr(ci.product, "sku", ""),
            "quantity": ci.quantity,
            "variations": [
                {"category": getattr(v, "variation_category", ""), "value": getattr(
                    v, "variation_value", "")}
                for v in ci.variations.all()
            ],
        })
    return items


def _clear_cart(request):
    if request.user.is_authenticated:
        CartItem.objects.filter(user=request.user).delete()
    CartItem.objects.filter(cart__cart_id=_session_cart_id(request)).delete()


def _pick_phone(user, order, data_post) -> str:
    # priority: posted 'phone' -> order.phone -> user fields
    posted = (data_post.get("phone") or "").strip()
    if posted:
        return posted
    if order and getattr(order, "phone", ""):
        return order.phone
    for attr in ("phone_number", "phone", "mobile", "phone_no"):
        val = getattr(user, attr, "")
        if val:
            return str(val)
    return ""


@login_required(login_url="login")
@require_POST
def submit_inquiry(request):
    # Only works in enquiry mode
    if not getattr(settings, "SHOP_ENQUIRY_MODE", False):
        messages.error(request, "Sales inquiry mode is disabled.")
        return redirect(reverse("store"))

    user = request.user

    # Pull order meta if present
    order_number = (request.POST.get("order_number") or "").strip()
    order = Order.objects.filter(
        order_number=order_number).first() if order_number else None

    # Build sender info from user + order
    first = getattr(user, "first_name", "") or ""
    last = getattr(user, "last_name", "") or ""
    name = (f"{first} {last}".strip() or getattr(
        user, "username", "") or "Customer")
    email = getattr(user, "email", "") or ""
    phone = _pick_phone(user, order, request.POST)

    ctx = {
        "name": name,
        "email": email,
        "phone": phone,
        "message": (request.POST.get("message") or "").strip(),
        "order_number": order_number,
        "order_note": (getattr(order, "order_note", "") if order else (request.POST.get("order_note") or "")),
        "billing": {
            "name": getattr(order, "full_name", "") if order else name,
            "address": getattr(order, "full_address", "") if order else "",
            "city": getattr(order, "city", "") if order else "",
            "state": getattr(order, "state", "") if order else "",
            "country": getattr(order, "country", "") if order else "",
            "email": getattr(order, "email", "") if order else email,
            "phone": getattr(order, "phone", "") if order else phone,
        },
        "cart_items": _cart_snapshot(request),
    }

    # Send email (reuse your existing service, unchanged)
    from .services import send_quote_email
    try:
        send_quote_email(ctx)
    except Exception:
        messages.error(
            request, "We couldn't send your inquiry right now. Please try again.")
        return redirect(request.META.get("HTTP_REFERER", reverse("store")))

    _clear_cart(request)
    messages.success(
        request, "Thanks! Your inquiry was sent to our sales team.")
    return redirect(reverse("store"))
