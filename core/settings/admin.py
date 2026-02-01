from django.contrib import admin
from .models import InstagramSettings


class InstagramSettingsAdmin(admin.ModelAdmin):
    list_display = ('app_id', 'api_version', 'created_on', 'updated_on')
    readonly_fields = ('created_on', 'updated_on')

    fieldsets = (
        ('Instagram App Configuration', {
            'fields': ('app_id', 'app_secret', 'api_version'),
            'description': 'Configure your Instagram/Facebook App credentials here.'
        }),
        ('Webhook Settings', {
            'fields': ('webhook_verify_token',),
            'description': 'Token used to verify webhook requests from Instagram.'
        }),
        ('Timestamps', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Only allow one Instagram settings instance
        return not InstagramSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the settings instance
        return False


admin.site.register(InstagramSettings, InstagramSettingsAdmin)
