from rest_framework import generics, permissions
from core.permissions import IsInTenant
from .models import Document
from .serializers import DocumentSerializer

class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsInTenant]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        qs = Document.objects.all()
        if tenant is None:
            qs = qs.filter(organization__isnull=True)
        else:
            qs = qs.filter(organization=tenant)
        # simple limit/sort
        limit = int(self.request.query_params.get('limit', '50') or 50)
        sort = self.request.query_params.get('sort', '-created_at')
        return qs.order_by(sort)[:limit]

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(organization=None if tenant is None else tenant,
                        created_by=self.request.user)

class DocumentDeleteView(generics.DestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsInTenant]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        qs = Document.objects.all()
        return qs.filter(organization__isnull=True) if tenant is None else qs.filter(organization=tenant)
