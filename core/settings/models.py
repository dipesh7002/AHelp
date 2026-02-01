from django.db import models
from django.utils.translation import gettext_lazy as _
from core.mixins.models import CommonModel


class InstagramSettings(CommonModel):
    """
    Specific model for Instagram API settings
    """
    app_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Instagram App ID")
    )
    app_secret = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Instagram App Secret")
    )
    api_version = models.CharField(
        max_length=10,
        default='v20.0',
        verbose_name=_("API Version")
    )
    webhook_verify_token = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Webhook Verify Token")
    )

    class Meta:
        db_table = 'instagram_settings'
        verbose_name = _('Instagram Settings')
        verbose_name_plural = _('Instagram Settings')

    def __str__(self):
        return f"Instagram Settings (App ID: {self.app_id or 'Not Set'})"

    @property
    def graph_api_url(self):
        return f"https://graph.facebook.com/{self.api_version}"

    @property
    def permissions(self):
        return [
            'pages_messaging',
            'pages_show_list',
            'instagram_basic',
            'instagram_manage_messages',
            'instagram_manage_comments'
        ]
