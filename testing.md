# Instagram Chat Integration - Testing & Deployment Guide

## Pre-Deployment Checklist

### 1. Instagram Business Account Requirements
- ✅ Convert personal Instagram to Business Account
- ✅ Link Instagram Business Account to a Facebook Page
- ✅ Ensure you're admin of the Facebook Page

### 2. Facebook App Configuration

#### Create Facebook App
```
1. Go to https://developers.facebook.com/
2. Click "Create App"
3. Choose "Business" type
4. Fill in app details:
   - App Name: "Your App Name"
   - App Contact Email: your@email.com
5. Click "Create App"
```

#### Add Instagram Product
```
1. In your app dashboard, click "Add Product"
2. Find "Instagram" and click "Set Up"
3. Complete Instagram Basic Display setup
```

#### Configure App Settings
```
1. Go to Settings > Basic
2. Add App Domains: yourdomain.com
3. Add Privacy Policy URL
4. Add Terms of Service URL
5. Save changes
```

#### Configure OAuth Settings
```
1. Go to Instagram > Basic Display
2. Add OAuth Redirect URI:
   - https://yourdomain.com/api/instagram/callback/
3. Add Deauthorize Callback URL
4. Add Data Deletion Request URL
5. Save changes
```

### 3. Webhook Configuration

#### Set Up Webhook
```
1. In Facebook App, go to Products > Webhooks
2. Click "Edit" on Instagram
3. Add Callback URL: https://yourdomain.com/api/instagram/webhook/
4. Add Verify Token: (use the same token from settings.py)
5. Subscribe to fields:
   - messages
   - messaging_postbacks
   - message_echoes
6. Save and verify
```

#### Test Webhook
```bash
# Test webhook verification
curl "https://yourdomain.com/api/instagram/webhook/?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test123"

# Should return: test123
```

## Local Development Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create `.env` file:
```env
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_app_secret
INSTAGRAM_REDIRECT_URI=http://localhost:8000/api/instagram/callback/
INSTAGRAM_WEBHOOK_VERIFY_TOKEN=your_random_token_12345
```

### 3. Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser
```bash
python manage.py createsuperuser
```

### 5. Run Development Server
```bash
python manage.py runserver
```

### 6. Test with ngrok (for webhooks)
Since webhooks need a public URL, use ngrok for local testing:
```bash
# Install ngrok
npm install -g ngrok

# Start ngrok
ngrok http 8000

# Update Facebook App webhook URL with ngrok URL
# Example: https://abc123.ngrok.io/api/instagram/webhook/
```

## Testing Flow

### Test 1: OAuth Connection
```
1. Navigate to: http://localhost:8000/api/instagram/connect/
2. Click authorization URL
3. Log in with Facebook account
4. Select permissions
5. Get redirected to callback URL
6. Should see list of Facebook pages
7. Select a page to complete connection
8. Verify connection in admin panel
```

### Test 2: Sync Conversations
```python
# In Django shell
python manage.py shell

from your_app.models import InstagramAccount
from your_app.services import InstagramDataSync

account = InstagramAccount.objects.first()
sync = InstagramDataSync(account)
conversations = sync.sync_conversations()
print(f"Synced {len(conversations)} conversations")
```

### Test 3: Send Message via API
```bash
curl -X POST http://localhost:8000/api/instagram/send-message/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "CONVERSATION_ID",
    "message_text": "Hello from Django!"
  }'
```

### Test 4: Receive Webhook Event
```bash
# Send test message from Instagram to your business account
# Check webhook logs in admin panel
# Verify message appears in database
```

## API Endpoints Reference

### Connection Endpoints
```
GET  /api/instagram/connect/          - Get authorization URL
GET  /api/instagram/callback/         - OAuth callback
POST /api/instagram/complete/         - Complete connection with page selection
```

### Account Endpoints
```
GET  /api/instagram/accounts/         - List connected accounts
GET  /api/instagram/accounts/{id}/    - Get account details
POST /api/instagram/accounts/{id}/sync/ - Manually sync conversations
POST /api/instagram/accounts/{id}/disconnect/ - Disconnect account
```

