from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from django.db.models import Q

from .models import IngestSource, IngestJob, IngestFile
from .serializers import SourceSerializer, IngestJobSerializer, DocumentSerializer

class HealthView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): return Response({"ok": True})

# ---- Sources ----
class SourceListCreate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = IngestSource.objects.filter(created_by=request.user)
        return Response(SourceSerializer(qs, many=True).data)

    def post(self, request):
        s = SourceSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        obj = s.save(created_by=request.user)
        return Response(SourceSerializer(obj).data, status=201)

class SourceDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        IngestSource.objects.filter(id=pk, created_by=request.user).delete()
        return Response(status=204)

# ---- Jobs ----
class JobListCreate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = IngestJob.objects.filter(created_by=request.user)
        return Response(IngestJobSerializer(qs, many=True).data)

    def post(self, request):
        data = request.data.copy()
        data.setdefault('status', 'queued')
        data.setdefault('progress', 0)
        ser = IngestJobSerializer(data=data)
        ser.is_valid(raise_exception=True)
        obj = ser.save(created_by=request.user)
        return Response(IngestJobSerializer(obj).data, status=201)

# ---- Upload ----
class UploadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        files = request.FILES.getlist('files')
        if not files:
            return Response({'detail':'No files provided'}, status=400)
        out = []
        for f in files:
            doc = IngestFile.objects.create(
                uploaded_by=request.user,
                filename=f.name,
                file=f
            )
            out.append({'id': doc.id, 'name': doc.filename})
        return Response(out, status=201)

# ---- Documents ----
class DocumentList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = int(request.GET.get('limit', 20))
        sort = request.GET.get('sort', '-created_at')
        # Map created_at -> uploaded_at for underlying model
        mapped_sort = sort.replace('created_at', 'uploaded_at')
        qs = IngestFile.objects.filter(uploaded_by=request.user).order_by(mapped_sort)[:limit]
        return Response(DocumentSerializer(qs, many=True).data)

class DocumentDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        IngestFile.objects.filter(id=pk, uploaded_by=request.user).delete()
        return Response(status=204)
