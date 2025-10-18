from django.db import models
from core.mixins.models import CommonModel
from django.utils.translation import gettext_lazy as _
from authentication.models import CommonUser

class AssignmentHelper(CommonModel):
    user = models.OneToOneField(CommonUser, on_delete=models.CASCADE, verbose_name=_("User"))
    