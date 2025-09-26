from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('order_complete/', views.order_complete, name='order_complete'),
    path("submit_inquiry/", views.submit_inquiry, name="submit_inquiry"),
    path("inquiry_complete/", views.inquiry_complete, name="inquiry_complete"),
]
