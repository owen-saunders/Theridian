"""
Django filters for the API application.
"""
import django_filters
from django.db.models import Q
from .models import ETLJob, MetricData


class ETLJobFilter(django_filters.FilterSet):
    """
    Filter for ETL jobs with advanced filtering options.
    """

    status = django_filters.MultipleChoiceFilter(
        choices=ETLJob.STATUS_CHOICES,
        help_text="Filter by job status (can select multiple)",
    )

    data_source = django_filters.UUIDFilter(
        field_name="data_source__id", help_text="Filter by data source ID"
    )

    data_source_name = django_filters.CharFilter(
        field_name="data_source__name",
        lookup_expr="icontains",
        help_text="Filter by data source name (case-insensitive partial match)",
    )

    created_after = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        help_text="Filter jobs created after this datetime",
    )

    created_before = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        help_text="Filter jobs created before this datetime",
    )

    started_after = django_filters.DateTimeFilter(
        field_name="started_at",
        lookup_expr="gte",
        help_text="Filter jobs started after this datetime",
    )

    started_before = django_filters.DateTimeFilter(
        field_name="started_at",
        lookup_expr="lte",
        help_text="Filter jobs started before this datetime",
    )

    completed_after = django_filters.DateTimeFilter(
        field_name="completed_at",
        lookup_expr="gte",
        help_text="Filter jobs completed after this datetime",
    )

    completed_before = django_filters.DateTimeFilter(
        field_name="completed_at",
        lookup_expr="lte",
        help_text="Filter jobs completed before this datetime",
    )

    min_records = django_filters.NumberFilter(
        field_name="records_processed",
        lookup_expr="gte",
        help_text="Filter jobs with at least this many records processed",
    )

    max_records = django_filters.NumberFilter(
        field_name="records_processed",
        lookup_expr="lte",
        help_text="Filter jobs with at most this many records processed",
    )

    has_errors = django_filters.BooleanFilter(
        method="filter_has_errors", help_text="Filter jobs that have error messages"
    )

    class Meta:
        model = ETLJob
        fields = {
            "name": ["exact", "icontains"],
        }

    def filter_has_errors(self, queryset, name, value):
        """
        Filter jobs based on whether they have error messages.
        """
        if value:
            return queryset.exclude(Q(error_message="") | Q(error_message__isnull=True))
        else:
            return queryset.filter(Q(error_message="") | Q(error_message__isnull=True))


class MetricDataFilter(django_filters.FilterSet):
    """
    Filter for metric data with time-based and value-based filtering.
    """

    metric_name = django_filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by metric name (case-insensitive partial match)",
    )

    metric_type = django_filters.ChoiceFilter(
        choices=[
            ("counter", "Counter"),
            ("gauge", "Gauge"),
            ("histogram", "Histogram"),
            ("summary", "Summary"),
        ],
        help_text="Filter by metric type",
    )

    timestamp_after = django_filters.DateTimeFilter(
        field_name="timestamp",
        lookup_expr="gte",
        help_text="Filter metrics recorded after this datetime",
    )

    timestamp_before = django_filters.DateTimeFilter(
        field_name="timestamp",
        lookup_expr="lte",
        help_text="Filter metrics recorded before this datetime",
    )

    min_value = django_filters.NumberFilter(
        field_name="metric_value",
        lookup_expr="gte",
        help_text="Filter metrics with value greater than or equal to this",
    )

    max_value = django_filters.NumberFilter(
        field_name="metric_value",
        lookup_expr="lte",
        help_text="Filter metrics with value less than or equal to this",
    )

    has_labels = django_filters.BooleanFilter(
        method="filter_has_labels", help_text="Filter metrics that have labels"
    )

    label_key = django_filters.CharFilter(
        method="filter_label_key",
        help_text="Filter metrics that have a specific label key",
    )

    label_value = django_filters.CharFilter(
        method="filter_label_value",
        help_text="Filter metrics that have a specific label value (use with label_key)",
    )

    class Meta:
        model = MetricData
        fields = []

    def filter_has_labels(self, queryset, name, value):
        """
        Filter metrics based on whether they have labels.
        """
        if value:
            return queryset.exclude(labels={})
        else:
            return queryset.filter(labels={})

    def filter_label_key(self, queryset, name, value):
        """
        Filter metrics that contain a specific label key.
        """
        return queryset.filter(labels__has_key=value)

    def filter_label_value(self, queryset, name, value):
        """
        Filter metrics that contain a specific label value.
        Note: This is a simple contains check across all label values.
        """
        return queryset.filter(labels__contains=value)
