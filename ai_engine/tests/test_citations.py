import unittest

from ai_engine.main import _build_citations, _clean_snippet, _extract_markers


class CitationHelpersTest(unittest.TestCase):
  def test_clean_snippet_returns_direct_substring(self):
    text = "First sentence. Second sentence with more detail! Third?"
    snippet = _clean_snippet(text, limit=40)
    self.assertTrue(text.startswith(snippet))

  def test_extract_markers_returns_unique_ids_in_order_and_citation_block(self):
    answer = "Value grew [S1] then stabilized [S2]. <citations> S3 S2 </citations>"
    markers = _extract_markers(answer)
    self.assertEqual(markers, ["S1", "S2", "S3"])

  def test_build_citations_maps_metadata_and_location(self):
    matches = [
      {
        "metadata": {
          "document_id": "doc-1",
          "title": "Integrated Report",
          "page": 5,
          "chunk_id": "doc-1:p5:c0",
          "source_type": "pdf",
          "url": "https://files.example.com/doc-1#page=5",
        },
        "content": "Revenue increased 18% quarter over quarter.",
        "score": 0.92,
      }
    ]
    citations = _build_citations(matches, limit=2)
    self.assertEqual(len(citations), 1)
    self.assertEqual(citations[0].doc_id, "doc-1")
    self.assertEqual(citations[0].page, 5)
    self.assertEqual(citations[0].source_type, "pdf")
    self.assertEqual(citations[0].url, "https://files.example.com/doc-1#page=5")
    self.assertTrue(citations[0].snippet.startswith("Revenue increased"))

  def test_build_citations_does_not_guess_page(self):
    matches = [
      {
        "metadata": {
          "document_id": "doc-2",
          "title": "Web Capture",
          "chunk": 0,
          "source_type": "web",
          "url": "https://example.com/page",
        },
        "content": "Inline text without page numbers.",
        "score": 0.7,
      }
    ]
    citations = _build_citations(matches, limit=1)
    self.assertIsNone(citations[0].page)
    self.assertEqual(citations[0].source_type, "web")

  def test_build_citations_handles_db_metadata(self):
    matches = [
      {
        "metadata": {
          "document_id": "db-1",
          "doc_title": "orders",
          "source_type": "db",
          "table": "orders",
          "row_id": "123",
          "column": "status",
        },
        "content": "status: shipped, id: 123",
        "score": 0.42,
      }
    ]
    citations = _build_citations(matches, limit=1)
    c = citations[0]
    self.assertEqual(c.table, "orders")
    self.assertEqual(c.row_id, "123")
    self.assertEqual(c.column, "status")


if __name__ == "__main__":
  unittest.main()
