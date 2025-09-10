from django.shortcuts import get_object_or_404, render

from store.models import Product
from .models import Cart, CartItem
from django.shortcuts import redirect
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

from django.core.mail import send_mail
from django.conf import settings


# Create your views here.


def send_welcome_email(to_email, username, product_name):
    subject = "Welcome to Our Website"
    message = f"Hi {username},\n\nThank you for registering on our site! Feel free to get back to us regarding {product_name}.\n\nBest regards,\nThe Team"
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [to_email]

    try:
        send_mail(subject, message, email_from, recipient_list)
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False


def test_email(request, product_name):
    success = send_welcome_email(
        "example@gmail.com", "Example", product_name)
    print("Email function executed.")
    if success:
        print("Email sent successfully!")
        return HttpResponse("Email sent successfully!")
    return HttpResponse("Failed to send email.")


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )
    cart.save()

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart,
        )
        cart_item.save()
    # return HttpResponse(cart_item.product)
    # test_email(request, product.product_name)

    return redirect('cart')


def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')


def remove_cart_item(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    cart_item.delete()
    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    tax, grand_total = 0, 0
    tax_percentage = 20
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (tax_percentage * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)
