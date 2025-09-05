from django.urls import path, re_path
from .views import (
    HealthView, SourceListCreate, SourceDetail,
    JobListCreate, JobDetail, UploadView, DocumentList, DocumentDetail,
    ContentList, ContentStatus, ContentRetry, SyncJobCancel
)

urlpatterns = [
    re_path(r'^health/?$', HealthView.as_view()),

    re_path(r'^api/ingest/sources/?$', SourceListCreate.as_view()),
    re_path(r'^api/ingest/sources/(?P<pk>\d+)/?$', SourceDetail.as_view()),

    re_path(r'^api/ingest/jobs/?$', JobListCreate.as_view()),
    re_path(r'^api/ingest/jobs/(?P<pk>\d+)/?$', JobDetail.as_view()),
    re_path(r'^api/ingest/upload/?$', UploadView.as_view()),

    re_path(r'^api/documents/?$', DocumentList.as_view()),
    re_path(r'^api/documents/(?P<pk>\d+)/?$', DocumentDetail.as_view()),

    # Unified content endpoints
    re_path(r'^api/content/?$', ContentList.as_view()),
    re_path(r'^api/content/(?P<pk>\d+)/status/?$', ContentStatus.as_view()),
    re_path(r'^api/content/(?P<pk>\d+)/retry/?$', ContentRetry.as_view()),

    # Sync job alias endpoints
    re_path(r'^api/sync-jobs/(?P<pk>\d+)/?$', JobDetail.as_view()),
    re_path(r'^api/sync-jobs/(?P<pk>\d+)/cancel/?$', SyncJobCancel.as_view()),
]
