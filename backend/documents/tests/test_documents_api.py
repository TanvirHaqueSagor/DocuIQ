from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Organization, UserProfile
from documents.models import Document


class DocumentApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.individual = User.objects.create_user(
            username="ind@example.com",
            email="ind@example.com",
            password="StrongPass123",
        )
        UserProfile.objects.create(
            user=self.individual,
            account_type="individual",
            name="Indy",
        )

        self.owner = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="StrongPass123",
        )
        self.org = Organization.objects.create(name="Acme", subdomain="acme", owner=self.owner)
        UserProfile.objects.create(
            user=self.owner,
            account_type="organization",
            organization=self.org,
            role="org_owner",
        )

        Document.objects.create(title="Global doc", organization=None, created_by=self.individual)
        Document.objects.create(title="Org doc", organization=self.org, created_by=self.owner)

    def auth_headers(self, user):
        token = RefreshToken.for_user(user).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_list_returns_only_global_documents_for_individual(self):
        response = self.client.get(
            "/api/documents/",
            **self.auth_headers(self.individual),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [doc["title"] for doc in response.data]
        self.assertIn("Global doc", titles)
        self.assertNotIn("Org doc", titles)

    def test_list_scoped_to_tenant_subdomain(self):
        response = self.client.get(
            "/api/documents/",
            HTTP_HOST="acme.example.com",
            **self.auth_headers(self.owner),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([doc["title"] for doc in response.data], ["Org doc"])

    def test_create_assigns_tenant_when_using_subdomain(self):
        payload = {"title": "New file", "filename": "new.pdf", "company": "Acme"}
        response = self.client.post(
            "/api/documents/",
            payload,
            format="json",
            HTTP_HOST="acme.example.com",
            **self.auth_headers(self.owner),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc_id = response.data["id"]
        created = Document.objects.get(id=doc_id)
        self.assertEqual(created.organization, self.org)
        self.assertEqual(created.created_by, self.owner)

    def test_delete_respects_tenant_scope(self):
        org_doc = Document.objects.filter(organization=self.org).first()
        response = self.client.delete(
            f"/api/documents/{org_doc.id}",
            **self.auth_headers(self.individual),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
