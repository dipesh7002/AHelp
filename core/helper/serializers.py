from core.mixins.serializers import CommonSerializer
from helper.models import (
    AssignmentHelper,
    Subject, 
    Education
)
from authentication.serializers import CommonUserSerializer
from rest_framework import serializers


class EducationSerializer(CommonSerializer):
    class Meta:
        model = Education
        fields = "__all__"


class AssignmentHelperSerializer(CommonSerializer):
    user = CommonUserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    education_details = serializers.SerializerMethodField()
    assigned_users_count = serializers.SerializerMethodField()
    rating_display = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentHelper
        fields = [
            "id", "user", "user_id", "pp", "education", 
            "education_details", "rating", "rating_display",
            "assigned_users", "assigned_users_count",
            "is_available", "is_active", "created_on", "updated_on"
        ]
        read_only_fields = ["assigned_users_count"]

    def get_education_details(self, obj):
        if obj.education:
            return EducationSerializer(obj.education).data
        return None

    def get_assigned_users_count(self, obj):
        return obj.assigned_users.count()

    def get_rating_display(self, obj):
        if obj.rating is None:
            return "N/A"
        return f"{obj.rating}/5"


class SubjectSerializer(CommonSerializer):
    class Meta:
        model = Subject
        fields = "__all__"