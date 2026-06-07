from django.conf import settings
from django.db import models
from django.db.models import Avg
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


class ServiceCategory(CommonModel):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_("Sort Order"))

    class Meta:
        ordering = ("sort_order", "name")
        verbose_name_plural = "Service categories"

    def __str__(self):
        return self.name


class Service(CommonModel):
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        related_name="services",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))

    class Meta:
        ordering = ("category__sort_order", "category__name", "name")

    def __str__(self):
        return self.name


class WriterProfile(CommonModel):
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
    services = models.ManyToManyField(Service, related_name="writer_profiles", blank=True)
    headline = models.CharField(max_length=160, blank=True, verbose_name=_("Headline"))
    bio = models.TextField(blank=True, verbose_name=_("Bio"))
    languages = models.CharField(max_length=255, blank=True, verbose_name=_("Languages"))
    starting_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Starting Price"),
    )
    delivery_days_min = models.PositiveSmallIntegerField(null=True, blank=True)
    delivery_days_max = models.PositiveSmallIntegerField(null=True, blank=True)
    is_available = models.BooleanField(default=True, verbose_name=_("Is Available"))
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.full_name or self.user.email

    @property
    def rating(self):
        return self.reviews.aggregate(avg=Avg("rating"))["avg"]

    @property
    def rating_count(self):
        return self.reviews.count()


class WriterWorkImage(CommonModel):
    writer_profile = models.ForeignKey(
        WriterProfile,
        on_delete=models.CASCADE,
        related_name="work_images",
    )
    image = models.ImageField(upload_to="writers/work-images/")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "created_at")

    def __str__(self):
        return f"Work image for {self.writer_profile}"


class WriterReview(CommonModel):
    class Rating(models.IntegerChoices):
        ONE = 1, "One"
        TWO = 2, "Two"
        THREE = 3, "Three"
        FOUR = 4, "Four"
        FIVE = 5, "Five"

    writer_profile = models.ForeignKey(
        WriterProfile,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="writer_reviews",
    )
    rating = models.IntegerField(choices=Rating.choices)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("writer_profile", "reviewer"),
                name="unique_review_per_reviewer",
            ),
        ]

    def __str__(self):
        return f"{self.rating}★ for {self.writer_profile}"


class WriterPerk(CommonModel):
    writer_profile = models.ForeignKey(
        WriterProfile,
        on_delete=models.CASCADE,
        related_name="perks",
    )
    text = models.CharField(max_length=120)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "created_at")

    def __str__(self):
        return self.text


class FavoriteWriter(CommonModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_writers",
    )
    writer_profile = models.ForeignKey(
        WriterProfile,
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "writer_profile"),
                name="unique_favorite_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.user} ♥ {self.writer_profile}"


class WriterFAQ(CommonModel):
    writer_profile = models.ForeignKey(
        WriterProfile,
        on_delete=models.CASCADE,
        related_name="faqs",
    )
    question = models.CharField(max_length=255)
    answer = models.TextField()
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "created_at")
        verbose_name = "Writer FAQ"
        verbose_name_plural = "Writer FAQs"

    def __str__(self):
        return self.question
