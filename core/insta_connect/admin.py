from django.contrib import admin

<<<<<<< HEAD
# Register your models here.
=======

@admin.register(InstagramAccount)
class InstagramAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'instagram_username']
    search_fields = ['user__username', 'instagram_username']
    readonly_fields = ['instagram_business_account_id']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Instagram Details', {
            'fields': ('instagram_business_account_id', 'instagram_username')
        }),
        ('Facebook Page', {
            'fields': ('facebook_page_id', 'facebook_page_name')
        }),
        ('Token', {
            'fields': ('access_token', 'token_expires_at'),
            'classes': ('collapse',)
        }),
        # ('Status', {
        #     'fields': ('is_active', 'connected_at', 'last_sync')
        # }),
    )


@admin.register(InstagramConversation)
class InstagramConversationAdmin(admin.ModelAdmin):
    list_display = ['participant_username', 'instagram_account', 'last_message_time', 'is_read', 'is_archived']
    list_filter = ['is_read', 'is_archived', 'created_at']
    search_fields = ['participant_username', 'participant_name']
    readonly_fields = ['conversation_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Account', {
            'fields': ('instagram_account', 'conversation_id')
        }),
        ('Participant', {
            'fields': ('participant_instagram_id', 'participant_username', 'participant_name', 'participant_profile_pic')
        }),
        ('Status', {
            'fields': ('is_read', 'is_archived', 'last_message_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InstagramMessage)
class InstagramMessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'message_type', 'is_from_business', 'text_preview', 'timestamp']
    list_filter = ['is_from_business', 'message_type', 'timestamp']
    search_fields = ['text', 'conversation__participant_username']
    readonly_fields = ['message_id', 'timestamp', 'created_at']
    
    def text_preview(self, obj):
        return obj.text[:50] if obj.text else '(No text)'
    text_preview.short_description = 'Message'
    
    fieldsets = (
        ('Conversation', {
            'fields': ('conversation', 'message_id')
        }),
        ('Message', {
            'fields': ('is_from_business', 'message_type', 'text', 'media_url')
        }),
        ('Status', {
            'fields': ('is_read', 'is_deleted')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'instagram_account', 'processed', 'received_at', 'processed_at']
    list_filter = ['processed', 'event_type', 'received_at']
    search_fields = ['event_type', 'error_message']
    readonly_fields = ['received_at', 'processed_at', 'raw_data']
    
    fieldsets = (
        ('Event', {
            'fields': ('event_type', 'instagram_account')
        }),
        ('Status', {
            'fields': ('processed', 'processed_at', 'error_message')
        }),
        ('Data', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('received_at',),
            'classes': ('collapse',)
        }),
    )
>>>>>>> dd61877 (feat: changed the way of viewing prices after getting shipengine rates. also removing redudant code)