### Conversation Endpoints
```
GET  /api/instagram/conversations/    - List conversations
GET  /api/instagram/conversations/{id}/ - Get conversation with messages
POST /api/instagram/conversations/{id}/mark_read/ - Mark as read
POST /api/instagram/conversations/{id}/archive/ - Archive conversation
```

### Messaging Endpoints
```
POST /api/instagram/send-message/     - Send text message
POST /api/instagram/send-media/       - Send media message
```

### Webhook Endpoint
```
GET  /api/instagram/webhook/          - Webhook verification
POST /api/instagram/webhook/          - Receive webhook events
```

## Production Deployment

### 1. Environment Setup
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
INSTAGRAM_APP_ID=production_app_id
INSTAGRAM_APP_SECRET=production_app_secret
INSTAGRAM_REDIRECT_URI=https://yourdomain.com/api/instagram/callback/
INSTAGRAM_WEBHOOK_CALLBACK_URL=https://yourdomain.com/api/instagram/webhook/
```

### 2. HTTPS Configuration
- Instagram API requires HTTPS for webhooks
- Use Let's Encrypt or your hosting provider's SSL

### 3. Database
```bash
# Use PostgreSQL in production
pip install psycopg2-binary

# Update settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 4. Static Files
```bash
python manage.py collectstatic
```

### 5. Process Manager (Gunicorn)
```bash
pip install gunicorn

gunicorn your_project.wsgi:application --bind 0.0.0.0:8000
```

### 6. Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/staticfiles/;
    }
}
```

### 7. Background Tasks (Celery - Optional)
For syncing messages in background:
```bash
pip install celery redis

# In settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'

# Start celery worker
celery -A your_project worker -l info
```

## Monitoring & Maintenance

### Check Token Expiry
```python
# Create management command
python manage.py check_token_expiry

# Schedule with cron to run daily
0 0 * * * /path/to/venv/bin/python /path/to/manage.py check_token_expiry
```

### Monitor Webhook Events
```
1. Check WebhookEvent model in admin
2. Monitor unprocessed events
3. Check error messages
4. Retry failed events if needed
```

### Sync Schedule
Set up periodic sync:
```python
# In celery beat schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'sync-instagram-conversations': {
        'task': 'your_app.tasks.sync_all_conversations',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
```

## Common Issues & Solutions

### Issue 1: Webhook Not Receiving Events
**Solution:**
- Verify webhook is subscribed in Facebook App
- Check webhook URL is accessible (test with curl)
- Ensure HTTPS is working
- Check webhook verify token matches

### Issue 2: Token Expired
**Solution:**
- Users need to reconnect their account
- Implement automatic token refresh if possible
- Show notification to user when token expires

### Issue 3: Conversation Not Syncing
**Solution:**
- Check API permissions are granted
- Verify Instagram account is Business type
- Check API rate limits
- Review error logs

### Issue 4: Messages Not Sending
**Solution:**
- Verify recipient_id is correct Instagram Scoped ID
- Check if 24-hour messaging window applies
- Ensure message format is valid
- Check API error response

## Facebook App Review (Production)

Before going live, you need Facebook to review your app:

### Required for Review:
1. App Privacy Policy URL
2. App Terms of Service URL
3. Detailed description of how you use Instagram data
4. Screencast showing app functionality
5. Test credentials for review team

### Permissions to Request:
- instagram_basic
- instagram_manage_messages
- pages_show_list
- pages_read_engagement
- pages_manage_metadata

### Review Timeline:
- Usually 3-5 business days
- Be prepared to answer questions
- Have test account ready

## Support & Resources

### Official Documentation:
- Instagram Graph API: https://developers.facebook.com/docs/instagram-api
- Messenger Platform: https://developers.facebook.com/docs/messenger-platform

### Useful Tools:
- Graph API Explorer: https://developers.facebook.com/tools/explorer/
- Webhook Testing: https://developers.facebook.com/tools/webhooks/

### Community:
- Stack Overflow: [instagram-graph-api]
- Facebook Developer Community