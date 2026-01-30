from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from authentication.views import (
    CommonUserViewset,
    CustomTokenObtainPairView,
    VerifyEmailView,
    ResendVerificationEmailView,
)

r = DefaultRouter()
r.register("user", CommonUserViewset, basename="user")

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),
] + r.urls
