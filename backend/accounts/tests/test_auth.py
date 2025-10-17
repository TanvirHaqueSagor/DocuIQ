from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Organization, UserProfile


class AuthTests(APITestCase):
    def setUp(self):
        User = get_user_model()
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

    def auth_headers(self, user):
        access = RefreshToken.for_user(user).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {access}"}

    def test_register_individual_creates_profile(self):
        payload = {
            "email": "newperson@example.com",
            "password": "Secur3Pass!",
            "account_type": "individual",
            "name": "New Person",
        }
        url = reverse("register")
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created = get_user_model().objects.get(email="newperson@example.com")
        profile = UserProfile.objects.get(user=created)
        self.assertEqual(profile.account_type, "individual")
        self.assertEqual(created.first_name, "New Person")

    def test_register_organization_requires_subdomain(self):
        payload = {
            "email": "org@example.com",
            "password": "StrongPass123",
            "account_type": "organization",
            "org_name": "Org Inc",
        }
        url = reverse("register")
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("subdomain", response.data)

    def test_login_returns_tokens_and_org_metadata(self):
        url = reverse("login")
        response = self.client.post(
            url,
            {"email": "owner@example.com", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertEqual(response.data.get("account_type"), "organization")
        self.assertEqual(response.data.get("org_subdomain"), "acme")

    def test_org_employee_creation_enforced_to_owner(self):
        url = reverse("org_employee_create")
        data = {
            "email": "staff@example.com",
            "password": "AnotherPass123",
            "first_name": "Staff",
        }
        headers = self.auth_headers(self.owner)
        response = self.client.post(
            url,
            data,
            format="json",
            HTTP_HOST="acme.example.com",
            **headers,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = get_user_model().objects.get(email="staff@example.com")
        profile = UserProfile.objects.get(user=created)
        self.assertEqual(profile.organization, self.org)
        self.assertEqual(profile.role, "org_employee")

    def test_org_employee_creation_rejects_non_owner(self):
        User = get_user_model()
        member = User.objects.create_user(
            username="member@example.com",
            email="member@example.com",
            password="StrongPass123",
        )
        UserProfile.objects.create(
            user=member,
            account_type="organization",
            organization=self.org,
            role="org_employee",
        )
        headers = self.auth_headers(member)
        response = self.client.post(
            reverse("org_employee_create"),
            {
                "email": "another@example.com",
                "password": "Pass123!@#",
            },
            format="json",
            HTTP_HOST="acme.example.com",
            **headers,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
