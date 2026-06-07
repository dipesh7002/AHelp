from django.contrib import admin
from django.utils import timezone

from accounts.models import User

from .models import (
    Education,
    FavoriteWriter,
    Service,
    ServiceCategory,
    Subject,
    WriterFAQ,
    WriterPerk,
    WriterProfile,
    WriterReview,
    WriterWorkImage,
)


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ("level", "status")
    list_filter = ("level", "status")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.role == User.Role.ADMIN

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == User.Role.ADMIN

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == User.Role.ADMIN


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    list_filter = ("category",)
    search_fields = ("name", "category__name")

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.role == User.Role.ADMIN

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == User.Role.ADMIN

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == User.Role.ADMIN


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order")
    search_fields = ("name",)
    ordering = ("sort_order", "name")

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.role == User.Role.ADMIN

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == User.Role.ADMIN

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == User.Role.ADMIN


class WriterWorkImageInline(admin.TabularInline):
    model = WriterWorkImage
    extra = 1
    max_num = 8


class WriterFAQInline(admin.TabularInline):
    model = WriterFAQ
    extra = 1


class WriterPerkInline(admin.TabularInline):
    model = WriterPerk
    extra = 1


@admin.register(WriterProfile)
class WriterProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "education", "approval_status", "is_available", "starting_price", "delivery_days_min", "delivery_days_max")
    list_filter = ("approval_status", "is_available", "education", "services")
    search_fields = ("user__email", "user__full_name", "user__location", "headline", "bio", "languages")
    filter_horizontal = ("subjects", "services")
    inlines = (WriterWorkImageInline, WriterPerkInline, WriterFAQInline)
    actions = ("approve_writers", "reject_writers")

    @admin.action(description="Approve selected writers")
    def approve_writers(self, request, queryset):
        queryset.update(approval_status=WriterProfile.ApprovalStatus.APPROVED, approved_at=timezone.now())

    @admin.action(description="Reject selected writers")
    def reject_writers(self, request, queryset):
        queryset.update(approval_status=WriterProfile.ApprovalStatus.REJECTED, approved_at=None)


@admin.register(WriterReview)
class WriterReviewAdmin(admin.ModelAdmin):
    list_display = ("writer_profile", "reviewer", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("writer_profile__user__email", "reviewer__email", "comment")
    autocomplete_fields = ("writer_profile",)
    raw_id_fields = ("reviewer",)


@admin.register(WriterFAQ)
class WriterFAQAdmin(admin.ModelAdmin):
    list_display = ("writer_profile", "question", "sort_order")
    search_fields = ("writer_profile__user__email", "question", "answer")


@admin.register(FavoriteWriter)
class FavoriteWriterAdmin(admin.ModelAdmin):
    list_display = ("user", "writer_profile", "created_at")
    search_fields = ("user__email", "writer_profile__user__email")
