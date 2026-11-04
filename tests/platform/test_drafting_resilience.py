import unittest
from src.platform.drafting.citations import parse_citations
from src.platform.drafting.types import SourceSnapshot


class DraftingResilienceTests(unittest.TestCase):
    def setUp(self):
        self.source = SourceSnapshot(
            id='00000000-0000-0000-0000-000000000001',
            version='1',
            content_hash='a' * 64,
            title='Sample Source',
            origin='https://example.com/source',
            text='We observe that deep representations improve classification accuracy on noisy inputs.',
            is_public=True,
            proposal_id=None
        )

    def test_parse_citations_with_markdown_fences(self):
        raw_llm = f"""```json
{{
  "text": "Prior work shows improved resilience [00000000-0000-0000-0000-000000000001].",
  "citations": [
    {{
      "source_id": "00000000-0000-0000-0000-000000000001",
      "quote": "deep representations improve classification accuracy"
    }}
  ],
  "insufficient_evidence": false
}}
```"""
        text, citations, insufficient = parse_citations(raw_llm, (self.source,))
        self.assertFalse(insufficient)
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0].source_id, self.source.id)
        self.assertEqual(citations[0].quote, "deep representations improve classification accuracy")

    def test_parse_citations_with_preamble_and_thought(self):
        raw_llm = f"""Here is the generated proposal section:
{{
  "text": "Our approach builds on [00000000-0000-0000-0000-000000000001].",
  "citations": [
    {{
      "source_id": "00000000-0000-0000-0000-000000000001",
      "quote": "deep representations improve classification accuracy on noisy inputs"
    }}
  ],
  "insufficient_evidence": false
}}
I hope this meets the requirements."""
        text, citations, insufficient = parse_citations(raw_llm, (self.source,))
        self.assertFalse(insufficient)
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0].source_id, self.source.id)
