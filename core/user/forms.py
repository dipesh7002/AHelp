from django.contrib.auth.forms import UserCreationForm
from helper.models import AssignmentHelper

class SignupForm(UserCreationForm):
    class Meta:
        model = AssignmentHelper
        fields = ['username',  
            'password1',  
            'password2',  
            'name',
            'age',
            'address',
            'description',
            'phone_no',
            'email',
            'education',
            'profile_picture',
            'experience_years',
            'mastery_subjects',
            'is_active',]