from django.db.models import Avg, Count, Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    Education,
    FavoriteWriter,
    Service,
    ServiceCategory,
    Subject,
    WriterFAQ,
    WriterProfile,
    WriterReview,
    WriterWorkImage,
)
from .serializers import (
    EducationSerializer,
    ServiceCategorySerializer,
    ServiceSerializer,
    SubjectSerializer,
    WriterCardSerializer,
    WriterDetailSerializer,
    WriterFAQSerializer,
    WriterReviewSerializer,
)


class EducationListView(ListAPIView):
    permission_classes = [AllowAny]
    queryset = Education.objects.all().order_by("level", "status")
    serializer_class = EducationSerializer
    pagination_class = None


class SubjectListView(ListAPIView):
    permission_classes = [AllowAny]
    queryset = Subject.objects.all().order_by("name")
    serializer_class = SubjectSerializer
    pagination_class = None


class ServiceListView(ListAPIView):
    permission_classes = [AllowAny]
    queryset = Service.objects.select_related("category").all()
    serializer_class = ServiceSerializer
    pagination_class = None


class ServiceCategoryListView(ListAPIView):
    permission_classes = [AllowAny]
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    pagination_class = None


def _approved_writers_queryset():
    return (
        WriterProfile.objects
        .filter(approval_status=WriterProfile.ApprovalStatus.APPROVED)
        .select_related("user")
        .annotate(_avg_rating=Avg("reviews__rating"), _review_count=Count("reviews"))
        .prefetch_related(
            Prefetch("work_images", queryset=WriterWorkImage.objects.order_by("sort_order", "created_at"))
        )
    )


class WriterCardListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = WriterCardSerializer
    pagination_class = None

    def get_queryset(self):
        return _approved_writers_queryset().order_by("-is_available", "-_avg_rating", "-updated_at")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.request.user.is_authenticated:
            ctx["favorited_writer_ids"] = set(
                FavoriteWriter.objects.filter(user=self.request.user).values_list("writer_profile_id", flat=True)
            )
        return ctx


class WriterDetailView(RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = WriterDetailSerializer

    def get_queryset(self):
        return _approved_writers_queryset().prefetch_related(
            "services",
            "faqs",
            "perks",
            Prefetch("reviews", queryset=WriterReview.objects.select_related("reviewer")),
        )


class WriterReviewListCreateView(ListCreateAPIView):
    serializer_class = WriterReviewSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_writer(self):
        return get_object_or_404(
            WriterProfile,
            pk=self.kwargs["pk"],
            approval_status=WriterProfile.ApprovalStatus.APPROVED,
        )

    def get_queryset(self):
        return (
            WriterReview.objects
            .filter(writer_profile_id=self.kwargs["pk"])
            .select_related("reviewer")
        )

    def create(self, request, *args, **kwargs):
        writer = self.get_writer()
        if writer.user_id == request.user.id:
            return Response(
                {"detail": "You cannot review your own profile."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if WriterReview.objects.filter(writer_profile=writer, reviewer=request.user).exists():
            return Response(
                {"detail": "You have already reviewed this writer."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(writer_profile=writer, reviewer=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WriterFAQListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = WriterFAQSerializer
    pagination_class = None

    def get_queryset(self):
        return WriterFAQ.objects.filter(writer_profile_id=self.kwargs["pk"])


class FavoriteWriterListCreateView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WriterCardSerializer
    pagination_class = None

    def get_queryset(self):
        favorited_ids = FavoriteWriter.objects.filter(user=self.request.user).values_list(
            "writer_profile_id", flat=True
        )
        return (
            _approved_writers_queryset()
            .filter(id__in=list(favorited_ids))
            .order_by("-is_available", "-_avg_rating", "-updated_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["favorited_writer_ids"] = set(
            FavoriteWriter.objects.filter(user=self.request.user).values_list("writer_profile_id", flat=True)
        )
        return ctx

    def post(self, request):
        if request.user.role != request.user.Role.USER:
            return Response(
                {"detail": "Only users can save writers."},
                status=status.HTTP_403_FORBIDDEN,
            )
        writer_id = request.data.get("writer_profile_id")
        if not writer_id:
            return Response(
                {"detail": "writer_profile_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        writer = get_object_or_404(
            WriterProfile,
            pk=writer_id,
            approval_status=WriterProfile.ApprovalStatus.APPROVED,
        )
        FavoriteWriter.objects.get_or_create(user=request.user, writer_profile=writer)
        return Response({"writer_profile_id": writer.id, "is_favorited": True}, status=status.HTTP_201_CREATED)


class FavoriteWriterDestroyView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        FavoriteWriter.objects.filter(user=request.user, writer_profile_id=pk).delete()
        return Response({"writer_profile_id": pk, "is_favorited": False}, status=status.HTTP_200_OK)
