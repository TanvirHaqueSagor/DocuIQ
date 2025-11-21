from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.http import FileResponse, Http404
from django.views.generic import TemplateView
import os, requests
import logging

from .models import IngestSource, IngestJob, IngestFile
from .serializers import SourceSerializer, IngestJobSerializer, DocumentSerializer
from .status import set_status
from .tasks import process_item, process_web_job
from accounts.plan import get_effective_plan, get_plan_limits

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
        try:
            logging.getLogger(__name__).info("Job created id=%s mode=%s by user=%s", obj.id, obj.mode, getattr(request.user, 'id', None))
        except Exception:
            pass
        # Kick off processing for certain modes
        mode = str(obj.mode or '').lower()
        try:
            if mode == 'web':
                process_web_job.delay(obj.id)
                logging.getLogger(__name__).info("process_web_job queued job_id=%s", obj.id)
        except Exception:
            logging.getLogger(__name__).exception("Failed to enqueue web job id=%s", obj.id)
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
            extra_deleted = 0
            if mode == 'web':
                url = payload.get('url') or payload.get('start_url')
                lookup = Q()
                if url:
                    lookup |= Q(payload__url=url) | Q(payload__start_url=url)
                if lookup:
                    extras = IngestJob.objects.filter(created_by=request.user, mode=j.mode).exclude(id=j.id).filter(lookup)
                    extra_deleted = extras.count()
                    if extra_deleted:
                        extras.delete()
            j.delete()
            try:
                logging.getLogger(__name__).info("Deleted job id=%s mode=%s extras=%s", pk, mode, extra_deleted)
            except Exception:
                pass
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
        plan_code = get_effective_plan(request.user)
        limits = get_plan_limits(plan_code)
        profile = getattr(request.user, 'userprofile', None)
        org = getattr(profile, 'organization', None) if profile else None

        if limits.document_limit is not None:
            if org:
                doc_qs = IngestFile.objects.filter(Q(organization=org) | Q(uploaded_by=request.user, organization__isnull=True))
            else:
                doc_qs = IngestFile.objects.filter(uploaded_by=request.user, organization__isnull=True)
            existing = doc_qs.count()
            if existing + len(files) > limits.document_limit:
                return Response({
                    'detail': 'plan_document_limit_reached',
                    'limit': limits.document_limit,
                }, status=status.HTTP_403_FORBIDDEN)

        max_size_bytes = None
        if limits.max_file_size_mb is not None:
            max_size_bytes = limits.max_file_size_mb * 1024 * 1024

        out = []
        try:
            logging.getLogger(__name__).info("Upload received count=%d by user=%s", len(files), getattr(request.user, 'id', None))
        except Exception:
            pass
        for f in files:
            f_size = getattr(f, 'size', 0) or 0
            if max_size_bytes is not None and f_size > max_size_bytes:
                return Response({
                    'detail': 'plan_file_size_limit',
                    'limit_mb': limits.max_file_size_mb,
                    'filename': getattr(f, 'name', None),
                }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            doc = IngestFile.objects.create(
                uploaded_by=request.user,
                filename=f.name,
                size=f_size,
                content_type=getattr(f, 'content_type', ''),
                organization=org
            )
            try:
                f.seek(0)
            except Exception:
                pass
            doc.file.save(f.name, f, save=True)
            # Queue processing (Celery)
            try:
                process_item.delay(doc.id)
                logging.getLogger(__name__).info("Queued process_item file_id=%s name=%s size=%s", doc.id, doc.filename, getattr(doc, 'size', None))
            except Exception:
                logging.getLogger(__name__).exception("Failed to queue process_item for file_id=%s", doc.id)
            out.append({'id': doc.id, 'name': doc.filename})
        return Response(out, status=201)

# ---- Documents ----
class DocumentList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 20))
        except (TypeError, ValueError):
            limit = 20
        try:
            offset = int(request.GET.get('offset', 0))
        except (TypeError, ValueError):
            offset = 0
        limit = max(1, min(limit, 500))
        offset = max(0, offset)
        sort = request.GET.get('sort', '-created_at')
        mapped_sort = sort.replace('created_at', 'uploaded_at')
        qs = IngestFile.objects.filter(uploaded_by=request.user).order_by(mapped_sort)
        total = qs.count()
        window = qs[offset: offset + limit]
        data = DocumentSerializer(window, many=True).data
        return Response({
            'count': total,
            'results': data,
            'limit': limit,
            'offset': offset,
        })

class DocumentDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        logger = logging.getLogger(__name__)
        logger.info("DocumentDetail requested id=%s user=%s", pk, getattr(request.user, 'id', None))
        obj = IngestFile.objects.filter(id=pk, uploaded_by=request.user).first()
        # Fallbacks: allow locating by title hint (?t=) or source URL (?url=)
        if not obj:
            t = request.query_params.get('t') or request.query_params.get('title')
            src_url = request.query_params.get('url')
            if src_url:
                try:
                    obj = (IngestFile.objects
                           .filter(uploaded_by=request.user, steps_json__contains={'source_url': src_url})
                           .order_by('-uploaded_at')
                           .first())
                except Exception:
                    obj = None
            if not obj and t:
                try:
                    obj = (IngestFile.objects
                           .filter(uploaded_by=request.user, filename__icontains=t)
                           .order_by('-uploaded_at')
                           .first())
                except Exception:
                    obj = None
        if not obj:
            logger.warning("DocumentDetail not found id=%s user=%s", pk, getattr(request.user, 'id', None))
            return Response({"detail": "not_found"}, status=404)
        logger.info("DocumentDetail found id=%s filename=%s status=%s", obj.id, obj.filename, obj.status)
        d = DocumentSerializer(obj).data
        # Build references from saved chat messages that cite this document
        refs = []
        try:
            from chats.models import ChatMessage
            doc_id_str = str(obj.id)
            src_url = None
            try:
                src_url = (getattr(obj, 'steps_json', {}) or {}).get('source_url')
            except Exception:
                src_url = None
            msgs = ChatMessage.objects.filter(thread__owner=request.user, role='assistant').order_by('-created_at')[:200]
            for m in msgs:
                cits = []
                try:
                    for c in (m.citations or []):
                        did = str(c.get('doc_id') or c.get('documentId') or c.get('document_id') or '')
                        url = c.get('url') or c.get('origin_url') or ''
                        if (did and did == doc_id_str) or (src_url and url and url == src_url):
                            cits.append(c)
                except Exception:
                    cits = []
                if cits:
                    refs.append({
                        'thread_id': m.thread_id,
                        'message_id': m.id,
                        'created_at': m.created_at.isoformat(),
                        'content': m.content,
                        'citations': cits,
                    })
        except Exception:
            refs = []
        return Response({'document': d, 'references': refs})

    def delete(self, request, pk):
        logger = logging.getLogger(__name__)
        obj = IngestFile.objects.filter(id=pk, uploaded_by=request.user).first()
        if not obj:
            return Response(status=204)
        jobs_deleted = 0
        sources_deleted = 0
        with transaction.atomic():
            # Cascade delete related ingest jobs referencing this file
            try:
                jobs = list(IngestJob.objects.filter(created_by=request.user))
                src_ids = set()
                for j in jobs:
                    try:
                        p = j.payload or {}
                        want = False
                        # upload jobs: payload.file_ids contains pk
                        if isinstance(p.get('file_ids'), list):
                            try:
                                if int(pk) in [int(x) for x in p.get('file_ids')]:
                                    want = True
                            except Exception:
                                want = any(str(pk) == str(x) for x in p.get('file_ids'))
                        # web jobs: payload.file_id equals pk or url matches source_url
                        if not want:
                            if (p.get('file_id') and str(p.get('file_id')) == str(pk)):
                                want = True
                            else:
                                try:
                                    src_url = (getattr(obj, 'steps_json', {}) or {}).get('source_url')
                                except Exception:
                                    src_url = None
                                if src_url and (p.get('url') == src_url or p.get('start_url') == src_url):
                                    want = True
                        if want:
                            if getattr(j, 'source_id', None):
                                src_ids.add(j.source_id)
                            j.delete()
                            jobs_deleted += 1
                    except Exception:
                        # Ignore malformed payloads or casting errors per job
                        pass
                # Optionally delete orphan sources
                for sid in list(src_ids):
                    try:
                        # Only delete if no other jobs reference it
                        if not IngestJob.objects.filter(source_id=sid).exists():
                            src = IngestSource.objects.filter(id=sid, created_by=request.user).first()
                            if src:
                                src.delete()
                                sources_deleted += 1
                    except Exception:
                        pass
            except Exception:
                pass

            # Ask AI engine to unindex vectors for this document
            try:
                AI_URL = os.environ.get('AI_ENGINE_URL') or os.environ.get('AI_URL') or 'http://ai:9000'
                requests.post(f"{AI_URL}/unindex_document", json={ 'document_id': str(obj.id) }, timeout=10)
                logger.info("Unindex requested for file_id=%s", obj.id)
            except Exception:
                logger.warning("Failed to unindex file_id=%s", obj.id)
            # Remove stored file if present
            try:
                if getattr(obj, 'file', None):
                    obj.file.delete(save=False)
            except Exception:
                pass
            obj.delete()
        try:
            logger.info("Deleted document id=%s; cascade jobs=%s sources=%s", pk, jobs_deleted, sources_deleted)
        except Exception:
            pass
        return Response(status=204)


