from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from django.db.models import Q
from django.utils import timezone
import os, requests

from .models import IngestSource, IngestJob, IngestFile
from .serializers import SourceSerializer, IngestJobSerializer, DocumentSerializer
from .status import set_status
from .tasks import process_item, process_web_job

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
        # Kick off processing for certain modes
        mode = str(obj.mode or '').lower()
        try:
            if mode == 'web':
                process_web_job.delay(obj.id)
        except Exception:
            pass
        return Response(IngestJobSerializer(obj).data, status=201)

class JobDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            j = IngestJob.objects.get(id=pk, created_by=request.user)
        except IngestJob.DoesNotExist:
            return Response(status=404)
        return Response(IngestJobSerializer(j).data)

    def delete(self, request, pk):
        # Cascade delete for certain modes (e.g., web) to remove the fetched document too
        j = IngestJob.objects.filter(id=pk, created_by=request.user).first()
        if j is not None:
            mode = str(j.mode or '').lower()
            if mode == 'web':
                payload = j.payload or {}
                file_id = payload.get('file_id')
                url = payload.get('url') or payload.get('start_url')
                # Fallback to source config url if payload empty
                if not url and getattr(j, 'source_id', None):
                    try:
                        src = IngestSource.objects.filter(id=j.source_id, created_by=request.user).first()
                        cfg = (src.config or {}) if src else {}
                        url = cfg.get('url') or cfg.get('start_url') or cfg.get('seed_url') or cfg.get('base_url')
                    except Exception:
                        url = None
                # Helper to delete a file record + unindex + file blob
                def _delete_file_obj(rec: IngestFile):
                    if not rec:
                        return
                    try:
                        AI_URL = os.environ.get('AI_ENGINE_URL') or os.environ.get('AI_URL') or 'http://ai:9000'
                        requests.post(f"{AI_URL}/unindex_document", json={ 'document_id': str(rec.id) }, timeout=10)
                    except Exception:
                        pass
                    try:
                        if getattr(rec, 'file', None):
                            rec.file.delete(save=False)
                    except Exception:
                        pass
                    rec.delete()
                if file_id:
                    _delete_file_obj(IngestFile.objects.filter(id=file_id, uploaded_by=request.user).first())
                if url:
                    try:
                        qs = IngestFile.objects.filter(uploaded_by=request.user, steps_json__contains={'source_url': url})
                        for rec in qs[:10]:
                            _delete_file_obj(rec)
                    except Exception:
                        pass
            # finally delete the job itself
            j.delete()
        return Response(status=204)

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
            # Queue processing (Celery)
            try:
                process_item.delay(doc.id)
            except Exception:
                pass
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
        obj = IngestFile.objects.filter(id=pk, uploaded_by=request.user).first()
        if not obj:
            return Response(status=204)
        # Ask AI engine to unindex vectors for this document
        try:
            AI_URL = os.environ.get('AI_ENGINE_URL') or os.environ.get('AI_URL') or 'http://ai:9000'
            requests.post(f"{AI_URL}/unindex_document", json={ 'document_id': str(obj.id) }, timeout=10)
        except Exception:
            pass
        # Remove stored file if present
        try:
            if getattr(obj, 'file', None):
                obj.file.delete(save=False)
        except Exception:
            pass
        obj.delete()
        return Response(status=204)

# ---- Unified content endpoints ----
class ContentList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = IngestFile.objects.filter(uploaded_by=request.user)
        status_param = request.GET.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        limit = int(request.GET.get('limit', 50))
        sort = request.GET.get('sort', '-status_updated_at')
        return Response(DocumentSerializer(qs.order_by(sort)[:limit], many=True).data)

class ContentStatus(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            obj = IngestFile.objects.get(id=pk, uploaded_by=request.user)
        except IngestFile.DoesNotExist:
            return Response(status=404)
        d = DocumentSerializer(obj).data
        return Response({
            'id': obj.id,
            'status': d.get('status'),
            'error_code': d.get('error_code'),
            'error_text': d.get('error_text'),
            'steps_json': d.get('steps_json'),
            'indexed_bool': d.get('indexed_bool'),
        })

class ContentRetry(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            obj = IngestFile.objects.get(id=pk, uploaded_by=request.user)
        except IngestFile.DoesNotExist:
            return Response(status=404)
        # Set to QUEUED and clear error fields
        set_status(obj, 'QUEUED', error_code=None, error_text=None, patch={})
        data = {'mode': 'upload', 'payload': {'file_ids': [obj.id]}, 'status': 'queued', 'progress': 0}
        ser = IngestJobSerializer(data=data)
        ser.is_valid(raise_exception=True)
        job = ser.save(created_by=request.user)
        job.state = 'QUEUED'
        job.started_at = None
        job.finished_at = None
        job.save(update_fields=['state','started_at','finished_at'])
        return Response({'ok': True, 'job_id': job.id}, status=201)

class SyncJobCancel(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            j = IngestJob.objects.get(id=pk, created_by=request.user)
        except IngestJob.DoesNotExist:
            return Response(status=404)
        j.status = 'failed'
        j.state = 'CANCELLED'
        j.finished_at = timezone.now()
        j.error_text = 'Cancelled by user'
        j.save(update_fields=['status','state','finished_at','error_text'])
        return Response({'ok': True})
