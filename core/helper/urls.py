from django.urls import path
from rest_framework.routers import DefaultRouter
from helper.views import (
    AssignmentHelperViewSet,
    SubjectViewSet,
    EducationViewSet
    )

r = DefaultRouter()

r.register("assignment-helper", AssignmentHelperViewSet, basename="assignment-helper")
r.register("subject", SubjectViewSet, basename="subject")
r.register("education", EducationViewSet, basename="education")

urlpatterns = r.urls