class DocumentFind(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        title = (request.query_params.get('title') or request.query_params.get('t') or '').strip()
        url = (request.query_params.get('url') or '').strip()
        qs = IngestFile.objects.filter(uploaded_by=request.user)
        obj = None
        if url:
            try:
                obj = qs.filter(steps_json__contains={'source_url': url}).order_by('-uploaded_at').first()
            except Exception:
                obj = None
        if (not obj) and title:
            obj = qs.filter(filename__icontains=title).order_by('-uploaded_at').first()
        if not obj:
            return Response({"detail": "not_found"}, status=404)
        return Response(DocumentSerializer(obj).data)


class DocumentFile(APIView):
    # AllowAny so we can accept token via query param; we will validate manually
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, pk):
        logger = logging.getLogger(__name__)
        user = None
        # Try Authorization header first
        try:
            authz = request.headers.get('Authorization', '')
            if authz.lower().startswith('bearer '):
                tok = authz.split(' ',1)[1].strip()
                if tok:
                    auth = JWTAuthentication()
                    v = auth.get_validated_token(tok)
                    user = auth.get_user(v)
        except Exception:
            user = None
        # Fallback: query param token (for iframe)
        if not user:
            try:
                qtok = request.query_params.get('access') or request.query_params.get('token')
                if qtok:
                    auth = JWTAuthentication()
                    v = auth.get_validated_token(qtok)
                    user = auth.get_user(v)
                    logger.info("Authenticated via query token for document file id=%s user=%s", pk, getattr(user, 'id', None))
            except Exception as e:
                user = None
        if not user:
            token = request.query_params.get('access') or request.query_params.get('token')
            if token:
                try:
                    backend = JWTAuthentication()
                    validated = backend.get_validated_token(token)
                    user = backend.get_user(validated)
                    logging.getLogger(__name__).info("DocumentFile authenticated via query token file_id=%s user=%s", pk, getattr(user, 'id', None))
                except Exception:
                    user = None
        if not user:
            return Response(status=401)
        obj = IngestFile.objects.filter(id=pk, uploaded_by=user).first()
        if not obj or not getattr(obj, 'file', None) or not getattr(obj.file, 'name', ''):
            raise Http404
        try:
            storage = obj.file.storage
            if storage and hasattr(storage, 'exists') and not storage.exists(obj.file.name):
                raise Http404
        except Exception:
            pass
        fh = obj.file.open('rb')
        resp = FileResponse(fh, content_type=obj.content_type or 'application/pdf')
        # Allow iframe embedding (especially for dev/local)
        try:
            from django.conf import settings
            if getattr(settings, 'DEBUG', False):
                resp['X-Frame-Options'] = 'ALLOWALL'
        except Exception:
            pass
        try:
            logging.getLogger(__name__).info("Serving file download id=%s path=%s", obj.id, getattr(obj.file, 'name', None))
        except Exception:
            pass
        return resp

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
        try:
            logging.getLogger(__name__).info("Retry queued for file_id=%s job_id=%s", obj.id, job.id)
        except Exception:
            pass
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
        try:
            logging.getLogger(__name__).info("Sync job cancelled id=%s by user=%s", j.id, getattr(request.user, 'id', None))
        except Exception:
            pass
        return Response({'ok': True})


