from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# Optional health check (useful for dev/ops)
def health(_request):
    return JsonResponse({"ok": True})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health),                 # optional
    path('api/accounts/', include('accounts.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/ingest/', include('ingest.urls')),
    path('api/', include('metrics.urls')), 
]
