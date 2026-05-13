import random

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailOTP, User


OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


class OTPError(Exception):
    pass


def generate_otp():
    return f"{random.randint(0, 999999):06d}"


def create_and_send_otp(email, target_role):
    email = User.objects.normalize_email(email)
    otp = generate_otp()
    EmailOTP.objects.create(
        email=email,
        otp_hash=make_password(otp),
        target_role=target_role,
        expires_at=timezone.now() + timezone.timedelta(minutes=OTP_EXPIRY_MINUTES),
    )
    send_mail(
        subject="Your Assignment Helper login OTP",
        message=f"Your OTP is {otp}. It expires in {OTP_EXPIRY_MINUTES} minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def verify_otp(email, otp, target_role):
    email = User.objects.normalize_email(email)
    otp_record = (
        EmailOTP.objects.filter(email=email, target_role=target_role, is_used=False)
        .order_by("-created_at")
        .first()
    )
    if not otp_record:
        raise OTPError("OTP not found. Please request a new OTP.")
    if otp_record.is_expired:
        raise OTPError("OTP has expired. Please request a new OTP.")
    if otp_record.attempts >= MAX_OTP_ATTEMPTS:
        raise OTPError("Too many OTP attempts. Please request a new OTP.")

    otp_record.attempts += 1
    if not check_password(otp, otp_record.otp_hash):
        otp_record.save(update_fields=["attempts"])
        raise OTPError("Invalid OTP.")

    otp_record.is_used = True
    otp_record.save(update_fields=["attempts", "is_used"])
    return email
