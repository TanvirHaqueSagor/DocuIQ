from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from ingest.models import IngestSource, IngestJob


class IngestApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="ingest@example.com",
            email="ingest@example.com",
            password="StrongPass123",
        )

    def auth_headers(self):
        token = RefreshToken.for_user(self.user).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_source_list_returns_only_user_records(self):
        other = get_user_model().objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="StrongPass123",
        )
        IngestSource.objects.create(kind="web", name="Mine", created_by=self.user)
        IngestSource.objects.create(kind="web", name="Theirs", created_by=other)

        response = self.client.get("/api/ingest/sources/", **self.auth_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Mine")

    def test_source_creation_sets_creator(self):
        payload = {"kind": "s3", "name": "Bucket", "config": {"bucket": "docs"}}
        response = self.client.post(
            "/api/ingest/sources/",
            payload,
            format="json",
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        source = IngestSource.objects.get(id=response.data["id"])
        self.assertEqual(source.created_by, self.user)

    def test_job_creation_queues_web_worker(self):
        payload = {"mode": "web", "payload": {"url": "https://example.com"}}
        with patch("ingest.views.process_web_job.delay") as mocked_delay:
            response = self.client.post(
                "/api/ingest/jobs/",
                payload,
                format="json",
                **self.auth_headers(),
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_delay.assert_called_once()
        job = IngestJob.objects.get(id=response.data["id"])
        self.assertEqual(job.created_by, self.user)
        self.assertEqual(job.status, "queued")

    def test_upload_requires_files(self):
        response = self.client.post(
            "/api/ingest/upload/",
            {},
            format="multipart",
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_enqueues_processing(self):
        upload = SimpleUploadedFile("doc.txt", b"test content", content_type="text/plain")
        with patch("ingest.views.process_item.delay") as mocked_delay:
            response = self.client.post(
                "/api/ingest/upload/",
                {"files": [upload]},
                format="multipart",
                **self.auth_headers(),
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_delay.assert_called_once()
