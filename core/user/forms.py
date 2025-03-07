from typing import Any
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from helper.models import AssignmentHelper

class SignupForm(UserCreationForm):
    class Meta:
        model = AssignmentHelper
        fields = '__all__' 
    def save(self, commit=True):
        user = super().save(commit=False)
        assignment_helper = AssignmentHelper(
            user=user  
        )
        if commit:
            user.save()
            assignment_helper.save()
        return user