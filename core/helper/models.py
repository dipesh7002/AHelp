from django.db import models
from core.mixins.models import CommonModel
from django.utils.translation import gettext_lazy as _
from authentication.models import CommonUser


class Education(CommonModel):
    class Level(models.TextChoices):
        PRIMARY = "pri", "Primary"
        SECONDARY = (
            "sec",
            "Secondary",
        )
        BACHELORS = (
            "bac",
            "Bachelors",
        )
        MASTERS = (
            "mas",
            "Masters",
        )
        PHD = "phd", "PHD"

    class Status(models.IntegerChoices):
        ONGOING = 1, "Ongoing"
        COMPLETED = 2, "Completed"

    level = models.CharField(
        max_length=3, choices=Level.choices, verbose_name=_("Education Level")
    )
    status = models.IntegerField(choices=Status.choices, verbose_name=_("Status"))
    
    def __str__(self):
        return f"{self.level} - {self.status}"


class Subject(CommonModel):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    
    def __str__(self):
        return f"{self.name}" 


class AssignmentHelper(CommonModel):
    class Rating(models.IntegerChoices):
        ONE = 1, "One"
        TWO = 2, "Two"
        THREE = 3, "Three"
        FOUR = 4, "Four"
        FIVE = 5, "Five"

    user = models.OneToOneField(
        CommonUser, on_delete=models.CASCADE, verbose_name=_("User")
    )
    pp = models.ImageField(verbose_name=_("Profile Picture"), upload_to="")
    education = models.ForeignKey(Education, on_delete=models.CASCADE)
    rating = models.IntegerField(null=True, blank=True)

    def __str_(self):
        return f"{self.user__first_name} {self.user__last_name}"