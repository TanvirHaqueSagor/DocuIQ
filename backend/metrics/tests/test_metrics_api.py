from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Organization, UserProfile
from ingest.models import IngestFile
from chats.models import ChatThread, ChatMessage


class MetricsApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(
            username="metrics@example.com",
            email="metrics@example.com",
            password="StrongPass123",
        )
        self.org = Organization.objects.create(name="Acme", subdomain="acme", owner=self.owner)
        UserProfile.objects.create(
            user=self.owner,
            account_type="organization",
            organization=self.org,
            role="org_owner",
        )

        self.other = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="StrongPass123",
        )
        UserProfile.objects.create(
            user=self.other,
            account_type="organization",
            organization=self.org,
            role="org_employee",
        )

        today_doc = IngestFile.objects.create(
            filename="today.pdf",
            uploaded_by=self.owner,
            organization=self.org,
        )
        yesterday_doc = IngestFile.objects.create(
            filename="yesterday.pdf",
            uploaded_by=self.owner,
            organization=self.org,
        )
        yesterday_doc.uploaded_at = timezone.now() - timedelta(days=1)
        yesterday_doc.save(update_fields=["uploaded_at"])

        self.today_doc = today_doc
        self.yesterday_doc = yesterday_doc

        self.thread = ChatThread.objects.create(owner=self.owner, title="Daily chat")
        ChatMessage.objects.create(thread=self.thread, role='user', content='Hello owner today')
        yesterday_msg = ChatMessage.objects.create(thread=self.thread, role='user', content='Yesterday question')
        yesterday_msg.created_at = timezone.now() - timedelta(days=1)
        yesterday_msg.save(update_fields=["created_at"])

    def auth_headers(self):
        token = RefreshToken.for_user(self.owner).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_dashboard_summary_counts_documents_and_users(self):
        response = self.client.get(
            "/api/dashboard/summary",
            HTTP_HOST="acme.example.com",
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_documents"], 2)
        self.assertEqual(response.data["org_users"], 2)
        self.assertEqual(response.data["delta_documents"], 0)  # 1 today minus 1 yesterday

    def test_usage_series_returns_span(self):
        response = self.client.get(
            "/api/analytics/usage?days=3",
            HTTP_HOST="acme.example.com",
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        counts = [row["count"] for row in response.data]
        self.assertTrue(any(c > 0 for c in counts))
