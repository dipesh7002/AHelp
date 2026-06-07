from django.urls import path

from .views import (
    EducationListView,
    FavoriteWriterDestroyView,
    FavoriteWriterListCreateView,
    ServiceCategoryListView,
    ServiceListView,
    SubjectListView,
    WriterCardListView,
    WriterDetailView,
    WriterFAQListView,
    WriterReviewListCreateView,
)

urlpatterns = [
    path("education/", EducationListView.as_view(), name="writer-education-list"),
    path("subjects/", SubjectListView.as_view(), name="writer-subject-list"),
    path("service-categories/", ServiceCategoryListView.as_view(), name="writer-service-category-list"),
    path("services/", ServiceListView.as_view(), name="writer-service-list"),
    path("profiles/", WriterCardListView.as_view(), name="writer-profile-list"),
    path("profiles/<int:pk>/", WriterDetailView.as_view(), name="writer-profile-detail"),
    path("profiles/<int:pk>/reviews/", WriterReviewListCreateView.as_view(), name="writer-review-list-create"),
    path("profiles/<int:pk>/faqs/", WriterFAQListView.as_view(), name="writer-faq-list"),
    path("favorites/", FavoriteWriterListCreateView.as_view(), name="writer-favorite-list-create"),
    path("favorites/<int:pk>/", FavoriteWriterDestroyView.as_view(), name="writer-favorite-destroy"),
]
