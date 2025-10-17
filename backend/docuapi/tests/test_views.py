from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate, APITestCase

from docuapi.views import ProtectedView, FileUploadView


class DocuApiViewTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="tester@example.com",
            email="tester@example.com",
            password="StrongPass123",
        )
        self.factory = APIRequestFactory()

    def test_protected_view_requires_auth(self):
        request = self.factory.get("/api/protected/")
        response = ProtectedView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_view_authorized_user(self):
        request = self.factory.get("/api/protected/")
        force_authenticate(request, user=self.user)
        response = ProtectedView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "You are authenticated.")

    def test_file_upload_requires_file(self):
        request = self.factory.post("/api/upload/", data={}, format="multipart")
        force_authenticate(request, user=self.user)
        response = FileUploadView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_file_upload_successful(self):
        upload = SimpleUploadedFile("test.txt", b"hello world", content_type="text/plain")
        request = self.factory.post("/api/upload/", data={"file": upload}, format="multipart")
        force_authenticate(request, user=self.user)
        response = FileUploadView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["filename"], "test.txt")
