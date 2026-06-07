from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.utils import html
from rest_framework_simplejwt.tokens import RefreshToken

from writers.models import Education, Service, Subject, WriterProfile, WriterWorkImage

User = get_user_model()


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("full_name", "profile_picture", "location", "bio", "languages")

    def update(self, instance, validated_data):
        if "full_name" in validated_data:
            instance.full_name = validated_data["full_name"]
        if "profile_picture" in validated_data:
            instance.profile_picture = validated_data["profile_picture"]
        if "location" in validated_data:
            instance.location = validated_data["location"]
        if "bio" in validated_data:
            instance.bio = validated_data["bio"]
        if "languages" in validated_data:
            instance.languages = validated_data["languages"]
        instance.is_profile_complete = True
        instance.save(update_fields=[
            "full_name", "profile_picture", "location", "bio", "languages", "is_profile_complete",
        ])
        return instance

    def validate_full_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Full name is required.")
        return value


class MultipleImageField(serializers.ListField):
    def get_value(self, dictionary):
        if html.is_html_input(dictionary):
            files = dictionary.getlist(self.field_name)
            if files:
                return files
        return super().get_value(dictionary)


class WriterProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True, write_only=True)
    location = serializers.CharField(required=False, allow_blank=True, max_length=120, write_only=True)
    education = serializers.PrimaryKeyRelatedField(queryset=Education.objects.all())
    subjects = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), many=True, required=False)
    services = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), many=True, required=False)
    work_images = MultipleImageField(
        child=serializers.ImageField(),
        max_length=8,
        required=False,
        write_only=True,
    )

    class Meta:
        model = WriterProfile
        fields = (
            "full_name",
            "profile_picture",
            "cv",
            "education",
            "subjects",
            "services",
            "headline",
            "bio",
            "languages",
            "location",
            "is_available",
            "work_images",
        )

    def update(self, instance, validated_data):
        subjects = validated_data.pop("subjects", None)
        services = validated_data.pop("services", None)
        work_images = validated_data.pop("work_images", None)
        profile_picture = validated_data.pop("profile_picture", serializers.empty)
        location = validated_data.pop("location", serializers.empty)
        full_name = validated_data.pop("full_name")

        user = instance.user
        user.full_name = full_name
        if profile_picture is not serializers.empty:
            user.profile_picture = profile_picture
        if location is not serializers.empty:
            user.location = location
        user.is_profile_complete = True
        user.save(update_fields=["full_name", "profile_picture", "location", "is_profile_complete"])

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.approval_status = WriterProfile.ApprovalStatus.PENDING
        instance.approved_at = None
        instance.save()

        if subjects is not None:
            instance.subjects.set(subjects)
        if services is not None:
            instance.services.set(services)
        if work_images is not None:
            instance.work_images.all().delete()
            WriterWorkImage.objects.bulk_create(
                WriterWorkImage(writer_profile=instance, image=image, sort_order=index)
                for index, image in enumerate(work_images)
            )
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
    date_joined = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "profile_picture",
            "location",
            "bio",
            "languages",
            "role",
            "date_joined",
            "is_email_verified",
            "is_profile_complete",
            "writer_approval_status",
        )

    def get_writer_approval_status(self, obj):
        if obj.role != User.Role.WRITER or not hasattr(obj, "writer_profile"):
            return None
        return obj.writer_profile.approval_status
