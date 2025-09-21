from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_quote_email(ctx: dict) -> None:
    subject = f"New sales inquiry – {ctx.get('email', 'guest')}"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL",
                         "no-reply@example.com")
    to = [getattr(settings, "SALES_INQUIRY_EMAIL_TO", "sales@example.com")]
    text_body = render_to_string("sales_inquiries/email_quote.txt", ctx)
    html_body = render_to_string("sales_inquiries/email_quote.html", ctx)
    msg = EmailMultiAlternatives(subject, text_body, from_email, to)
    msg.attach_alternative(html_body, "text/html")
    msg.send()
