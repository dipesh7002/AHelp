from rest_framework.viewsets import ModelViewSet
from helper.models import (
    AssignmentHelper,
    Subject,
    Education
)
from helper.serializers import (
    AssignmentHelperSerializer,
    SubjectSerializer,
    EducationSerializer
    )



class AssignmentHelperViewSet(ModelViewSet):
    queryset = AssignmentHelper.objects.all()
    serializer_class = AssignmentHelperSerializer

class SubjectViewSet(ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

class EducationViewSet(ModelViewSet):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
