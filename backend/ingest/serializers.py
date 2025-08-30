from rest_framework import serializers
from .models import IngestSource, IngestJob, IngestFile

class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestSource
        fields = ('id', 'kind', 'name', 'config', 'created_at')

class IngestJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestJob
        fields = ('id','mode','source','payload','status','progress','created_at')

class DocumentSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = IngestFile
        fields = ('id','title','filename','created_at')

    def get_title(self, obj):
        return obj.filename

    def get_created_at(self, obj):
        # Map uploaded_at -> created_at for API compatibility
        try:
            return obj.uploaded_at
        except AttributeError:
            return None
