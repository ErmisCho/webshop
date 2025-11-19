import re
from django.core.mail import EmailMultiAlternatives, BadHeaderError
from django.core.mail import EmailMessage, BadHeaderError
from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
import logging
from .email_async import executor

from store.models import Product, ReviewRating
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives, BadHeaderError
from django.conf import settings
from .email_async import executor
from django.shortcuts import render
from django.http import Http404
from django.template import TemplateDoesNotExist

import logging
import re
logger = logging.getLogger(__name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def home(request):
    products = Product.objects.all().filter(
        is_available=True).order_by('created_date')
    for product in products:
        reviews = ReviewRating.objects.filter(
            product_id=product.id, status=True)
    context = {
        'products': products,
        'reviews': reviews,
    }
    return render(request, 'home.html', context)


def lux_preview(request):
    products = (Product.objects
                .filter(is_available=True)
                .order_by('-created_date')[:6])
    return render(request, "webshop/lux_test.html", {
        "products": products,
        "use_gallery_lightbox": True,
    })


logger = logging.getLogger(__name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _send_pair(name, email, phone, msg, pid, ptitle, brand):
    """Runs in a background thread: sends sales email + user confirmation."""
    try:
        sales_subject = f"Sales Inquiry: {ptitle or 'Product'}"
        sales_text = (
            f"Product: {ptitle or '—'} (ID: {pid or '—'})\n"
            f"From: {name} <{email}>\n"
            f"Phone: {phone or '—'}\n\n"
            f"{msg}\n"
        )
        sales_html = f"""
          <div style="font-family:Inter,system-ui,-apple-system,Segoe UI,Arial,sans-serif;line-height:1.5">
            <h2 style="margin:0 0 8px 0">{sales_subject}</h2>
            <p><strong>Product:</strong> {ptitle or '—'} (ID: {pid or '—'})</p>
            <p><strong>From:</strong> {name} &lt;{email}&gt;</p>
            <p><strong>Phone:</strong> {phone or '—'}</p>
            <hr style="border:none;border-top:1px solid #eee;margin:12px 0" />
            <pre style="white-space:pre-wrap;margin:0">{msg}</pre>
          </div>
        """.strip()

        user_subject = f"We received your inquiry — {brand}"
        user_text = (
            f"Hello {name},\n\nThank you for contacting {brand}. "
            f"We’ve received your inquiry and will get back to you shortly.\n\n"
            f"— Your message —\nProduct: {ptitle or '—'} (ID: {pid or '—'})\n\n{msg}\n\n"
            f"Best regards,\n{brand} Sales Team"
        )
        user_html = f"""
          <div style="font-family:Inter,system-ui,-apple-system,Segoe UI,Arial,sans-serif;line-height:1.6">
            <p>Hello {name},</p>
            <p>Thank you for contacting <strong>{brand}</strong>. We’ve received your inquiry and will get back to you shortly.</p>
            <p><strong>Your message</strong></p>
            <p><strong>Product:</strong> {ptitle or '—'} (ID: {pid or '—'})</p>
            <blockquote style="margin:0;padding-left:12px;border-left:3px solid #eee">{msg}</blockquote>
            <p style="margin-top:16px">Best regards,<br>{brand} Sales Team</p>
          </div>
        """.strip()

        # Send to Sales (reply-to = user)
        sales = EmailMultiAlternatives(
            subject=sales_subject,
            body=sales_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.SALES_INQUIRY_EMAIL_TO],
            reply_to=[email],
        )
        sales.attach_alternative(sales_html, "text/html")
        sales.send(fail_silently=False)

        # Send confirmation to User (reply-to = sales)
        user = EmailMultiAlternatives(
            subject=user_subject,
            body=user_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
            reply_to=[settings.SALES_INQUIRY_EMAIL_TO],
        )
        user.attach_alternative(user_html, "text/html")
        user.send(fail_silently=False)

    except BadHeaderError:
        logger.exception("Bad header in email while sending inquiry pair")
    except Exception:
        logger.exception("Unhandled error sending inquiry emails")


@require_POST
def send_inquiry(request):
    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    msg = (request.POST.get("message") or "").strip()
    pid = (request.POST.get("product_id") or "").strip()
    ptitle = (request.POST.get("product_title") or "").strip()

    if not (name and email and msg):
        return JsonResponse({"ok": False, "error": "Missing required fields."}, status=400)
    if not EMAIL_RE.match(email):
        return JsonResponse({"ok": False, "error": "Invalid email format."}, status=400)

    brand = getattr(settings, "BRAND", "Your Brand")

    executor.submit(_send_pair, name, email, phone, msg, pid, ptitle, brand)

    return JsonResponse({"ok": True, "queued": True})


def static_page(request, page_slug):
    template_name = f"webshop/{page_slug}.html"
    try:
        return render(request, template_name)
    except TemplateDoesNotExist:
        raise Http404("Page not found")
