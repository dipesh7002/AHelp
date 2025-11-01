from core.mixins.serializers import CommonSerializer
from helper.models import (
    AssignmentHelper,
    Subject, 
    Education
)


class EducationSerializer(CommonSerializer):
    class Meta:
        model = Education
        fields = "__all__"

class AssignmentHelperSerializer(CommonSerializer):
    class Meta:
        model = AssignmentHelper
        fields = "__all__"

class SubjectSerializer(CommonSerializer):
    class Meta:
        model = Subject
        fields = "__all__"