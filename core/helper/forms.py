from django.forms import ModelForm
from .models import AssignmentHelper

class AssignmentHelperForm(ModelForm):
    class Meta:
        model = AssignmentHelper
        fields = '__all__'