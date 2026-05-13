from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from writers.models import Education, Subject, WriterProfile

User = get_user_model()


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("full_name",)

    def update(self, instance, validated_data):
        instance.full_name = validated_data["full_name"]
        instance.is_profile_complete = True
        instance.save(update_fields=["full_name", "is_profile_complete"])
        return instance

    def validate_full_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Full name is required.")
        return value


class WriterProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True)
    education = serializers.PrimaryKeyRelatedField(queryset=Education.objects.all())
    subjects = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), many=True, required=False)

    class Meta:
        model = WriterProfile
        fields = ("full_name", "profile_picture", "cv", "education", "subjects", "is_available")

    def update(self, instance, validated_data):
        subjects = validated_data.pop("subjects", None)
        full_name = validated_data.pop("full_name")

        user = instance.user
        user.full_name = full_name
        user.is_profile_complete = True
        user.save(update_fields=["full_name", "is_profile_complete"])

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.approval_status = WriterProfile.ApprovalStatus.PENDING
        instance.approved_at = None
        instance.save()

        if subjects is not None:
            instance.subjects.set(subjects)
        return instance

    def validate_full_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Full name is required.")
        return value

    def validate_cv(self, value):
        allowed_extensions = (".pdf", ".doc", ".docx")
        if value and not value.name.lower().endswith(allowed_extensions):
            raise serializers.ValidationError("CV must be a PDF, DOC, or DOCX file.")
        return value

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        if not attrs.get("cv") and not getattr(instance, "cv", None):
            raise serializers.ValidationError({"cv": "CV is required."})
        return attrs


def build_token_payload(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def writer_next_step(user):
    if not user.is_profile_complete or not hasattr(user, "writer_profile"):
        return "complete_writer_profile"
    if user.writer_profile.approval_status == WriterProfile.ApprovalStatus.APPROVED:
        return "writer_dashboard"
    return "pending_approval"


class MeSerializer(serializers.ModelSerializer):
    writer_approval_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "role",
            "is_email_verified",
            "is_profile_complete",
            "writer_approval_status",
        )

    def get_writer_approval_status(self, obj):
        if obj.role != User.Role.WRITER or not hasattr(obj, "writer_profile"):
            return None
        return obj.writer_profile.approval_status
