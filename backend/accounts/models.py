from django.db import models
from django.contrib.auth.models import User

class Organization(models.Model):
    name = models.CharField(max_length=200)
    subdomain = models.SlugField(max_length=63, unique=True)  # e.g. "acme"
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='owned_orgs')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.subdomain})"

ROLE_CHOICES = (
    ('individual', 'Individual'),
    ('org_owner', 'OrganizationOwner'),
    ('org_employee', 'OrganizationEmployee'),
)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_type = models.CharField(max_length=20, choices=(('individual', 'Individual'), ('organization', 'Organization')))
    name = models.CharField(max_length=120, blank=True, null=True)
    org_name = models.CharField(max_length=200, blank=True, null=True)  # legacy রাখুন
    # ⬇️ নতুন দুইটি ফিল্ড
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='individual')

    def __str__(self):
        return f"{self.user.email} ({self.account_type})"
