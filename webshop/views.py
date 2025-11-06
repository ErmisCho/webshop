from django.shortcuts import render

from store.models import Product, ReviewRating


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


# def lux_preview(request):
#     cards = [
#         {"title": "Diamond Cluster Necklace",
#             "img": "https://images.unsplash.com/photo-1585386959984-a41552231656?q=80&w=1200&auto=format&fit=crop"},
#         {"title": "Emerald Halo Ring",
#             "img": "https://images.unsplash.com/photo-1617038260897-5f9f6cd7b0b4?q=80&w=1200&auto=format&fit=crop"},
#         {"title": "Sapphire Drop Earrings",
#             "img": "https://placehold.co/600x800"},
#     ]
#     return render(request, "webshop/lux_test.html", {"cards": cards})
def lux_preview(request):
    products = (Product.objects
                .filter(is_available=True)
                .order_by('-created_date')[:6])
    return render(request, "webshop/lux_test.html", {
        "products": products,
        "use_gallery_lightbox": True,   # <-- only here
    })
