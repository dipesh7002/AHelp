from core.mixins.serializers import CommonSerializer
from helper.models import AssignmentHelper


class AssignmentHelperSerializer(CommonSerializer):
    class Meta:
        model = AssignmentHelper
        fields = "__all__"
