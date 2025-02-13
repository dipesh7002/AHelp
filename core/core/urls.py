from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")),
    path('', include('home.urls', namespace='home')),
    path('user/', include('user.urls')),
    path('auth/', include('social_django.urls', namespace='social')),
    path('client/', include('client.urls', namespace='client')),
    path('helper/', include('helper.urls', namespace='helper')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# http://localhost:8000/auth/login/google-oauth2/
