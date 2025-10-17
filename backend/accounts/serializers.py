from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from .models import UserProfile, Organization, SalesInquiry
from .plan import PLAN_CHOICES

User = get_user_model()

ACCOUNT_TYPES = (('individual', 'Individual'), ('organization', 'Organization'))

class RegisterSerializer(serializers.ModelSerializer):
    account_type = serializers.ChoiceField(choices=ACCOUNT_TYPES)
    name = serializers.CharField(required=False, allow_blank=True)
    org_name = serializers.CharField(required=False, allow_blank=True)
    # new for org:
    subdomain = serializers.SlugField(required=False, allow_blank=True, max_length=63)

    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8, required=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'account_type', 'name', 'org_name', 'subdomain')

    def validate(self, attrs):
        email = (attrs.get('email') or '').strip().lower()
        attrs['email'] = email

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({'email': 'This email is already registered.'})

        acct = attrs.get('account_type')
        if acct == 'individual' and not attrs.get('name'):
            raise serializers.ValidationError({'name': 'Name is required for individual accounts.'})
        if acct == 'organization':
            if not attrs.get('org_name'):
                raise serializers.ValidationError({'org_name': 'Organization name is required.'})
            if not attrs.get('subdomain'):
                raise serializers.ValidationError({'subdomain': 'Subdomain is required for organization.'})
            sd = slugify(attrs['subdomain'])
            if Organization.objects.filter(subdomain=sd).exists():
                raise serializers.ValidationError({'subdomain': 'This subdomain is already taken.'})
            attrs['subdomain'] = sd

        try:
            validate_password(attrs.get('password'))
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': e.messages})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        account_type = validated_data['account_type']
        name = (validated_data.get('name') or '').strip()
        org_name = (validated_data.get('org_name') or '').strip()
        subdomain = validated_data.get('subdomain')

        user = User.objects.create_user(username=email, email=email, password=password)
        if account_type == 'individual' and name:
            user.first_name = name
            user.save(update_fields=['first_name'])

        org = None
        role = 'individual'
        if account_type == 'organization':
            org = Organization.objects.create(name=org_name, subdomain=subdomain, owner=user)
            role = 'org_owner'

        UserProfile.objects.create(
            user=user,
            account_type=account_type,
            name=name if account_type == 'individual' else '',
            org_name=org_name if account_type == 'organization' else '',
            organization=org,
            role=role,
        )
        return user


class SubscriptionPlanUpdateSerializer(serializers.Serializer):
    plan = serializers.ChoiceField(choices=PLAN_CHOICES)


class SalesInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesInquiry
        fields = ('full_name', 'email', 'company', 'role', 'desired_plan', 'message')
