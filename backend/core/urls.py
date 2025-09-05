from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Mount accounts under /api/accounts/
    path('api/accounts/', include('accounts.urls')),
    # Metrics endpoints under /api/
    path('api/', include('metrics.urls')),
    # Chat history endpoints
    path('api/chats/', include('chats.urls')),
    path('', include('ingest.urls')),    # health + ingest + documents
]
