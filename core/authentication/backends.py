from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows login with email or username.
    This ensures proper password verification through Django's password hashing.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to get user by email first (preferred for this system)
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                # Fall back to username field
                user = User.objects.get(username=username)
            except MultipleObjectsReturned:
                # If multiple users found by email/username, return None (security issue)
                return None
        except User.DoesNotExist:
            return None

        # Verify password using Django's password hashing
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
