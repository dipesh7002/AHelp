from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import Education, Subject
from .serializers import EducationSerializer, SubjectSerializer


class EducationListView(ListAPIView):
    permission_classes = [AllowAny]
    queryset = Education.objects.all().order_by("level", "status")
    serializer_class = EducationSerializer
    pagination_class = None


class SubjectListView(ListAPIView):
    permission_classes = [AllowAny]
    queryset = Subject.objects.all().order_by("name")
    serializer_class = SubjectSerializer
    pagination_class = None
