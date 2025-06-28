"""
Serializers for the API application.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import APIKey, DataSource, ETLJob, MetricData


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class APIKeySerializer(serializers.ModelSerializer):
    """
    Serializer for APIKey model.
    """

    user = UserSerializer(read_only=True)

    class Meta:
        model = APIKey
        fields = [
            "id",
            "name",
            "key",
            "user",
            "is_active",
            "expires_at",
            "last_used_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "key", "last_used_at", "created_at", "updated_at"]

    def create(self, validated_data):
        """
        Create a new API key with auto-generated key.
        """
        import secrets

        validated_data["key"] = secrets.token_urlsafe(32)
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class DataSourceSerializer(serializers.ModelSerializer):
    """
    Serializer for DataSource model.
    """

    etl_jobs_count = serializers.SerializerMethodField()

    class Meta:
        model = DataSource
        fields = [
            "id",
            "name",
            "source_type",
            "connection_string",
            "is_active",
            "metadata",
            "etl_jobs_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {"connection_string": {"write_only": True}}

    def get_etl_jobs_count(self, obj):
        """
        Get the count of ETL jobs for this data source.
        """
        return obj.etl_jobs.count()

    def validate_name(self, value):
        """
        Validate that the name is unique (case-insensitive).
        """
        if DataSource.objects.filter(name__iexact=value).exists():
            if self.instance and self.instance.name.lower() == value.lower():
                return value
            raise serializers.ValidationError(
                "A data source with this name already exists."
            )
        return value


class ETLJobSerializer(serializers.ModelSerializer):
    """
    Serializer for ETLJob model.
    """

    data_source = DataSourceSerializer(read_only=True)
    data_source_id = serializers.UUIDField(write_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = ETLJob
        fields = [
            "id",
            "name",
            "status",
            "data_source",
            "data_source_id",
            "started_at",
            "completed_at",
            "records_processed",
            "error_message",
            "configuration",
            "duration",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "started_at",
            "completed_at",
            "records_processed",
            "error_message",
            "created_at",
            "updated_at",
        ]

    def get_duration(self, obj):
        """
        Get the duration of the ETL job in seconds.
        """
        duration = obj.duration
        return duration.total_seconds() if duration else None

    def validate_data_source_id(self, value):
        """
        Validate that the data source exists and is active.
        """
        try:
            data_source = DataSource.objects.get(id=value)
            if not data_source.is_active:
                raise serializers.ValidationError(
                    "Cannot create job for inactive data source."
                )
            return value
        except DataSource.DoesNotExist:
            raise serializers.ValidationError("Data source does not exist.")


class MetricDataSerializer(serializers.ModelSerializer):
    """
    Serializer for MetricData model.
    """

    class Meta:
        model = MetricData
        fields = [
            "id",
            "metric_name",
            "metric_value",
            "metric_type",
            "labels",
            "timestamp",
            "created_at",
        ]
        read_only_fields = ["id", "timestamp", "created_at"]

    def validate_metric_type(self, value):
        """
        Validate metric type.
        """
        valid_types = ["counter", "gauge", "histogram", "summary"]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Metric type must be one of: {', '.join(valid_types)}"
            )
        return value


class ETLJobCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating ETL jobs.
    """

    class Meta:
        model = ETLJob
        fields = ["name", "data_source", "configuration"]

    def create(self, validated_data):
        """
        Create ETL job and trigger processing.
        """
        job = super().create(validated_data)
        # Import here to avoid circular imports
        from .tasks import process_etl_job

        process_etl_job.delay(str(job.id))  # type: ignore
        return job


class HealthCheckSerializer(serializers.Serializer):
    """
    Serializer for health check responses.
    """

    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    version = serializers.CharField()
    database = serializers.BooleanField()
    cache = serializers.BooleanField()
    celery = serializers.BooleanField()

    def to_representation(self, instance):
        """
        Override to add custom health check data.
        """
        data = super().to_representation(instance)
        data["uptime"] = getattr(instance, "uptime", None)
        return data
