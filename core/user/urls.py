from django.urls import path, include
from .views import login_user, home, signup_view, logout_user, signUpMiddle
from django.conf import settings
from django.contrib.auth import logout

app_name = 'user'


urlpatterns = [
    path('login/', login_user, name="user login"),
    path('home/', home.as_view(), name="user home"),
    path('signup/', signup_view, name="user signup"),
      # path('check/', include('social_django.urls', namespace='social')),
  path('logout/', logout_user, name="user logout"),
#     name='logout'),
path('signupmiddle/', signUpMiddle.as_view(), name='user signupmiddle')
]