"""Check generated policy facts against the supplied PDF text."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).casefold()


class PolicyMarkdownTests(unittest.TestCase):
    def test_key_markdown_facts_are_present_in_the_pdf(self) -> None:
        pdf = next((ROOT / "Desafio Técnico AI Engineer 2026" / "data").glob("*loja.pdf"))
        pdf_text = normalized(" ".join(page.extract_text() or "" for page in PdfReader(pdf).pages))
        wiki = normalized((ROOT / "knowledge/policies/store.md").read_text(encoding="utf-8"))
        for fact in (
            "09:00 às 18:00",
            "Parcelamento em até 3x",
            "exceto abaixo de R$ 50,00",
            "Parcelamento de 4x a 6x: sem juros, parcela mínima de R$ 80,00",
            "Parcelamento de 7x a 12x: sem juros, parcela mínima de R$ 100,00",
            "para compras acima de R$ 2.000,00",
            "5% de desconto sobre o preço de tabela",
            "7 (sete) dias corridos após o recebimento",
            "reembolso será realizado na mesma forma de pagamento original em até 10 dias úteis",
            "frete de devolução é por conta da loja",
            "frete grátis para pedidos acima de R$ 500,00",
            "90 (noventa) dias contra defeitos de fabricação",
            "dados pessoais coletados durante o atendimento",
        ):
            with self.subTest(fact=fact):
                self.assertIn(normalized(fact), pdf_text)
                self.assertIn(normalized(fact), wiki)


if __name__ == "__main__":
    unittest.main()
