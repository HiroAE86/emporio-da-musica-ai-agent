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

from unittest.mock import patch

from agent_cli import Evidence, load_evidence, local_answer  # noqa: E402
from order_status import GENERIC_MISMATCH, lookup_order_status  # noqa: E402


class AgentBehaviorTests(unittest.TestCase):
    def test_category_budget_filter_and_empty_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "products.csv"
            csv_path.write_text(
                "product_id,price_brl,name,category_id,description,stock_quantity,status\n"
                "a,599.9,Yamaha C40,5,Violão clássico,3,active\n"
                "b,1200,Tagima Memphis,5,Violão acústico,0,active\n",
                encoding="utf-8",
            )
            with patch("agent_cli.PRODUCTS", csv_path):
                evidence = load_evidence("Quais violões vocês têm até R$ 1.000?")
                empty = load_evidence("Quais violões vocês têm até R$ 100?")
            self.assertIn("Yamaha C40", local_answer("", evidence))
            self.assertIn("R$ 599,90", local_answer("", evidence))
            self.assertIn("disponível", local_answer("", evidence))
            self.assertIn("Nenhum produto", local_answer("", empty))

    def test_policy_answers_use_extracted_text_and_unknown_fails_closed(self) -> None:
        class Page:
            def extract_text(self) -> str:
                return "Endereço Rua 14 de Maio, 3200, CEP 79202-333. Horário de Funcionamento Segunda a Sexta-feira 09:00 às 18:00."

        class Reader:
            pages = [Page()]

        with patch("agent_cli.PdfReader", return_value=Reader()):
            evidence = load_evidence("Qual é o endereço da loja?")
        self.assertIn("Rua 14 de Maio", local_answer("Qual é o endereço?", evidence))
        self.assertIn("Não encontrei", local_answer("Quais formas de pagamento?", evidence))

    def test_local_policy_topics_answer_from_synthetic_policy_text(self) -> None:
        text = (
            "Endereço Rua 14 de Maio, 3200, CEP 79202-333. Horário de Funcionamento "
            "Segunda a Sexta-feira Domingo e Feriados. Formas de Pagamento PIX Boleto Bancário. "
            "Política de Trocas e Devoluções defeito de fabricação 30 (trinta) dias corridos."
        )
        evidence = Evidence("policy", "synthetic.pdf", text)
        questions = {
            "Qual o horário de funcionamento?": "9h às 18h",
            "Quais formas de pagamento aceitam?": "5% de desconto",
            "Como funciona a troca por defeito?": "30 dias corridos",
            "Vocês aceitam devolução de produto com defeito?": "30 dias corridos",
        }
        for question, expected in questions.items():
            with self.subTest(question=question):
                self.assertIn(expected, local_answer(question, evidence))

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
        answer = local_answer(
            "Posso devolver por arrependimento?", Evidence("policy", "policy.pdf", "")
        )
        for term in (
            "7 dias corridos",
            "sem uso",
            "embalagem original",
            "frete",
            "forma de pagamento original",
            "10 dias úteis",
        ):
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
            wrong_phone = lookup_order_status(
                "A-1", "shared@example.test", "222", orders, customers
            )
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
