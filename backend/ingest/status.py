from django.utils import timezone
from django.db import DatabaseError

ALLOWED_CHAIN = [
    'QUEUED', 'FETCHING', 'NORMALIZING', 'CHUNKING', 'EMBEDDING', 'INDEXING', 'READY'
]
TERMINALS = {'READY', 'PARTIAL_READY', 'FAILED', 'CANCELLED', 'DELETED'}
RETRYABLE = {'RATE_LIMIT', 'TIMEOUT', 'EMBED_ERROR', 'INDEX_ERROR', 'STORAGE_ERROR'}

def _can_transition(cur, new):
    cur = (cur or '').upper() or 'QUEUED'
    new = (new or '').upper()
    if new in {'FAILED', 'CANCELLED'}:
        return True
    if cur in {'DELETED'}:
        return False
    if cur in {'READY', 'PARTIAL_READY'} and new == 'DELETED':
        return True
    # forward-only along chain
    try:
        return ALLOWED_CHAIN.index(new) >= ALLOWED_CHAIN.index(cur)
    except ValueError:
        # allow PARTIAL_READY from INDEXING/EMBEDDING
        if new == 'PARTIAL_READY' and cur in {'EMBEDDING', 'INDEXING'}:
            return True
        return False

def set_status(item, new_status, *, error_code=None, error_text=None, patch=None):
    """
    Update item status with forward-only rules, timestamps and metrics merge.
    item: model with fields (status, status_updated_at, error_code, error_text, steps_json, indexed_bool)
    """
    cur = getattr(item, 'status', None)
    if not _can_transition(cur, new_status):
        return False
    item.status = new_status.upper()
    item.status_updated_at = timezone.now()
    if error_code:
        item.error_code = error_code
    if error_text:
        item.error_text = error_text
    if patch:
        base = dict(getattr(item, 'steps_json', {}) or {})
        base.update(patch or {})
        item.steps_json = base
    if item.status in {'READY', 'PARTIAL_READY'}:
        item.indexed_bool = True
    fields = {
        'status': item.status,
        'status_updated_at': item.status_updated_at,
        'error_code': getattr(item, 'error_code', None),
        'error_text': getattr(item, 'error_text', None),
        'steps_json': getattr(item, 'steps_json', {}),
        'indexed_bool': getattr(item, 'indexed_bool', False),
    }
    try:
        item.save(update_fields=list(fields.keys()))
    except DatabaseError:
        # Item might have been deleted concurrently; or UPDATE affected 0 rows.
        # Try a direct queryset update as best-effort; ignore if row is gone.
        try:
            item.__class__.objects.filter(pk=item.pk).update(**fields)
        except Exception:
            pass
    return True
