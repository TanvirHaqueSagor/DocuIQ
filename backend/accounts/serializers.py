from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile

class RegisterSerializer(serializers.ModelSerializer):
    account_type = serializers.ChoiceField(choices=[('individual', 'Individual'), ('organization', 'Organization')])
    name = serializers.CharField(required=False, allow_blank=True)
    org_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8, required=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'account_type', 'name', 'org_name')

    def validate(self, data):
        if data['account_type'] == 'individual' and not data.get('name'):
            raise serializers.ValidationError({"name": "Name is required for individual."})
        if data['account_type'] == 'organization' and not data.get('org_name'):
            raise serializers.ValidationError({"org_name": "Organization name is required."})
        return data

    def create(self, validated_data):
        email = validated_data['email'].strip().lower()
        password = validated_data['password']
        account_type = validated_data['account_type']
        name = validated_data.get('name', '')
        org_name = validated_data.get('org_name', '')
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        UserProfile.objects.create(
            user=user,
            account_type=account_type,
            name=name if account_type == "individual" else "",
            org_name=org_name if account_type == "organization" else ""
        )
        return user
