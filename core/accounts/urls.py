from django.urls import path

from .views import (
    MeView,
    UserOTPRequestView,
    UserOTPVerifyView,
    UserProfileView,
    WriterOTPRequestView,
    WriterOTPVerifyView,
    WriterProfileView,
)

urlpatterns = [
    path("users/request-otp/", UserOTPRequestView.as_view(), name="user-request-otp"),
    path("users/verify-otp/", UserOTPVerifyView.as_view(), name="user-verify-otp"),
    path("users/profile/", UserProfileView.as_view(), name="user-profile"),
    path("writers/request-otp/", WriterOTPRequestView.as_view(), name="writer-request-otp"),
    path("writers/verify-otp/", WriterOTPVerifyView.as_view(), name="writer-verify-otp"),
    path("writers/profile/", WriterProfileView.as_view(), name="writer-profile"),
    path("me/", MeView.as_view(), name="me"),
]
