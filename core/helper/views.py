from rest_framework.viewsets import ModelViewSet
from helper.models import (
    AssignmentHelper,
)
from helper.serializers import AssignmentHelperSerializer


class AssignmentHelperViewSet(ModelViewSet):
    queryset = AssignmentHelper.objects.all()
    serializer_class = AssignmentHelperSerializer
