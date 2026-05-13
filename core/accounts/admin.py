from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import EmailOTP, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = (
        "email",
        "full_name",
        "role",
        "is_email_verified",
        "is_profile_complete",
        "is_staff",
    )
    list_filter = ("role", "is_email_verified", "is_profile_complete", "is_staff")
    ordering = ("email",)
    search_fields = ("email", "full_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "role", "is_email_verified", "is_profile_complete")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role"),
            },
        ),
    )


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("email", "target_role", "is_used", "attempts", "expires_at", "created_at")
    list_filter = ("target_role", "is_used")
    search_fields = ("email",)
    readonly_fields = ("otp_hash", "created_at")
