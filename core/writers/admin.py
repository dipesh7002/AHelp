from django.contrib import admin
from django.utils import timezone

from .models import Education, Subject, WriterProfile


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ("level", "status")
    list_filter = ("level", "status")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(WriterProfile)
class WriterProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "education", "approval_status", "is_available", "rating")
    list_filter = ("approval_status", "is_available", "education")
    search_fields = ("user__email", "user__full_name")
    filter_horizontal = ("subjects",)
    actions = ("approve_writers", "reject_writers")

    @admin.action(description="Approve selected writers")
    def approve_writers(self, request, queryset):
        queryset.update(approval_status=WriterProfile.ApprovalStatus.APPROVED, approved_at=timezone.now())

    @admin.action(description="Reject selected writers")
    def reject_writers(self, request, queryset):
        queryset.update(approval_status=WriterProfile.ApprovalStatus.REJECTED, approved_at=None)
