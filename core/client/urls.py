from django.urls import path
from .views import ClientHome, AssignmentCreate, AssignmentView, AssignmentDetail

app_name = "client"

urlpatterns = [
    path('home/', ClientHome.as_view(), name="client-home"),
    path('create/', AssignmentCreate.as_view(), name='create-assignments'),
    path('viewassignments/', AssignmentView.as_view(), name='view-assignments'),
    path('<pk>/detailassignment/', AssignmentDetail.as_view(), name='detail-assignment'),
]