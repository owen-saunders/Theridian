"""
API views for the Django REST Framework application.
"""
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q, QuerySet
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
import structlog

from .models import APIKey, DataSource, ETLJob, MetricData
from .serializers import (
    APIKeySerializer,
    DataSourceSerializer,
    ETLJobSerializer,
    MetricDataSerializer,
    ETLJobCreateSerializer,
    HealthCheckSerializer,
)
from .filters import ETLJobFilter, MetricDataFilter
from .tasks import process_etl_job

logger = structlog.get_logger(__name__)


class APIKeyListCreateView(generics.ListCreateAPIView):
    """
    List and create API keys for the authenticated user.
    """

    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "last_used_at"]
    ordering = ["-created_at"]

    def get_queryset(self):  # type: ignore[override]
        return APIKey.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info("Creating new API key", user=self.request.user.username)
        serializer.save(user=self.request.user)


class APIKeyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an API key.
    """

    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        return APIKey.objects.filter(user=self.request.user)


class DataSourceListCreateView(generics.ListCreateAPIView):
    """
    List and create data sources.
    """

    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["source_type", "is_active"]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "source_type"]
    ordering = ["name"]

    def perform_create(self, serializer):
        logger.info("Creating new data source", name=serializer.validated_data["name"])
        serializer.save()


class DataSourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a data source.
    """

    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]


class ETLJobListCreateView(generics.ListCreateAPIView):
    """
    List and create ETL jobs.
    """

    queryset = ETLJob.objects.select_related("data_source").all()
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ETLJobFilter
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "started_at", "completed_at", "status"]
    ordering = ["-created_at"]

    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == "POST":
            return ETLJobCreateSerializer
        return ETLJobSerializer

    def perform_create(self, serializer):
        logger.info("Creating new ETL job", name=serializer.validated_data["name"])
        job = serializer.save()
        # Trigger the ETL job processing
        process_etl_job.delay(str(job.id))  # type: ignore


class ETLJobDetailView(generics.RetrieveAPIView):
    """
    Retrieve an ETL job.
    """

    queryset = ETLJob.objects.select_related("data_source").all()
    serializer_class = ETLJobSerializer
    permission_classes = [IsAuthenticated]


class ETLJobRetryView(APIView):
    """
    Retry a failed ETL job.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Retry a failed ETL job", responses={200: ETLJobSerializer}
    )
    def post(self, request, pk):
        try:
            job = ETLJob.objects.get(pk=pk)
            if job.status not in ["failed", "cancelled"]:
                return Response(
                    {"error": "Only failed or cancelled jobs can be retried"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Reset job status
            job.status = "pending"
            job.error_message = ""
            job.started_at = None
            job.completed_at = None
            job.save()

            # Trigger the job again
            process_etl_job.delay(str(job.id))  # type: ignore

            logger.info("Retrying ETL job", job_id=str(job.id))

            serializer = ETLJobSerializer(job)
            return Response(serializer.data)

        except ETLJob.DoesNotExist:
            return Response(
                {"error": "ETL job not found"}, status=status.HTTP_404_NOT_FOUND
            )


class MetricDataListCreateView(generics.ListCreateAPIView):
    """
    List and create metric data.
    """

    queryset = MetricData.objects.all()
    serializer_class = MetricDataSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = MetricDataFilter
    ordering_fields = ["timestamp", "metric_name", "metric_value"]
    ordering = ["-timestamp"]

    def perform_create(self, serializer):
        logger.debug(
            "Recording metric", metric_name=serializer.validated_data["metric_name"]
        )
        serializer.save()


class DashboardStatsView(APIView):
    """
    Dashboard statistics endpoint.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Get dashboard statistics",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "total_data_sources": {"type": "integer"},
                    "active_data_sources": {"type": "integer"},
                    "total_etl_jobs": {"type": "integer"},
                    "running_jobs": {"type": "integer"},
                    "completed_jobs_today": {"type": "integer"},
                    "failed_jobs_today": {"type": "integer"},
                    "recent_jobs": {"type": "array", "items": {"type": "object"}},
                },
            }
        },
    )
    def get(self, request):
        today = timezone.now().date()

        stats = {
            "total_data_sources": DataSource.objects.count(),
            "active_data_sources": DataSource.objects.filter(is_active=True).count(),
            "total_etl_jobs": ETLJob.objects.count(),
            "running_jobs": ETLJob.objects.filter(status="running").count(),
            "completed_jobs_today": ETLJob.objects.filter(
                status="completed", completed_at__date=today
            ).count(),
            "failed_jobs_today": ETLJob.objects.filter(
                status="failed", completed_at__date=today
            ).count(),
        }

        # Recent jobs
        recent_jobs = ETLJob.objects.select_related("data_source").order_by(
            "-created_at"
        )[:5]
        stats["recent_jobs"] = ETLJobSerializer(recent_jobs, many=True).data

        logger.info("Dashboard stats requested", user=request.user.username)
        return Response(stats)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint.
    """
    from django.db import connection
    from django.core.cache import cache
    import redis

    health_data = {
        "status": "healthy",
        "timestamp": timezone.now(),
        "version": "1.0.0",
        "database": False,
        "cache": False,
        "celery": False,
    }

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_data["database"] = True
    except Exception as e:
        health_data["status"] = "unhealthy"
        logger.error("Database health check failed", error=str(e))

    # Check cache
    try:
        cache.set("health_check", "ok", 30)
        cache.get("health_check")
        health_data["cache"] = True
    except Exception as e:
        health_data["status"] = "unhealthy"
        logger.error("Cache health check failed", error=str(e))

    # Check Celery
    try:
        from core.celery import app

        inspect = app.control.inspect()
        stats = inspect.stats()
        health_data["celery"] = bool(stats)
    except Exception as e:
        logger.error("Celery health check failed", error=str(e))

    serializer = HealthCheckSerializer(health_data)
    return Response(serializer.data)
