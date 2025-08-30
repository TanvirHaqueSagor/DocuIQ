from django.db import models
from django.conf import settings
from accounts.models import Organization

class Document(models.Model):
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)
    filename = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=120, blank=True)
    year = models.IntegerField(null=True, blank=True)
    file = models.FileField(upload_to='docs/%Y/%m/%d/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
