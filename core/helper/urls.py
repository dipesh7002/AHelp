from django.urls import path    
from .views import HelperHome

app_name ='helper'

urlpatterns = [
    path('home/', HelperHome.as_view(), name='helper home')
]