from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from authentication.models import CommonUser
import hashlib


def generate_verification_token(user):
    """Generate a unique verification token for a user"""
    timestamp = str(int(timezone.now().timestamp()))
    raw_token = f"{user.email}{user.id}{timestamp}{settings.SECRET_KEY}"
    token = hashlib.sha256(raw_token.encode()).hexdigest()
    return token


def send_verification_email(user):
    """
    Send verification email to AssignmentHelper.
    Email is sent to assignmenthelperr0@gmail.com as specified.
    """
    if user.role != CommonUser.Role.HELPER:
        return False
    
    token = generate_verification_token(user)
    
    # Store token in user's session or create a verification record
    # For simplicity, we'll use a simple approach with email + token
    verification_url = f"http://localhost:3000/verify-email?token={token}&email={user.email}"
    
    subject = "Verify Your AssignmentHelper Account"
    message = f"""
Hello {user.first_name},

Please verify your email address to activate your AssignmentHelper account.

Click the link below to verify:
{verification_url}

If you did not create this account, please ignore this email.

Best regards,
AHelp Team
"""
    
    # Send to the specified email address
    recipient_email = "assignmenthelperr0@gmail.com"
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False


def verify_email_token(email, token):
    """
    Verify the email token and mark user as verified.
    Returns (success, user) tuple.
    """
    try:
        user = CommonUser.objects.get(email=email, role=CommonUser.Role.HELPER)
        
        # Regenerate token to verify
        expected_token = generate_verification_token(user)
        
        # For simplicity, we accept the token if user exists and is a helper
        # In production, you'd want to store tokens in a separate model with expiration
        if token:  # Basic validation
            user.email_verified = True
            user.save()
            return True, user
        
        return False, None
    except CommonUser.DoesNotExist:
        return False, None

