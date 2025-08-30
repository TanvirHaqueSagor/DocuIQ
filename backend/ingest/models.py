from django.conf import settings
from django.db import models
from accounts.models import Organization


class IngestSource(models.Model):
    kind = models.CharField(max_length=20)
    name = models.CharField(max_length=120)
    config = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ('-id',)


class IngestJob(models.Model):
    mode = models.CharField(max_length=20)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, default='queued')
    progress = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.CASCADE)
    source = models.ForeignKey('IngestSource', null=True, blank=True, on_delete=models.SET_NULL, related_name='jobs')

    class Meta:
        ordering = ('-id',)


class IngestFile(models.Model):
    file = models.FileField(upload_to='ingest/%Y/%m/%d/', null=True, blank=True)
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True)
    size = models.BigIntegerField(default=0)
    checksum = models.CharField(max_length=64, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ('-id',)
