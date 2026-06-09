import random
import base64
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailOTP, User


OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


class OTPError(Exception):
    pass


class EmailDeliveryError(Exception):
    pass


def generate_otp():
    return f"{random.randint(0, 999999):06d}"


def send_transactional_email(to_email, subject, message):
    if settings.MAILJET_API_KEY and settings.MAILJET_SECRET_KEY:
        send_mailjet_email(to_email, subject, message)
        return

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )


def send_mailjet_email(to_email, subject, message):
    payload = {
        "Messages": [
            {
                "From": {
                    "Email": settings.MAILJET_FROM_EMAIL,
                    "Name": settings.MAILJET_FROM_NAME,
                },
                "To": [{"Email": to_email}],
                "Subject": subject,
                "TextPart": message,
            }
        ]
    }
    body = json.dumps(payload).encode("utf-8")
    token = f"{settings.MAILJET_API_KEY}:{settings.MAILJET_SECRET_KEY}".encode("utf-8")
    auth = base64.b64encode(token).decode("ascii")
    request = Request(
        settings.MAILJET_API_URL,
        data=body,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise EmailDeliveryError(
            f"Mailjet API returned HTTP {exc.code}: {error_body}"
        ) from exc

    data = json.loads(response_body)
    message_status = data.get("Messages", [{}])[0].get("Status")
    if message_status != "success":
        raise EmailDeliveryError(f"Mailjet API did not accept email: {response_body}")


def create_and_send_otp(email, target_role):
    email = User.objects.normalize_email(email)
    otp = generate_otp()
    EmailOTP.objects.create(
        email=email,
        otp_hash=make_password(otp),
        target_role=target_role,
        expires_at=timezone.now() + timezone.timedelta(minutes=OTP_EXPIRY_MINUTES),
    )
    send_transactional_email(
        to_email=email,
        subject="Your Assignment Helper login OTP",
        message=f"Your OTP is {otp}. It expires in {OTP_EXPIRY_MINUTES} minutes.",
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
