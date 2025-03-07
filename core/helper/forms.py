from django.forms import ModelForm
from .models import AssignmentHelper

class AssignmentHelperForm(ModelForm):
    class Meta:
        model = AssignmentHelper
        fields = ['name', 'age', 'address', 'description', 'phone_no', ] 
