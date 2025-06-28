"""
API models for the Django REST Framework application.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
import uuid


class TimeStampedModel(models.Model):
    """
    Abstract base class with self-updating created and modified fields.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class APIKey(TimeStampedModel):
    """
    API Key model for authentication.
    """

    name = models.CharField(max_length=100, validators=[MinLengthValidator(3)])
    key = models.CharField(max_length=64, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:  # type: ignore
        db_table = "api_keys"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class DataSource(TimeStampedModel):
    """
    Data source model for ETL processes.
    """

    SOURCE_TYPES = [
        ("database", "Database"),
        ("api", "API"),
        ("file", "File"),
        ("stream", "Stream"),
    ]

    name = models.CharField(max_length=100, unique=True)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    connection_string = models.TextField(
        help_text="Connection details for the data source"
    )
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:  # type: ignore
        db_table = "data_sources"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class ETLJob(TimeStampedModel):
    """
    ETL job tracking model.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    data_source = models.ForeignKey(
        DataSource, on_delete=models.CASCADE, related_name="etl_jobs"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    records_processed = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    configuration = models.JSONField(default=dict)

    class Meta:  # type: ignore
        db_table = "etl_jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.status}"

    @property
    def duration(self):
        """Calculate job duration if both start and end times are available."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class MetricData(TimeStampedModel):
    """
    Model for storing application metrics.
    """

    metric_name = models.CharField(max_length=100, db_index=True)
    metric_value = models.FloatField()
    metric_type = models.CharField(max_length=20, default="gauge")
    labels = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:  # type: ignore
        db_table = "metrics_data"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["metric_name", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value}"
