from django.urls import re_path
from .views import DashboardSummaryView, UsageSeriesView

urlpatterns = [
    re_path(r'^dashboard/summary/?$', DashboardSummaryView.as_view()),
    re_path(r'^analytics/usage/?$', UsageSeriesView.as_view()),
]
