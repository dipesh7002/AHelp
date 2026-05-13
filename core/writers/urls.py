from django.urls import path

from .views import EducationListView, SubjectListView

urlpatterns = [
    path("education/", EducationListView.as_view(), name="writer-education-list"),
    path("subjects/", SubjectListView.as_view(), name="writer-subject-list"),
]
