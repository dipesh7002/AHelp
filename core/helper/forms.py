from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import AssignmentHelper

class AssignmentHelperForm(ModelForm):
    class Meta:
        model = AssignmentHelper 
        exclude = ['user', 'total_assignments_done', 'average_rating', 'is_active']

class UserSignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']