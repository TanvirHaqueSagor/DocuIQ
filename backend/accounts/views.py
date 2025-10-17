from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    RegisterSerializer,
    SubscriptionPlanUpdateSerializer,
    SalesInquirySerializer,
)
from .models import UserProfile, Organization
from .plan import (
    PLAN_CHOICES,
    can_manage_plan,
    get_effective_plan,
    get_effective_plan_and_source,
    normalize_plan,
    serialize_plan,
)
from core.permissions import IsInTenant
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken


User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'msg': 'Registration successful!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]  # JWT login-এর জন্য public

    def post(self, request):
        # frontend থেকে আসে: email, password
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''
        if not email or not password:
            return Response({'detail': 'Email and password required'}, status=400)

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({'detail': 'Invalid credentials'}, status=401)

        if not user.check_password(password):
            return Response({'detail': 'Invalid credentials'}, status=401)

        # JWT টোকেন বানান
        refresh = RefreshToken.for_user(user)

        # প্রোফাইল/অর্গ ইনফো
        profile = getattr(user, 'userprofile', None)
        account_type = getattr(profile, 'account_type', 'individual') if profile else 'individual'
        org_subdomain = None
        if profile and getattr(profile, 'organization', None):
            org_subdomain = getattr(profile.organization, 'subdomain', None)

        # UI-তে দেখানোর জন্য name
        name = ''
        if profile and getattr(profile, 'name', ''):
            name = profile.name
        elif getattr(user, 'first_name', ''):
            name = user.first_name
        else:
            name = user.username or (user.email.split('@')[0] if user.email else '')

        plan_code, plan_source = get_effective_plan_and_source(user)
        plan_payload = serialize_plan(plan_code)
        plan_payload['source'] = plan_source

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'name': name,
            },
            'account_type': account_type,
            'org_subdomain': org_subdomain,
            'plan': plan_payload,
        }, status=200)

class MeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        profile = getattr(user, 'userprofile', None)
        plan_code, plan_source = get_effective_plan_and_source(user)
        plan_payload = serialize_plan(plan_code)
        plan_payload['source'] = plan_source
        return Response({
            "id": user.id,
            "email": user.email,
            "username": getattr(user, "username", "") or (user.email.split("@")[0] if user.email else ""),
            "first_name": getattr(user, "first_name", ""),
            "last_name": getattr(user, "last_name", ""),
            "account_type": getattr(profile, "account_type", "individual") if profile else "individual",
            "org_subdomain": getattr(profile.organization, "subdomain", None) if (profile and profile.organization) else None,
            "plan": plan_payload,
        })

# --- Org employee create (Owner only) ---
from rest_framework import generics
from rest_framework import serializers

class OrgEmployeeCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name  = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, v):
        if User.objects.filter(email__iexact=v).exists():
            raise serializers.ValidationError('Email already registered.')
        return v

    def create(self, validated):
        req = self.context['request']
        owner_prof = UserProfile.objects.select_related('organization').get(user=req.user)
        org = owner_prof.organization
        user = User.objects.create_user(
            username=validated['email'],
            email=validated['email'],
            password=validated['password'],
            first_name=validated.get('first_name',''),
            last_name=validated.get('last_name',''),
        )
        UserProfile.objects.create(
            user=user, account_type='organization',
            organization=org, role='org_employee'
        )
        return user

class OrgEmployeeCreateView(generics.CreateAPIView):
    serializer_class = OrgEmployeeCreateSerializer
    permission_classes = [IsAuthenticated, IsInTenant]
    def perform_create(self, serializer):
        prof = UserProfile.objects.filter(user=self.request.user).first()
        if not prof or prof.role != 'org_owner':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only organization owners can add employees.')
        serializer.save()


class SubscriptionPlanView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plan_code, plan_source = get_effective_plan_and_source(request.user)
        payload = serialize_plan(plan_code)
        payload.update({
            'source': plan_source,
            'can_manage': can_manage_plan(request.user),
            'available_plans': [{'code': code, 'label': label} for code, label in PLAN_CHOICES],
        })
        return Response(payload)

    def post(self, request):
        if not can_manage_plan(request.user):
            return Response({'detail': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)

        serializer = SubscriptionPlanUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        desired_plan = normalize_plan(serializer.validated_data['plan'])
        profile = getattr(request.user, 'userprofile', None)
        if profile is None:
            return Response({'detail': 'profile_not_found'}, status=status.HTTP_400_BAD_REQUEST)

        if profile.account_type == 'organization':
            org = getattr(profile, 'organization', None)
            if org is None:
                return Response({'detail': 'organization_not_found'}, status=status.HTTP_400_BAD_REQUEST)
            org.plan = desired_plan
            org.save(update_fields=['plan'])
        else:
            profile.plan = desired_plan
            profile.save(update_fields=['plan'])

        plan_code, plan_source = get_effective_plan_and_source(request.user)
        payload = serialize_plan(plan_code)
        payload['source'] = plan_source
        return Response(payload, status=status.HTTP_200_OK)


class ContactSalesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SalesInquirySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_code = get_effective_plan(request.user)
        inquiry = serializer.save(metadata={
            'user_id': request.user.id,
            'plan_at_submission': serialize_plan(plan_code),
        })

        return Response({
            'id': inquiry.id,
            'created_at': inquiry.created_at.isoformat(),
            'success': True,
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # ফ্রন্টএন্ড বডিতে refresh টোকেন পাঠাবে
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"detail": "refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            # invalid/expired হলেও 205 দিতে পারেন (idempotent)
            pass
        return Response(status=status.HTTP_205_RESET_CONTENT)
    
class LogoutAllView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        tokens = OutstandingToken.objects.filter(user=request.user)
        for t in tokens:
            BlacklistedToken.objects.get_or_create(token=t)
        return Response(status=status.HTTP_205_RESET_CONTENT)
