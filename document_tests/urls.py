from django.urls import path
from . import views

urlpatterns = [
    path("emirates-id-test/", views.emirates_id_upload_test),
    path("passport/", views.passport_upload),
    path("uae-visa/", views.uae_visa_upload),
]
