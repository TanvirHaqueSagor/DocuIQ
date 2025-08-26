from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# Optional health check (useful for dev/ops)
def health(_request):
    return JsonResponse({"ok": True})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health),                 # optional
    path('api/auth/', include('accounts.urls')),
]
