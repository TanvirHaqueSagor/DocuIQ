from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_type = models.CharField(max_length=20, choices=(('individual', 'Individual'), ('organization', 'Organization')))
    name = models.CharField(max_length=120, blank=True, null=True)
    org_name = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} ({self.account_type})"
