from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from core.mixins.models import CommonModel
from django.utils.translation import gettext_lazy as _


class BaseUser(CommonModel, AbstractBaseUser):
    # aa = models.
    # ad = mo
    # email = models
    pass


class CommonUser(AbstractBaseUser, CommonModel):
    class Gender:
        MALE = 1, _("Male")
        FEMALE = 2, _("Female")
        OTHER = 3, _("Other")

    first_name = models.CharField(max_length=50, verbose_name=_("First Name"))
    middle_name = models.CharField(
        max_length=50, null=True, blank=True, verbose_name=_("Middle Name")
    )
    last_name = models.CharField(max_length=50, verbose_name=_("Last Name"))
    email = models.EmailField(unique=True, verbose_name=_("email"))
    image = models.ImageField()
    is_staff = models.BooleanField(default=False, verbose_name=_("Is Staff"))
    REQUIRED_FIELDS = []
    USERNAME_FIELD = "email"
