from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.mixins.models import CommonModel
from django.contrib.auth.models import BaseUserManager

class CommonUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)

class CommonUser(AbstractBaseUser, PermissionsMixin, CommonModel):
    class Gender(models.IntegerChoices):
        MALE = 1, _("Male")
        FEMALE = 2, _("Female")
        OTHER = 3, _("Other")

    class Role(models.TextChoices):
        COMMON = 'common', _('CommonUser')
        HELPER = 'helper', _('AssignmentHelper')
        ADMIN = 'admin', _('SuperUser')

    first_name = models.CharField(max_length=50, verbose_name=_("First Name"))
    middle_name = models.CharField(
        max_length=50, null=True, blank=True, verbose_name=_("Middle Name")
    )
    last_name = models.CharField(max_length=50, verbose_name=_("Last Name"))
    email = models.EmailField(unique=True, verbose_name=_("Email"))
    username = models.CharField(
        max_length=150, unique=True, null=True, blank=True, verbose_name=_("Username")
    )
    image = models.ImageField(null=True, blank=True, upload_to="authentication/images")
    role = models.CharField(
        max_length=10, 
        choices=Role.choices, 
        default=Role.COMMON, 
        verbose_name=_("Role")
    )
    email_verified = models.BooleanField(
        default=False, 
        verbose_name=_("Email Verified")
    )

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = CommonUserManager()  # 🔴 REQUIRED

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    @property
    def is_common_user(self):
        return self.role == self.Role.COMMON

    @property
    def is_assignment_helper(self):
        return self.role == self.Role.HELPER

    @property
    def is_superuser_role(self):
        return self.role == self.Role.ADMIN

    def save(self, *args, **kwargs):
        # Auto-set is_staff and is_superuser for admin role
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)
