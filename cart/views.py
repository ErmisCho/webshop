from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import get_object_or_404, render

from store.models import Product, Variation
from .models import Cart, CartItem
from django.shortcuts import redirect
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required


# Create your views here.


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    current_user = request.user

    # collect variations from POST (unchanged variables)
    product_variation = []
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

    # >>> MINIMAL CHANGE: normalize incoming variations to sorted ID list
    product_variation_ids = sorted([v.id for v in product_variation])

    # ============== AUTHENTICATED USER BRANCH ==============
    if current_user.is_authenticated:
        cart_items = CartItem.objects.filter(
            product=product, user=current_user)

        if cart_items.exists():
            ex_var_list = []
            id = []
            for item in cart_items:
                existing_variation = item.variations.all()
                # >>> MINIMAL CHANGE: compare by sorted IDs
                ex_var_list.append(
                    sorted(list(existing_variation.values_list('id', flat=True))))
                id.append(item.id)

            if product_variation_ids in ex_var_list:
                index = ex_var_list.index(product_variation_ids)
                item_id = id[index]
                item = CartItem.objects.get(
                    product=product, id=item_id, user=current_user)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(
                    product=product, quantity=1, user=current_user)
                if product_variation:
                    item.variations.set(product_variation)
                item.save()
        else:
            item = CartItem.objects.create(
                product=product, quantity=1, user=current_user)
            if product_variation:
                item.variations.set(product_variation)
            item.save()

        return redirect('cart')

    # ============== GUEST / SESSION CART BRANCH ==============
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
    cart.save()

    cart_items = CartItem.objects.filter(product=product, cart=cart)

    if cart_items.exists():
        ex_var_list = []
        id = []
        for item in cart_items:
            existing_variation = item.variations.all()
            # >>> MINIMAL CHANGE: compare by sorted IDs
            ex_var_list.append(
                sorted(list(existing_variation.values_list('id', flat=True))))
            id.append(item.id)

        if product_variation_ids in ex_var_list:
            index = ex_var_list.index(product_variation_ids)
            item_id = id[index]
            item = CartItem.objects.get(product=product, id=item_id, cart=cart)
            item.quantity += 1
            item.save()
        else:
            item = CartItem.objects.create(
                product=product, quantity=1, cart=cart)
            if product_variation:
                item.variations.set(product_variation)
            item.save()
    else:
        item = CartItem.objects.create(product=product, quantity=1, cart=cart)
        if product_variation:
            item.variations.set(product_variation)
        item.save()

    return redirect('cart')


def remove_cart(request, product_id, cart_item_id):

    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(
                product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(
                product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')


def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(
            product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(
            product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    tax, grand_total = 0, 0
    tax_percentage = 20
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(
                user=request.user, is_active=True)
        else:
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


@login_required(login_url='login')
def checkout(request,  total=0, quantity=0, cart_items=None):
    tax, grand_total = 0, 0
    tax_percentage = 20
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(
                user=request.user, is_active=True)
        else:
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
    return render(request, 'store/checkout.html', context)
