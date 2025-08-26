from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from .models import UserProfile

User = get_user_model()

ACCOUNT_TYPES = (('individual', 'Individual'), ('organization', 'Organization'))

class RegisterSerializer(serializers.ModelSerializer):
    # extra fields for profile
    account_type = serializers.ChoiceField(choices=ACCOUNT_TYPES)
    name = serializers.CharField(required=False, allow_blank=True)
    org_name = serializers.CharField(required=False, allow_blank=True)

    # core fields
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8, required=True)

    class Meta:
        model = User
        # আমরা username ইউজ করছি না—email কে username বানাবো
        fields = ('email', 'password', 'account_type', 'name', 'org_name')

    def validate(self, attrs):
        # 1) normalize email
        email = (attrs.get('email') or '').strip().lower()
        attrs['email'] = email

        # 2) email unique? (Django default User এ email unique নয়)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({'email': 'This email is already registered.'})

        # 3) account_type ভিত্তিক আবশ্যক ফিল্ড
        acct = attrs.get('account_type')
        if acct == 'individual' and not attrs.get('name'):
            raise serializers.ValidationError({'name': 'Name is required for individual accounts.'})
        if acct == 'organization' and not attrs.get('org_name'):
            raise serializers.ValidationError({'org_name': 'Organization name is required for organization accounts.'})

        # 4) password validators (numeric only, common passwords, length, ইত্যাদি)
        try:
            validate_password(attrs.get('password'))
        except Exception as e:
            # e লিস্ট/এররসমূহ হতে পারে—DRF friendly বানাই
            raise serializers.ValidationError({'password': list(e)})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        account_type = validated_data['account_type']
        name = validated_data.get('name', '').strip()
        org_name = validated_data.get('org_name', '').strip()

        # username = email (লগইন সহজ করার জন্য)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        # চাইলে first_name এ name সেট করতে পারেন (individual হলে)
        if account_type == 'individual' and name:
            # split করে first/last করতে পারেন—এখানে simple first_name
            user.first_name = name
            user.save(update_fields=['first_name'])

        # Profile create
        UserProfile.objects.create(
            user=user,
            account_type=account_type,
            name=name if account_type == 'individual' else '',
            org_name=org_name if account_type == 'organization' else ''
        )

        return user
