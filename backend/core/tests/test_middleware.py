from django.test import SimpleTestCase

from core.middleware import extract_subdomain


class ExtractSubdomainTests(SimpleTestCase):
    def test_root_host_returns_none(self):
        self.assertIsNone(extract_subdomain("example.com", "example.com"))

    def test_known_subdomain_returns_label(self):
        self.assertEqual(extract_subdomain("acme.example.com", "example.com"), "acme")

    def test_non_matching_host_returns_none(self):
        self.assertIsNone(extract_subdomain("example.org", "example.com"))
