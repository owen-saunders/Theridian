"""
Celery tasks for the API application.
"""
import time
from datetime import datetime, timedelta
from django.utils import timezone
from celery import shared_task
from celery.utils.log import get_task_logger
import structlog

from .models import ETLJob, MetricData, DataSource

logger = get_task_logger(__name__)
struct_logger = structlog.get_logger(__name__)


@shared_task(bind=True, max_retries=3)
def process_etl_job(self, job_id):
    """
    Process an ETL job asynchronously.
    """
    try:
        job = ETLJob.objects.get(id=job_id)
        struct_logger.info(
            "Starting ETL job processing", job_id=job_id, job_name=job.name
        )

        # Update job status
        job.status = "running"
        job.started_at = timezone.now()
        job.save()

        # Record metric
        MetricData.objects.create(
            metric_name="etl_jobs_started",
            metric_value=1,
            metric_type="counter",
            labels={"job_name": job.name, "data_source": job.data_source.name},
        )

        # Simulate ETL processing based on data source type
        records_processed = _process_data_source(job)

        # Update job completion
        job.status = "completed"
        job.completed_at = timezone.now()
        job.records_processed = records_processed
        job.save()

        # Record completion metrics
        if job.completed_at and job.started_at:
            duration = (job.completed_at - job.started_at).total_seconds()  # type: ignore
        else:
            duration = 0
        MetricData.objects.create(
            metric_name="etl_job_duration_seconds",
            metric_value=duration,
            metric_type="gauge",
            labels={"job_name": job.name, "status": "completed"},
        )

        MetricData.objects.create(
            metric_name="etl_records_processed",
            metric_value=records_processed,
            metric_type="gauge",
            labels={"job_name": job.name, "data_source": job.data_source.name},
        )

        struct_logger.info(
            "ETL job completed successfully",
            job_id=job_id,
            records_processed=records_processed,
            duration=duration,
        )

    except ETLJob.DoesNotExist:
        struct_logger.error("ETL job not found", job_id=job_id)
        raise

    except Exception as exc:
        struct_logger.error("ETL job failed", job_id=job_id, error=str(exc))

        # Update job with error
        try:
            job = ETLJob.objects.get(id=job_id)
            job.status = "failed"
            job.completed_at = timezone.now()
            job.error_message = str(exc)
            job.save()

            # Record failure metric
            MetricData.objects.create(
                metric_name="etl_jobs_failed",
                metric_value=1,
                metric_type="counter",
                labels={"job_name": job.name, "error_type": type(exc).__name__},
            )
        except:
            pass

        # Retry logic
        if self.request.retries < self.max_retries:
            struct_logger.info(
                "Retrying ETL job", job_id=job_id, retry=self.request.retries + 1
            )
            raise self.retry(countdown=60 * (2**self.request.retries))

        raise exc


def _process_data_source(job):
    """
    Process data from a data source based on its type.
    This is a simplified implementation for demonstration.
    """
    data_source = job.data_source
    configuration = job.configuration

    if data_source.source_type == "database":
        return _process_database_source(data_source, configuration)
    elif data_source.source_type == "api":
        return _process_api_source(data_source, configuration)
    elif data_source.source_type == "file":
        return _process_file_source(data_source, configuration)
    elif data_source.source_type == "stream":
        return _process_stream_source(data_source, configuration)
    else:
        raise ValueError(f"Unsupported data source type: {data_source.source_type}")


def _process_database_source(data_source, configuration):
    """Process database data source."""
    # Simulate database processing
    time.sleep(2)  # Simulate work
    batch_size = configuration.get("batch_size", 1000)
    return batch_size


def _process_api_source(data_source, configuration):
    """Process API data source."""
    # Simulate API processing
    time.sleep(1.5)  # Simulate work
    page_size = configuration.get("page_size", 100)
    pages = configuration.get("pages", 5)
    return page_size * pages


def _process_file_source(data_source, configuration):
    """Process file data source."""
    # Simulate file processing
    time.sleep(3)  # Simulate work
    estimated_records = configuration.get("estimated_records", 5000)
    return estimated_records


def _process_stream_source(data_source, configuration):
    """Process stream data source."""
    # Simulate stream processing
    duration = configuration.get("duration_seconds", 10)
    records_per_second = configuration.get("records_per_second", 100)
    time.sleep(min(duration, 5))  # Simulate work (max 5 seconds)
    return duration * records_per_second


@shared_task
def health_check():
    """
    Periodic health check task.
    """
    struct_logger.info("Running periodic health check")

    # Record system health metrics
    MetricData.objects.create(
        metric_name="system_health_check",
        metric_value=1,
        metric_type="counter",
        labels={"component": "celery"},
    )

    # Check for stuck jobs
    stuck_threshold = timezone.now() - timedelta(hours=2)
    stuck_jobs = ETLJob.objects.filter(status="running", started_at__lt=stuck_threshold)

    for job in stuck_jobs:
        struct_logger.warning(
            "Found stuck ETL job", job_id=str(job.id), started_at=job.started_at
        )
        job.status = "failed"
        job.error_message = "Job timed out after 2 hours"
        job.completed_at = timezone.now()
        job.save()

        MetricData.objects.create(
            metric_name="etl_jobs_timeout",
            metric_value=1,
            metric_type="counter",
            labels={"job_name": job.name},
        )

    return f"Health check completed. Found {stuck_jobs.count()} stuck jobs."


@shared_task
def cleanup_old_logs():
    """
    Clean up old metric data to prevent database bloat.
    """
    cutoff_date = timezone.now() - timedelta(days=30)

    deleted_count, _ = MetricData.objects.filter(timestamp__lt=cutoff_date).delete()

    struct_logger.info("Cleaned up old metric data", deleted_count=deleted_count)

    # Record cleanup metric
    MetricData.objects.create(
        metric_name="metrics_cleanup",
        metric_value=deleted_count,
        metric_type="gauge",
        labels={"retention_days": "30"},
    )

    return f"Cleaned up {deleted_count} old metric records."


@shared_task
def generate_daily_report():
    """
    Generate daily ETL summary report.
    """
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    # Get yesterday's job statistics
    jobs_yesterday = ETLJob.objects.filter(created_at__date=yesterday)

    completed_jobs = jobs_yesterday.filter(status="completed").count()
    failed_jobs = jobs_yesterday.filter(status="failed").count()
    total_records = sum(
        job.records_processed for job in jobs_yesterday.filter(status="completed")
    )

    report_data = {
        "date": str(yesterday),
        "total_jobs": jobs_yesterday.count(),
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "total_records_processed": total_records,
        "success_rate": (completed_jobs / jobs_yesterday.count() * 100)
        if jobs_yesterday.count() > 0
        else 0,
    }

    struct_logger.info("Daily ETL report generated", **report_data)

    # Record report metrics
    for key, value in report_data.items():
        if isinstance(value, (int, float)):
            MetricData.objects.create(
                metric_name=f"daily_report_{key}",
                metric_value=value,
                metric_type="gauge",
                labels={"date": str(yesterday)},
            )

    return report_data


@shared_task(bind=True)
def test_celery_connection(self):
    """
    Simple task to test Celery connectivity.
    """
    struct_logger.info("Testing Celery connection", task_id=self.request.id)
    return {
        "status": "success",
        "task_id": self.request.id,
        "timestamp": timezone.now().isoformat(),
    }
