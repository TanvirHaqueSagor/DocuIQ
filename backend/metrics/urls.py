from django.urls import path
from .views import DashboardSummaryView, UsageSeriesView

urlpatterns = [
    path('dashboard/summary', DashboardSummaryView.as_view()),
    path('analytics/usage', UsageSeriesView.as_view()),
]
