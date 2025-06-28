"""
Dagster jobs and schedules for ETL operations.

WARNING: DO NOT USE RELATIVE IMPORTS IN THIS FILE AS DAGSTER
RUNS IT AS A SCRIPT, NOT A MODULE.
"""
from dagster import (
    job,
    schedule,
    repository,
    DefaultScheduleStatus,
    RunRequest,
    ScheduleEvaluationContext,
    sensor,
    SensorEvaluationContext,
    SkipReason,
)
from apps.etl.dagster_assets import (
    raw_data_extract,
    cleaned_data,
    aggregated_metrics,
    data_load_complete,
)


@job(
    description="Complete ETL pipeline for data processing",
    tags={"team": "data", "environment": "production"},
)
def etl_pipeline():
    """
    Main ETL job that processes data through the complete pipeline.
    """
    # Define the asset dependency chain
    raw_data = raw_data_extract()
    clean_data = cleaned_data(raw_data)
    metrics = aggregated_metrics(clean_data)
    data_load_complete(metrics)


@job(
    description="Quick data extraction job",
    tags={"team": "data", "environment": "development"},
)
def extract_only():
    """
    Job that only extracts data for testing purposes.
    """
    raw_data_extract()


@schedule(
    job=etl_pipeline,
    cron_schedule="0 2 * * *",  # Run daily at 2 AM
    default_status=DefaultScheduleStatus.RUNNING,
    description="Daily ETL pipeline execution",
)
def daily_etl_schedule(context: ScheduleEvaluationContext):
    """
    Schedule for running the complete ETL pipeline daily.
    """
    return RunRequest(
        run_key=f"daily_etl_{context.scheduled_execution_time.strftime('%Y_%m_%d')}",
        tags={
            "schedule": "daily",
            "execution_date": context.scheduled_execution_time.strftime("%Y-%m-%d"),
        },
    )


@schedule(
    job=extract_only,
    cron_schedule="0 */6 * * *",  # Run every 6 hours
    default_status=DefaultScheduleStatus.STOPPED,  # Disabled by default
    description="Frequent data extraction for monitoring",
)
def frequent_extract_schedule(context: ScheduleEvaluationContext):
    """
    Schedule for running frequent data extraction.
    """
    return RunRequest(
        run_key=f"extract_{context.scheduled_execution_time.strftime('%Y_%m_%d_%H')}",
        tags={
            "schedule": "frequent",
            "execution_time": context.scheduled_execution_time.strftime(
                "%Y-%m-%d %H:%M"
            ),
        },
    )


@sensor(
    job=etl_pipeline, description="Sensor to trigger ETL when new data is available"
)
def data_availability_sensor(context: SensorEvaluationContext):
    """
    Sensor that monitors for new data availability and triggers ETL.
    """
    # Check for new data indicator
    # This could check file timestamps, database triggers, API endpoints, etc.

    try:
        from apps.api.models import DataSource

        # Check if any data sources have been updated recently
        import django

        django.setup()

        from django.utils import timezone
        from datetime import timedelta

        recent_threshold = timezone.now() - timedelta(hours=1)
        updated_sources = DataSource.objects.filter(
            updated_at__gte=recent_threshold, is_active=True
        )

        if updated_sources.exists():
            # Get the latest updated source
            latest_source = updated_sources.order_by("-updated_at").first()

            return RunRequest(
                run_key=f"sensor_triggered_{latest_source.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                tags={
                    "trigger": "sensor",
                    "data_source": latest_source.name,
                    "source_type": latest_source.source_type,
                },
            )

        return SkipReason("No new data sources updated in the last hour")

    except Exception as e:
        context.log.error(f"Error in data availability sensor: {str(e)}")
        return SkipReason(f"Sensor error: {str(e)}")


@sensor(job=etl_pipeline, description="Failure recovery sensor for failed ETL jobs")
def etl_failure_recovery_sensor(context: SensorEvaluationContext):
    """
    Sensor to automatically retry failed ETL jobs after investigation.
    """
    try:
        from apps.api.models import ETLJob

        # Check for failed jobs that might need retry
        import django

        django.setup()

        from django.utils import timezone
        from datetime import timedelta

        # Look for jobs that failed in the last 4 hours but haven't been retried
        retry_threshold = timezone.now() - timedelta(hours=4)
        failed_jobs = ETLJob.objects.filter(
            status="failed",
            completed_at__gte=retry_threshold,
            error_message__icontains="temporary",  # Only retry temporary failures
        )

        if failed_jobs.exists():
            # Retry the oldest failed job
            job_to_retry = failed_jobs.order_by("completed_at").first()

            return RunRequest(
                run_key=f"retry_{job_to_retry.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                tags={
                    "trigger": "retry",
                    "original_job_id": str(job_to_retry.id),
                    "retry_reason": "automatic_recovery",
                },
            )

        return SkipReason("No failed jobs requiring automatic retry")

    except Exception as e:
        context.log.error(f"Error in failure recovery sensor: {str(e)}")
        return SkipReason(f"Recovery sensor error: {str(e)}")


@repository
def etl_repository():
    return [
        etl_pipeline,
        extract_only,
        daily_etl_schedule,
        frequent_extract_schedule,
        data_availability_sensor,
        etl_failure_recovery_sensor,
    ]
