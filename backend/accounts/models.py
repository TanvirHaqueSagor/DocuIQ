from django.db import models
from django.contrib.auth.models import User

from .plan import PLAN_CHOICES, PLAN_ENTERPRISE, PLAN_STARTER

class Organization(models.Model):
    name = models.CharField(max_length=200)
    subdomain = models.SlugField(max_length=63, unique=True)  # e.g. "acme"
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='owned_orgs')
    created_at = models.DateTimeField(auto_now_add=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_STARTER)

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
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_STARTER)

    def __str__(self):
        return f"{self.user.email} ({self.account_type})"


class SalesInquiry(models.Model):
    PLAN_CHOICES = PLAN_CHOICES

    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    company = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=120, blank=True)
    desired_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_ENTERPRISE)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.full_name} <{self.email}> → {self.desired_plan}"
