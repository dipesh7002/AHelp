from django.urls import path, include
from .views import login_user, home, signup_view, logout_user, SignUp, HelperPage, SignUpHelper
from django.conf import settings
from django.contrib.auth import logout

app_name = 'user'


urlpatterns = [
  path('login/', login_user, name="user login"),
  path('home/', home.as_view(), name="user home"),
  path('logout/', logout_user, name="user logout"),
  path('signup_helper/', SignUp.as_view(), name='user middle'),
  path('user/helper', SignUpHelper.as_view(), name = 'user helper_sign'),
  path('user/helper', HelperPage.as_view(), name = 'helper page'),
]