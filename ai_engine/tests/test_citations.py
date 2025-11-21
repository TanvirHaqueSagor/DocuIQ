import unittest

from ai_engine.main import _build_citations, _clean_snippet, _extract_markers


class CitationHelpersTest(unittest.TestCase):
  def test_clean_snippet_preserves_sentences(self):
    text = "First sentence. Second sentence with more detail! Third?"
    snippet = _clean_snippet(text, limit=80)
    self.assertIn("First sentence.", snippet)
    self.assertIn("Second sentence", snippet)

  def test_extract_markers_returns_unique_ids_in_order(self):
    answer = "Value grew [S1] then stabilized [S2] before rising again [S1]."
    markers = _extract_markers(answer)
    self.assertEqual(markers, ["S1", "S2"])

  def test_build_citations_maps_metadata(self):
    matches = [
      {
        "metadata": {
          "document_id": "doc-1",
          "title": "Integrated Report",
          "page": 5,
          "chunk_id": "doc-1:p5:c0",
          "source_type": "pdf",
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
    self.assertTrue(citations[0].snippet.startswith("Revenue increased"))


if __name__ == "__main__":
  unittest.main()
