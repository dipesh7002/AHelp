from django.urls import path    
from rest_framework.routers import DefaultRouter
from helper.views import (
    AssignmentHelperViewSet
)

r = DefaultRouter()

r.register("assignment-helper", AssignmentHelperViewSet, basename="assignment-helper")

urlpatterns = r.urls