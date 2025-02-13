from django.urls import path
from .views import startingPage, AboutUsPage

app_name = "home"

urlpatterns = [
    path('',startingPage.as_view(), name="starting page",  ),
    path('view/', AboutUsPage.as_view(), name="about us", ),
]