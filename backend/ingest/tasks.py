from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from urllib.parse import urlsplit, unquote, quote
from .models import IngestFile, IngestJob, IngestSource
from .status import set_status
import os, requests, os as _os, hashlib, random, io
from pdfminer.high_level import extract_text as pdf_extract_text, extract_pages
import logging

# Quiet noisy pdfminer warnings (e.g., invalid color values in malformed PDFs)
for _ln in (
    'pdfminer',
    'pdfminer.pdfinterp',
    'pdfminer.converter',
    'pdfminer.layout',
    'pdfminer.image',
    'pdfminer.cmapdb',
):
    try:
        logging.getLogger(_ln).setLevel(logging.ERROR)
    except Exception:
        pass

AI_URL = os.environ.get('AI_ENGINE_URL') or os.environ.get('AI_URL') or 'http://ai:9000'
CRAWL_UA = os.environ.get('CRAWL_UA', 'DocuIQBot/1.0 (+https://docuiq.local)')
SCRAPER_URL = os.environ.get('SCRAPER_URL')  # optional external render/fetch service

_UAS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36',
]

def _browser_headers(overrides=None):
    h = {
        'User-Agent': CRAWL_UA or random.choice(_UAS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.google.com/',
    }
    if overrides:
        try:
            h.update({k: v for k, v in (overrides or {}).items() if isinstance(k, str)})
        except Exception:
            pass
    return h

def _fetch_url(url, *, headers=None, timeout=20):
    # First attempt: direct fetch with browser-like headers
    last = None
    try:
        last = requests.get(url, headers=_browser_headers(headers), timeout=timeout)
        if last.status_code == 200 and (last.content or b''):
            return last
    except Exception:
        pass
    # Fallback: rotate UA and try again
    try:
        last = requests.get(url, headers=_browser_headers({'User-Agent': random.choice(_UAS)}), timeout=timeout)
        if last.status_code == 200 and (last.content or b''):
            return last
    except Exception:
        pass
    # Optional external scraper (rendered HTML) if configured
    if SCRAPER_URL:
        try:
            sr = requests.get(SCRAPER_URL, params={'url': url}, timeout=timeout+10)
            if sr.ok and (sr.content or b''):
                class Resp:
                    status_code = 200
                    headers = {'content-type': sr.headers.get('content-type','text/html')}
                    content = sr.content
                    text = sr.text
                return Resp()
        except Exception:
            pass
    if last is not None:
        last.raise_for_status()
        return last
    raise requests.HTTPError('fetch_failed')

@shared_task(bind=True, max_retries=3, default_retry_delay=15)
def process_item(self, file_id: int, job_id: int = None):
    try:
        item = IngestFile.objects.get(id=file_id)
    except IngestFile.DoesNotExist:
        return

    # FETCHING
    set_status(item, 'FETCHING', patch={ 'fetching': { 'started_at': timezone.now().isoformat() } })
    content = b''
    try:
        fh = getattr(item, 'file', None)
        if fh and hasattr(fh, 'open'):
            with fh.open('rb') as f:
                content = f.read()
        bytes_in = len(content)
    except Exception as e:
        set_status(item, 'FAILED', error_code='FETCH_ERROR', error_text=str(e))
        # Reflect in job if provided
        if job_id:
            try:
                j = IngestJob.objects.filter(id=job_id).first()
                if j:
                    j.status = 'failed'; j.finished_at = timezone.now(); j.message = str(e); j.save(update_fields=['status','finished_at','message'])
            except Exception:
                pass
        return

    # NORMALIZING (extract text)
    mime = (getattr(item, 'content_type', '') or '').lower()
    filename = (getattr(item, 'filename', '') or '').lower()
    set_status(item, 'NORMALIZING', patch={ 'normalizing': { 'mime': mime, 'bytes_in': len(content) } })
    text = ''
    pages_payload = None
    try:
        if 'pdf' in mime or filename.endswith('.pdf'):
            # Extract text per-page for precise page mapping
            pages = []
            try:
                for i, layout in enumerate(extract_pages(io.BytesIO(content)), start=1):
                    parts = []
                    for el in layout:
                        try:
                            if hasattr(el, 'get_text'):
                                parts.append(el.get_text())
                        except Exception:
                            pass
                    txt = "\n".join([t for t in parts if t and t.strip()])
                    pages.append({ 'page': i, 'text': txt })
            except Exception:
                pages = []
            # Fallback to whole-doc text as well
            try:
                text = pdf_extract_text(io.BytesIO(content)) or ''
            except Exception:
                text = ''
            pages_payload = pages if pages else None
        else:
            # Fallback: naive utf-8 decode (handles txt/html minimally)
            text = content.decode('utf-8', errors='ignore')
    except Exception as e:
        text = ''

    # CHUNKING (handled by AI for now; record placeholder)
    set_status(item, 'CHUNKING', patch={ 'chunking': { 'chunk_count': 0, 'avg_tokens': 0 } })

    # EMBEDDING + INDEXING via AI engine
    set_status(item, 'EMBEDDING')
    try:
        payload = {
            'document_id': str(item.id),
            'title': item.filename,
        }
        if pages_payload:
            payload['pages'] = pages_payload
        else:
            payload['text'] = text
        r = requests.post(f"{AI_URL}/index_document", json=payload, timeout=30)
        if not r.ok:
            # Surface AI error
            snippet = (r.text or '')[:200]
            set_status(item, 'FAILED', error_code='EMBED_ERROR', error_text=f'AI index failed {r.status_code}: {snippet}')
            if job_id:
                try:
                    j = IngestJob.objects.filter(id=job_id).first()
                    if j:
                        j.status = 'failed'; j.finished_at = timezone.now(); j.message = f'Embed failed: {snippet}'; j.save(update_fields=['status','finished_at','message'])
                except Exception:
                    pass
            return
        data = r.json() if r.content else {}
    except Exception as e:
        set_status(item, 'FAILED', error_code='EMBED_ERROR', error_text=str(e))
        if job_id:
            try:
                j = IngestJob.objects.filter(id=job_id).first()
                if j:
                    j.status = 'failed'; j.finished_at = timezone.now(); j.message = str(e); j.save(update_fields=['status','finished_at','message'])
            except Exception:
                pass
        return

    set_status(item, 'INDEXING', patch={ 'indexing': { 'vectors_written': int(data.get('chunks') or 0) } })
    if int(data.get('chunks') or 0) > 0:
        set_status(item, 'READY', patch={ 'partial': False })
        if job_id:
            try:
                j = IngestJob.objects.filter(id=job_id).first()
                if j:
                    j.status = 'success'; j.progress = 100; j.finished_at = timezone.now(); j.message = f'Indexed {int(data.get("chunks") or 0)} chunk(s)'; j.save(update_fields=['status','progress','finished_at','message'])
            except Exception:
                pass
    else:
        set_status(item, 'FAILED', error_code='EMBED_ERROR', error_text='No chunks embedded')
        if job_id:
            try:
                j = IngestJob.objects.filter(id=job_id).first()
                if j:
                    j.status = 'failed'; j.finished_at = timezone.now(); j.message = 'No chunks embedded'; j.save(update_fields=['status','finished_at','message'])
            except Exception:
                pass


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def process_web_job(self, job_id: int):
    """Fetch a web URL for a job, create an IngestFile, and enqueue processing."""
    try:
        j = IngestJob.objects.get(id=job_id)
    except IngestJob.DoesNotExist:
        return
    # Mark running
    j.status = 'running'
    j.started_at = timezone.now()
    j.save(update_fields=['status','started_at'])
    try:
        payload = (j.payload or {})
        file_id_hint = payload.get('file_id')
        url = payload.get('url') or payload.get('start_url')
        rec = None
        if file_id_hint:
            rec = IngestFile.objects.filter(id=file_id_hint, uploaded_by=j.created_by).first()
            if rec and not url:
                try:
                    url = (rec.steps_json or {}).get('source_url')
                except Exception:
                    pass
        if not url:
            raise ValueError('Missing url in payload')
        # Try Wikipedia REST API for wikipedia.org/wiki/<Title>
        content = None
        ct = None
        base = None
        parsed = urlsplit(url)
        if 'wikipedia.org' in (parsed.netloc or '') and parsed.path.startswith('/wiki/'):
            try:
                title = unquote(parsed.path.split('/wiki/',1)[1]) or 'page'
                api_base = f"{parsed.scheme}://{parsed.netloc}"
                api_url = api_base + '/api/rest_v1/page/plain/' + quote(title)
                wr = requests.get(api_url, headers={'User-Agent': CRAWL_UA, 'Accept': 'text/plain; charset=utf-8'}, timeout=25)
                if wr.ok and (wr.content or b''):
                    content = wr.content
                    ct = 'text/plain'
                    base = f"{title}.txt"
            except Exception:
                content = None
        if content is None:
            # Merge any per-source headers from config
            extra_headers = {}
            if getattr(j, 'source_id', None):
                try:
                    src = IngestSource.objects.filter(id=j.source_id, created_by=j.created_by).first()
                    if src and isinstance(src.config, dict):
                        extra_headers = src.config.get('headers') or {}
                except Exception:
                    extra_headers = {}
            r = _fetch_url(url, headers=extra_headers, timeout=25)
            content = r.content or b''
            ct = r.headers.get('content-type', 'text/html')
            pth = parsed.path or urlsplit(url).path
            base = _os.path.basename(pth) or 'page.html'
            if '.' not in base:
                base = (base or 'page') + '.html'
        sha = hashlib.sha256(content).hexdigest()
        # Reuse existing file for same URL if present; else fallback to checksum
        rec = rec or (IngestFile.objects
               .filter(uploaded_by=j.created_by, steps_json__contains={'source_url': url})
               .order_by('-uploaded_at')
               .first())
        if rec is None:
            rec = IngestFile.objects.filter(uploaded_by=j.created_by, checksum=sha).order_by('-uploaded_at').first()
        if rec is None:
            # Create file record
            rec = IngestFile.objects.create(
                uploaded_by=j.created_by,
                filename=base,
                content_type=ct,
                size=len(content),
                checksum=sha,
                steps_json={'source_url': url}
            )
        else:
            # Update metadata and checksum
            rec.filename = base
            rec.content_type = ct
            rec.size = len(content)
            rec.checksum = sha
            sj = dict(rec.steps_json or {})
            sj['source_url'] = url
            rec.steps_json = sj
            rec.save(update_fields=['filename','content_type','size','checksum','steps_json'])
        try:
            rec.file.save(base, ContentFile(content), save=True)
        except Exception:
            # Ignore file save issues; we still can index text
            pass
        # Persist back file_id/url into job payload for future re-runs
        try:
            new_payload = dict(j.payload or {})
            new_payload['file_id'] = rec.id
            new_payload.setdefault('url', url)
            j.payload = new_payload
            j.save(update_fields=['payload'])
        except Exception:
            pass

        # Enqueue indexing pipeline (job will be marked success/failed by process_item)
        process_item.delay(rec.id, j.id)
        # Keep job running; update message
        j.status = 'running'
        j.message = f'Fetched {url} -> {base}; indexing queued'
        j.save(update_fields=['status','message'])
    except Exception as e:
        j.status = 'failed'
        j.finished_at = timezone.now()
        j.message = str(e)
        j.save(update_fields=['status','finished_at','message'])
