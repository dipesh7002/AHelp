from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class CommonModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Education(CommonModel):
    class Level(models.TextChoices):
        PRIMARY = "pri", "Primary"
        SECONDARY = "sec", "Secondary"
        BACHELORS = "bac", "Bachelors"
        MASTERS = "mas", "Masters"
        PHD = "phd", "PHD"

    class Status(models.IntegerChoices):
        ONGOING = 1, "Ongoing"
        COMPLETED = 2, "Completed"

    level = models.CharField(
        max_length=3,
        choices=Level.choices,
        verbose_name=_("Education Level"),
    )
    status = models.IntegerField(choices=Status.choices, verbose_name=_("Status"))

    class Meta:
        unique_together = ("level", "status")

    def __str__(self):
        return f"{self.get_level_display()} - {self.get_status_display()}"


class Subject(CommonModel):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))

    def __str__(self):
        return self.name


class WriterProfile(CommonModel):
    class Rating(models.IntegerChoices):
        ONE = 1, "One"
        TWO = 2, "Two"
        THREE = 3, "Three"
        FOUR = 4, "Four"
        FIVE = 5, "Five"

    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="writer_profile",
        verbose_name=_("User"),
    )
    profile_picture = models.ImageField(
        verbose_name=_("Profile Picture"),
        upload_to="writers/profile-pictures/",
        null=True,
        blank=True,
    )
    cv = models.FileField(
        verbose_name=_("CV"),
        upload_to="writers/cvs/",
        null=True,
        blank=True,
    )
    education = models.ForeignKey(
        Education,
        on_delete=models.PROTECT,
        related_name="writer_profiles",
    )
    subjects = models.ManyToManyField(Subject, related_name="writer_profiles", blank=True)
    rating = models.IntegerField(choices=Rating.choices, null=True, blank=True)
    is_available = models.BooleanField(default=True, verbose_name=_("Is Available"))
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.full_name or self.user.email
