"""Price validation against current, filtered category evidence."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from agent_cli import load_evidence  # noqa: E402
from offline_answers import local_answer  # noqa: E402
from price_grounding import prices_grounded  # noqa: E402
from tool_calling import _dispatch  # noqa: E402


class PriceGroundingTests(unittest.TestCase):
    def test_correct_pairs_and_markdown_are_accepted(self):
        evidence = load_evidence("Quais violões até R$ 500?")
        for answer in (
            "Violões: **Tagima Memphis** — R$ 429,90; **Rozini RC-104** — R$ 459,90",
            "| Tagima Memphis | R$\u00a0429,90 |",
            local_answer("", evidence),
        ):
            with self.subTest(answer=answer):
                self.assertTrue(prices_grounded(answer, evidence.text))

    def test_each_pair_is_checked(self):
        evidence = load_evidence("Quais violões até R$ 500?")
        self.assertFalse(
            prices_grounded(
                "Violões: Tagima Memphis — R$ 429,90; Rozini RC-104 — R$ 429,90", evidence.text
            )
        )
        self.assertFalse(prices_grounded("Violões: Yamaha C40 — R$ 599,90", evidence.text))

    def test_empty_budget_result_does_not_display_over_budget_products(self):
        evidence = load_evidence("Quais guitarras até R$ 500?")
        self.assertIn("Correspondências dentro do limite: 0", evidence.text)
        self.assertNotIn("Fender", local_answer("", evidence))
        self.assertTrue(prices_grounded(local_answer("", evidence), evidence.text))

    def test_float_tool_limit_is_not_interpreted_as_thousands(self):
        result = _dispatch("list_category", {"category": "violao", "max_price": 500.0})
        self.assertIn("Correspondências até R$ 500,00: 2", result)
        self.assertNotIn("Yamaha C40", result)

    def test_budget_catalog_ranges_use_filtered_rows(self):
        evidence = load_evidence("Catálogo até R$ 500")
        self.assertIn("violões: 2 produto(s), de R$ 429,90 a R$ 459,90", evidence.text)
        self.assertNotIn("R$ 599,90", evidence.text)
        self.assertTrue(prices_grounded(local_answer("", evidence), evidence.text))
        self.assertFalse(prices_grounded("Takamine GD20 — R$ 459,90", evidence.text))
