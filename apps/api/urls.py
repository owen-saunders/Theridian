"""
URL patterns for the API application.
"""
from django.urls import path
from . import views

app_name = "api"

urlpatterns = [
    # API Keys
    path("keys/", views.APIKeyListCreateView.as_view(), name="apikey-list"),
    path("keys/<uuid:pk>/", views.APIKeyDetailView.as_view(), name="apikey-detail"),
    # Data Sources
    path(
        "data-sources/",
        views.DataSourceListCreateView.as_view(),
        name="datasource-list",
    ),
    path(
        "data-sources/<uuid:pk>/",
        views.DataSourceDetailView.as_view(),
        name="datasource-detail",
    ),
    # ETL Jobs
    path("etl-jobs/", views.ETLJobListCreateView.as_view(), name="etljob-list"),
    path("etl-jobs/<uuid:pk>/", views.ETLJobDetailView.as_view(), name="etljob-detail"),
    path(
        "etl-jobs/<uuid:pk>/retry/",
        views.ETLJobRetryView.as_view(),
        name="etljob-retry",
    ),
    # Metrics
    path("metrics/", views.MetricDataListCreateView.as_view(), name="metric-list"),
    # Dashboard
    path(
        "dashboard/stats/", views.DashboardStatsView.as_view(), name="dashboard-stats"
    ),
    # Health Check
    path("health/", views.health_check, name="health-check"),
]
