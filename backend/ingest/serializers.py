from rest_framework import serializers
from .models import IngestSource, IngestJob, IngestFile

class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestSource
        fields = ('id', 'kind', 'name', 'config', 'created_at')

class IngestJobSerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()

    class Meta:
        model = IngestJob
        fields = ('id','mode','source','payload','status','state','progress','message','error_text','totals_json','created_at','started_at','finished_at')

    def get_state(self, obj):
        m = str(obj.status or '').lower()
        return {
            'queued': 'QUEUED',
            'running': 'RUNNING',
            'success': 'SUCCEEDED',
            'failed': 'FAILED',
        }.get(m, (obj.state or 'QUEUED'))

class DocumentSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = IngestFile
        fields = (
            'id','title','filename','created_at',
            'status','status_updated_at','error_code','error_text','steps_json','indexed_bool','file_url'
        )

    def get_title(self, obj):
        # Prefer friendly titles for web-fetched items
        try:
            sj = getattr(obj, 'steps_json', {}) or {}
            url = sj.get('source_url')
            if url:
                return f"WEB · {url}"
        except Exception:
            pass
        return obj.filename

    def get_created_at(self, obj):
        # Map uploaded_at -> created_at for API compatibility
        try:
            return obj.uploaded_at
        except AttributeError:
            return None

    def get_status(self, obj):
        # Fallback: if not explicitly set, treat indexed_bool as READY
        s = getattr(obj, 'status', None)
        if s:
            return s
        if getattr(obj, 'indexed_bool', False):
            return 'READY'
        return 'QUEUED'

    def get_file_url(self, obj):
        """Return a usable file URL only if the file actually exists on storage.
        This avoids returning stale paths that 404 after container changes.
        """
        try:
            f = getattr(obj, 'file', None)
            if not f or not getattr(f, 'name', ''):
                return None
            storage = getattr(f, 'storage', None)
            if storage and hasattr(storage, 'exists'):
                if not storage.exists(f.name):
                    return None
            return getattr(f, 'url', None)
        except Exception:
            return None
