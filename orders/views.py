import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
import datetime
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from cart.models import CartItem
from store.models import Product
from .models import Order, OrderProduct, Payment
from .forms import OrderForm
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.db import transaction
import logging
logger = logging.getLogger(__name__)

# Create your views here.


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(
        user=request.user, is_ordered=False, order_number=body['orderID'])
    print(body)

    payment = Payment(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status'],
    )
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the cart items to Order Product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()

        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear the cart
    CartItem.objects.filter(user=request.user).delete()

    # Send order received email to customer
    mail_subject = 'Thank you for your order'
    message = render_to_string('orders/order_received_email.html', {
        'user': request.user,
        'order': order,
    })

    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }

    # Send order number and transaction ID back to sendData method via JsonResponse
    # return render(request, 'orders/payments.html')
    return JsonResponse(data)


def place_order(request, total=0, quantity=0):
    current_user = request.user

    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    tax_percentage = 20
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (tax_percentage * total)/100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(
                user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            # return redirect('checkout', context)
            return render(request, 'orders/payments.html', context)
    else:
        return redirect('checkout')


def order_complete(request):
    # return render(request, 'orders/order_complete.html')
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')


@login_required
@require_POST
@transaction.atomic
def submit_inquiry(request):
    from django.contrib import messages
    from django.template.loader import render_to_string
    from django.core.mail import EmailMessage
    from django.urls import reverse

    current_user = request.user
    order_number = request.POST.get("order_number")

    if not order_number:
        messages.error(request, "Missing order number for inquiry.")
        return redirect("checkout")

    try:
        order = Order.objects.get(
            user=current_user, is_ordered=False, order_number=order_number)
    except Order.DoesNotExist:
        messages.error(request, "We couldn't find your pending inquiry.")
        return redirect("checkout")

    cart_items = CartItem.objects.filter(user=current_user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("store")

    # Idempotency: if lines already exist, just show complete
    if OrderProduct.objects.filter(order=order).exists():
        return redirect(f"{reverse('orders:inquiry_complete')}?order_number={order.order_number}")

    for item in cart_items.select_related("product"):
        op = OrderProduct.objects.create(
            order=order,
            user=current_user,
            product=item.product,
            quantity=item.quantity,
            product_price=item.product.price,
            ordered=False,
            inquired=True,
        )
        if item.variations.exists():
            op.variations.set(item.variations.all())

    order.is_inquired = True
    order.is_ordered = False
    order.save(update_fields=["is_inquired", "is_ordered"])

    cart_items.delete()

    # send confirmation email to customer (already present)
    try:
        ordered_products = (
            OrderProduct.objects
            .filter(order=order)
            .select_related("product")
            .prefetch_related("variations")
        )
        mail_subject = "Thank you for your inquiry"
        message = render_to_string("orders/order_received_email.html", {
            "user": current_user,
            "order": order,
            "ordered_products": ordered_products,
        })
        msg = EmailMessage(mail_subject, message, to=[order.email])
        msg.content_subtype = "html"
        msg.send(fail_silently=False)
    except Exception:
        pass

    # === NEW: send inquiry details to sales team ===
    try:
        sales_to = getattr(settings, "SALES_INQUIRY_EMAIL_TO",
                           None) or os.getenv("SALES_INQUIRY_EMAIL_TO")
        print(f"before sales_to: {sales_to}")
        if sales_to:
            # gather line items with variations
            ordered_products = OrderProduct.objects.filter(
                order=order).select_related("product").prefetch_related("variations")

            sales_subject = f"New inquiry #{order.order_number} from {order.full_name()}"
            sales_html = render_to_string("sales_inquiries/email_quote.html", {
                "order": order,
                "ordered_products": ordered_products,
            })
            sales_msg = EmailMessage(
                subject=sales_subject,
                body=sales_html,
                to=[sales_to],
                # so sales can reply directly to customer
                reply_to=[order.email] if order.email else None,
            )
            sales_msg.content_subtype = "html"  # render as HTML
            sales_msg.send()
            logger.info("Sales inquiry email sent to %s for %s",
                        sales_to, order.order_number)
        # else: if not configured, we silently skip
        else:
            logger.warning(
                "SALES_INQUIRY_EMAIL_TO not configured; skipping sales email for %s", order.order_number)
            print("wen to else")

    except Exception as e:
        print(f"There is an exception: {e}")

    return redirect(f"{reverse('inquiry_complete')}?order_number={order.order_number}")


def inquiry_complete(request):
    order_number = request.GET.get("order_number")
    try:
        order = Order.objects.get(order_number=order_number, is_inquired=True)
    except Order.DoesNotExist:
        return redirect("home")

    ordered_products = OrderProduct.objects.filter(order=order)
    subtotal = sum(i.product_price * i.quantity for i in ordered_products)

    return render(request, "orders/inquiry_complete.html", {
        "order": order,
        "ordered_products": ordered_products,
        "subtotal": subtotal,
    })