class AdminCleanup(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        action = str((request.data or {}).get('action') or '').lower()
        if action not in ('clear_vectors','delete_documents','delete_all'):
            return Response({'detail': 'invalid_action'}, status=400)
        cleared = False
        vectors_removed = 0
        deleted_docs = 0
        deleted_jobs = 0
        deleted_sources = 0
        # Helper to cascade-delete a single file (reuse logic from DocumentDetail.delete)
        def _delete_doc(obj: IngestFile):
            nonlocal deleted_jobs, deleted_sources
            if not obj:
                return
            with transaction.atomic():
                try:
                    jobs = list(IngestJob.objects.filter(created_by=request.user))
                    src_ids = set()
                    for j in jobs:
                        try:
                            p = j.payload or {}
                            want = False
                            if isinstance(p.get('file_ids'), list):
                                try:
                                    if int(obj.id) in [int(x) for x in p.get('file_ids')]:
                                        want = True
                                except Exception:
                                    want = any(str(obj.id) == str(x) for x in p.get('file_ids'))
                            if not want:
                                if (p.get('file_id') and str(p.get('file_id')) == str(obj.id)):
                                    want = True
                                else:
                                    try:
                                        src_url = (getattr(obj, 'steps_json', {}) or {}).get('source_url')
                                    except Exception:
                                        src_url = None
                                    if src_url and (p.get('url') == src_url or p.get('start_url') == src_url):
                                        want = True
                            if want:
                                if getattr(j, 'source_id', None):
                                    src_ids.add(j.source_id)
                                j.delete(); deleted_jobs += 1
                        except Exception:
                            pass
                    for sid in list(src_ids):
                        try:
                            if not IngestJob.objects.filter(source_id=sid).exists():
                                src = IngestSource.objects.filter(id=sid, created_by=request.user).first()
                                if src:
                                    src.delete(); deleted_sources += 1
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    AI_URL = os.environ.get('AI_ENGINE_URL') or os.environ.get('AI_URL') or 'http://ai:9000'
                    requests.post(f"{AI_URL}/unindex_document", json={ 'document_id': str(obj.id) }, timeout=10)
                except Exception:
                    pass
                try:
                    if getattr(obj, 'file', None):
                        obj.file.delete(save=False)
                except Exception:
                    pass
                obj.delete()

        # Clear vectors
        if action in ('clear_vectors','delete_all'):
            try:
                AI_URL = os.environ.get('AI_ENGINE_URL') or os.environ.get('AI_URL') or 'http://ai:9000'
                r = requests.post(f"{AI_URL}/admin/clear_all", timeout=15)
                cleared = bool(r.ok)
                try:
                    data = r.json() if r.content else {}
                    vectors_removed = int(data.get('removed') or 0)
                except Exception:
                    vectors_removed = 0
            except Exception:
                cleared = False
        # Delete documents (+ cascade)
        if action in ('delete_documents','delete_all'):
            qs = IngestFile.objects.filter(uploaded_by=request.user).order_by('-id')
            for obj in qs:
                _delete_doc(obj)
                deleted_docs += 1
        return Response({
            'ok': True,
            'cleared_vectors': cleared,
            'vectors_removed': vectors_removed,
            'deleted_docs': deleted_docs,
            'deleted_jobs': deleted_jobs,
            'deleted_sources': deleted_sources,
        })


class OAuthStartView(TemplateView):
    """
    Placeholder UI for kicking off third-party OAuth flows.
    In a real deployment this would redirect to the provider consent URL.
    For now we render a simple page so the browser workflow is unblocked.
    """
    template_name = "ingest/oauth_stub.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kind = (self.request.GET.get('kind') or '').strip().lower() or 'files'
        redirect_url = self.request.GET.get('redirect') or ''
        origin = f"{self.request.scheme}://{self.request.get_host()}"
        context.update({
            "kind": kind,
            "redirect": redirect_url,
            "origin": origin,
        })
        return context
