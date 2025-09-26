from django.contrib import admin
from .models import Payment, Order, OrderProduct, Product


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('payment', 'user', 'product',
                       'quantity', 'product_price', 'ordered', 'inquired')
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'phone', 'email',
                    'city', 'order_total', 'tax', 'status', 'is_ordered', 'created_at', 'is_inquired']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'first_name',
                     'last_name', 'phone', 'email']
    list_per_page = 20
    inlines = [OrderProductInline]


@admin.register(OrderProduct)
class OrderProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'product_price',
                    'ordered', 'inquired', 'created_at')
    list_filter = ('ordered', 'inquired', 'created_at', 'product')
    search_fields = ('order__order_number',
                     'product__product_name', 'order__email')
    filter_horizontal = ("variations",)
    readonly_fields = (
        'order', 'payment', 'user', 'product',
        'quantity', 'product_price', 'ordered', 'inquired',
        'created_at', 'updated_at',
    )


# Register your models here.
admin.site.register(Payment)
admin.site.register(Order, OrderAdmin)
# admin.site.register(OrderProduct)
