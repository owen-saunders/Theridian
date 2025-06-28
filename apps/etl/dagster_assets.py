"""
Dagster assets for ETL operations.


WARNING: Add the following
```
import django
django.setup()
```
at the start of any Dagster op or function that uses Django models. 
This will resolve AppRegistryNotReady errors.

Do not put this at the module level; always inside the function and before
any Django model imports or ORM operations.
"""
import pandas as pd
from dagster import asset, AssetIn, Config
from typing import Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class ETLConfig(Config):
    """Configuration for ETL assets."""

    batch_size: int = 1000
    source_table: str = "raw_data"
    target_table: str = "processed_data"


@asset(description="Extract raw data from source systems", group_name="extraction")
def raw_data_extract(config: ETLConfig) -> pd.DataFrame:
    """
    Extract raw data from configured data sources.
    """
    logger.info("Starting data extraction", table=config.source_table)

    # Simulate data extraction
    # In real implementation, this would connect to actual data sources
    data = {
        "id": range(1, config.batch_size + 1),
        "name": [f"Record_{i}" for i in range(1, config.batch_size + 1)],
        "value": [i * 10 for i in range(1, config.batch_size + 1)],
        "status": ["active"] * config.batch_size,
    }

    df = pd.DataFrame(data)
    logger.info("Data extraction completed", records=len(df))

    return df


@asset(
    ins={"raw_data": AssetIn("raw_data_extract")},
    description="Transform and clean extracted data",
    group_name="transformation",
)
def cleaned_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    """
    Transform and clean the raw data.
    """
    logger.info("Starting data transformation", input_records=len(raw_data))

    # Data cleaning operations
    cleaned_df = raw_data.copy()

    # Remove any null values
    cleaned_df = cleaned_df.dropna()

    # Add computed columns
    cleaned_df["processed_at"] = pd.Timestamp.now()
    cleaned_df["value_category"] = pd.cut(
        cleaned_df["value"],
        bins=[0, 100, 500, float("inf")],
        labels=["low", "medium", "high"],
    )

    # Data validation
    assert len(cleaned_df) > 0, "No records after cleaning"
    assert not cleaned_df["id"].duplicated().any(), "Duplicate IDs found"

    logger.info("Data transformation completed", output_records=len(cleaned_df))

    return cleaned_df


@asset(
    ins={"cleaned_data": AssetIn("cleaned_data")},
    description="Aggregate cleaned data for reporting",
    group_name="aggregation",
)
def aggregated_metrics(cleaned_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Create aggregated metrics from cleaned data.
    """
    logger.info("Starting data aggregation", input_records=len(cleaned_data))

    metrics = {
        "total_records": len(cleaned_data),
        "avg_value": cleaned_data["value"].mean(),
        "max_value": cleaned_data["value"].max(),
        "min_value": cleaned_data["value"].min(),
        "value_distribution": cleaned_data["value_category"].value_counts().to_dict(),
        "status_distribution": cleaned_data["status"].value_counts().to_dict(),
        "processed_at": pd.Timestamp.now().isoformat(),
    }

    logger.info("Data aggregation completed", metrics=metrics)

    return metrics


@asset(
    ins={"metrics": AssetIn("aggregated_metrics")},
    description="Load processed data into target systems",
    group_name="loading",
)
def data_load_complete(config: ETLConfig, metrics: Dict[str, Any]) -> bool:
    """
    Load processed data into target systems and mark completion.
    """
    logger.info("Starting data load", target_table=config.target_table)

    # Simulate data loading
    # In real implementation, this would save to databases, APIs, etc.

    import django

    django.setup()  # Ensure Django is set up for ORM operations

    # Record completion metrics
    from apps.api.models import MetricData

    try:
        # Save metrics to database
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                MetricData.objects.create(
                    metric_name=f"etl_{metric_name}",
                    metric_value=value,
                    metric_type="gauge",
                    labels={"pipeline": "dagster_etl", "table": config.target_table},
                )

        logger.info(
            "Data load completed successfully",
            total_records=metrics.get("total_records", 0),
        )
        return True

    except Exception as e:
        logger.error("Data load failed", error=str(e))
        return False
