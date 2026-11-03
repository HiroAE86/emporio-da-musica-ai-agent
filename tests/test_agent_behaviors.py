"""Offline behavior checks over isolated, synthetic source files."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from agent_cli import Evidence, local_answer  # noqa: E402
from order_status import GENERIC_MISMATCH, lookup_order_status  # noqa: E402


class AgentBehaviorTests(unittest.TestCase):
    def test_product_price_and_stock_from_synthetic_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "products.csv"
            csv_path.write_text(
                "product_id,price_brl,name,category_id,description,stock_quantity,status\n"
                "x,599.9,Yamaha C40,5,Violão,3,active\n",
                encoding="utf-8",
            )
            env = os.environ | {"PRODUCTS_CSV": str(csv_path), "OPENAI_BASE_URL": ""}
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/agent_cli.py"), "Quanto custa Yamaha C40?"],
                capture_output=True,
                text=True,
                env=env,
                check=True,
            )
            self.assertIn("R$ 599,90", result.stdout)
            self.assertIn("disponível", result.stdout)

    def test_regret_policy_fallback_includes_all_answer_terms(self) -> None:
        answer = local_answer("Posso devolver por arrependimento?", Evidence("policy", "policy.pdf", ""))
        for term in ("7 dias corridos", "sem uso", "embalagem original", "frete", "forma de pagamento original", "10 dias úteis"):
            self.assertIn(term, answer)

    def test_duplicate_email_requires_phone_and_keeps_generic_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            customers = Path(directory) / "customers.csv"
            orders = Path(directory) / "orders.csv"
            customers.write_text(
                "customer_id,name,phone,email\n"
                "a,Ana,111,shared@example.test\n"
                "b,Bia,222,shared@example.test\n",
                encoding="utf-8",
            )
            orders.write_text(
                "order_id,customer_id,status,estimated_delivery\n"
                "A-1,a,shipped,2026-11-05\nB-1,b,pending,\n",
                encoding="utf-8",
            )
            good = lookup_order_status("A-1", "shared@example.test", "111", orders, customers)
            wrong_phone = lookup_order_status("A-1", "shared@example.test", "222", orders, customers)
            unknown = lookup_order_status("Z-9", "shared@example.test", "111", orders, customers)
            self.assertIn("shipped", good)
            self.assertEqual(GENERIC_MISMATCH, wrong_phone)
            self.assertEqual(GENERIC_MISMATCH, unknown)

    def test_out_of_scope_uses_local_redirect(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/agent_cli.py"), "Qual é a capital da França?"],
            capture_output=True,
            text=True,
            env=os.environ | {"OPENAI_BASE_URL": ""},
            check=True,
        )
        self.assertIn("Posso ajudar com instrumentos musicais", result.stdout)


if __name__ == "__main__":
    unittest.main()
