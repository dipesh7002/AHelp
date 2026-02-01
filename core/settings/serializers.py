from rest_framework import serializers
from .models import InstagramSettings


class InstagramSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for Instagram settings
    """
    permissions = serializers.SerializerMethodField()
    graph_api_url = serializers.SerializerMethodField()

    class Meta:
        model = InstagramSettings
        fields = [
            'id', 'app_id', 'app_secret', 'api_version',
            'webhook_verify_token', 'permissions', 'graph_api_url',
            'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'created_on', 'updated_on', 'permissions', 'graph_api_url']
        extra_kwargs = {
            'app_secret': {'write_only': True},
        }

    def get_permissions(self, obj):
        return obj.permissions

    def get_graph_api_url(self, obj):
        return obj.graph_api_url
