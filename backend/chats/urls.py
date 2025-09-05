from django.urls import re_path
from .views import ThreadsListCreate, ThreadDetail, MessagesListCreate

urlpatterns = [
    re_path(r'^threads/?$', ThreadsListCreate.as_view()),
    re_path(r'^threads/(?P<pk>\d+)/?$', ThreadDetail.as_view()),
    re_path(r'^threads/(?P<thread_id>\d+)/messages/?$', MessagesListCreate.as_view()),
]

