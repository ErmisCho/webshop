from django.urls import path
from .views import submit_inquiry

app_name = "sales_inquiries"
urlpatterns = [
    path("sales-inquiry/submit/", submit_inquiry, name="submit"),
]
