import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from writers.models import WriterProfile
from writers.services import send_writer_application_email

from .serializers import (
    MeSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    UserProfileSerializer,
    WriterProfileSerializer,
    build_token_payload,
    writer_next_step,
)
from .services import OTPError, create_and_send_otp, verify_otp

User = get_user_model()
logger = logging.getLogger(__name__)


class OTPRequestView(APIView):
    permission_classes = [AllowAny]
    target_role = None

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            create_and_send_otp(serializer.validated_data["email"], self.target_role)
        except Exception:
            logger.exception(
                "Failed to send OTP email to %s for role %s",
                serializer.validated_data["email"],
                self.target_role,
            )
            return Response(
                {"detail": "Could not send OTP. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"detail": "OTP sent."})


class OTPVerifyView(APIView):
    permission_classes = [AllowAny]
    target_role = None

    @transaction.atomic
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            email = verify_otp(
                serializer.validated_data["email"],
                serializer.validated_data["otp"],
                self.target_role,
            )
        except OTPError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        user, _ = User.objects.get_or_create(email=email, defaults={"role": self.target_role})
        if user.role != self.target_role:
            return Response(
                {"detail": f"This email is already registered as {user.role}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])

        if user.role == User.Role.WRITER:
            next_step = writer_next_step(user)
        elif user.full_name and user.is_profile_complete:
            next_step = "dashboard"
        else:
            next_step = "complete_profile"

        return Response(
            {
                "tokens": build_token_payload(user),
                "next": next_step,
                "user": MeSerializer(user).data,
            }
        )


class UserOTPRequestView(OTPRequestView):
    target_role = User.Role.USER


class UserOTPVerifyView(OTPVerifyView):
    target_role = User.Role.USER


class WriterOTPRequestView(OTPRequestView):
    target_role = User.Role.WRITER


class WriterOTPVerifyView(OTPVerifyView):
    target_role = User.Role.WRITER


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def patch(self, request):
        if request.user.role != User.Role.USER:
            return Response({"detail": "Only normal users can update this profile."}, status=status.HTTP_403_FORBIDDEN)
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"next": "dashboard", "user": MeSerializer(request.user).data})


class WriterProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def patch(self, request):
        if request.user.role != User.Role.WRITER:
            return Response({"detail": "Only writers can update this profile."}, status=status.HTTP_403_FORBIDDEN)

        profile = getattr(request.user, "writer_profile", None)
        if profile is None:
            profile = WriterProfile(user=request.user)

        serializer = WriterProfileSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        writer_profile = serializer.save()
        send_writer_application_email(writer_profile)
        return Response({"next": "pending_approval", "user": MeSerializer(request.user).data})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)
