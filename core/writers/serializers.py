from rest_framework import serializers

from .models import (
    Education,
    Service,
    ServiceCategory,
    Subject,
    WriterFAQ,
    WriterPerk,
    WriterProfile,
    WriterReview,
)


class EducationSerializer(serializers.ModelSerializer):
    level_display = serializers.CharField(source="get_level_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Education
        fields = ("id", "level", "level_display", "status", "status_display")


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ("id", "name")


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ("id", "name", "sort_order")


class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_sort_order = serializers.IntegerField(source="category.sort_order", read_only=True)

    class Meta:
        model = Service
        fields = ("id", "name", "category", "category_name", "category_sort_order")


class WriterFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = WriterFAQ
        fields = ("id", "question", "answer", "sort_order")


class WriterPerkSerializer(serializers.ModelSerializer):
    class Meta:
        model = WriterPerk
        fields = ("id", "text", "sort_order")


class WriterReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()
    reviewer_picture = serializers.SerializerMethodField()

    class Meta:
        model = WriterReview
        fields = ("id", "rating", "comment", "reviewer_name", "reviewer_picture", "created_at")
        read_only_fields = ("id", "reviewer_name", "reviewer_picture", "created_at")

    def get_reviewer_name(self, obj):
        if not obj.reviewer:
            return "Anonymous"
        return obj.reviewer.full_name or obj.reviewer.email

    def get_reviewer_picture(self, obj):
        if not obj.reviewer or not getattr(obj.reviewer, "profile_picture", None):
            return None
        request = self.context.get("request")
        url = obj.reviewer.profile_picture.url
        return request.build_absolute_uri(url) if request else url


class WriterCardSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    work_image = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = WriterProfile
        fields = (
            "id",
            "full_name",
            "profile_picture",
            "work_image",
            "headline",
            "bio",
            "rating",
            "rating_count",
            "is_available",
            "is_favorited",
            "starting_price",
            "delivery_days_min",
            "delivery_days_max",
        )

    def _absolute_url(self, file_field):
        if not file_field:
            return None
        request = self.context.get("request")
        url = file_field.url
        return request.build_absolute_uri(url) if request else url

    def get_full_name(self, obj):
        return obj.user.full_name or obj.user.email

    def get_profile_picture(self, obj):
        return self._absolute_url(obj.user.profile_picture)

    def get_work_image(self, obj):
        first = next(iter(obj.work_images.all()), None)
        return self._absolute_url(first.image) if first else None

    def get_rating(self, obj):
        annotated = getattr(obj, "_avg_rating", None)
        if annotated is not None:
            return round(annotated, 1)
        value = obj.rating
        return round(value, 1) if value is not None else None

    def get_rating_count(self, obj):
        annotated = getattr(obj, "_review_count", None)
        if annotated is not None:
            return annotated
        return obj.rating_count

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        favorited_ids = self.context.get("favorited_writer_ids")
        if favorited_ids is not None:
            return obj.id in favorited_ids
        return obj.favorited_by.filter(user=request.user).exists()


class WriterDetailSerializer(WriterCardSerializer):
    services = serializers.SerializerMethodField()
    work_images = serializers.SerializerMethodField()
    location = serializers.CharField(source="user.location", read_only=True)
    languages = serializers.CharField(read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    faqs = WriterFAQSerializer(many=True, read_only=True)
    perks = WriterPerkSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    member_since = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta(WriterCardSerializer.Meta):
        fields = WriterCardSerializer.Meta.fields + (
            "email",
            "location",
            "languages",
            "services",
            "work_images",
            "faqs",
            "perks",
            "reviews",
            "member_since",
        )

    def get_services(self, obj):
        return [{"id": s.id, "name": s.name} for s in obj.services.all()]

    def get_work_images(self, obj):
        return [self._absolute_url(img.image) for img in obj.work_images.all()]

    def get_reviews(self, obj):
        recent = obj.reviews.all()[:5]
        return WriterReviewSerializer(recent, many=True, context=self.context).data
