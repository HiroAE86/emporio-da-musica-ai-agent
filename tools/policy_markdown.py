"""Generate a sectioned Markdown copy of the supplied store policy PDF."""

from __future__ import annotations

import re

from project_paths import ROOT, resolve_policy_pdf
from pypdf import PdfReader

OUTPUT = ROOT / "knowledge" / "policies" / "store.md"
HEADINGS = {
    "1": "Sobre a Empório da Música",
    "2": "Horário de Funcionamento",
    "3": "Formas de Pagamento",
    "4": "Política de Trocas e Devoluções",
    "5": "Política de Frete e Entregas",
    "6": "Promoções e Descontos",
    "7": "Atendimento via WhatsApp",
    "8": "Garantia",
    "9": "Privacidade e Proteção de Dados",
    "10": "Disposições Finais",
}
SUBHEADINGS = {
    "1.1": "Missão",
    "1.2": "Dados da Empresa",
    "3.1": "Regras de Parcelamento",
    "4.1": "Direito de Arrependimento (Compras Online)",
    "4.2": "Trocas por Defeito",
    "4.3": "Trocas por Preferência",
    "4.4": "Itens Não Elegíveis para Troca",
    "5.1": "Entregas na Região Metropolitana de Campo Grande",
    "5.2": "Entregas para Outras Cidades",
    "5.3": "Código de Rastreamento",
    "6.1": "Tipos de Promoção",
    "6.2": "Regras de Promoções",
    "7.1": "Diretrizes de Atendimento",
    "7.2": "Fluxo de Atendimento Padrão",
    "7.3": "Situações Especiais",
    "8.1": "Garantia Legal",
    "8.2": "Garantia do Fabricante",
    "8.3": "O que Não Cobre a Garantia",
}
TABLES = {
    "2": (
        "Dia Horário Segunda a Sexta-feira 09:00 às 18:00 Sábado 09:00 às 13:00 Domingo e Feriados Fechado",
        "\n\nDia | Horário\n--- | ---\nSegunda a Sexta-feira | 09:00 às 18:00\nSábado | 09:00 às 13:00\nDomingo e Feriados | Fechado\n\n",
    ),
    "3": (
        "Forma Condições Observações PIX Pagamento à vista 5% de desconto sobre o preço de tabela Cartão de Débito Pagamento à vista Todas as bandeiras aceitas Cartão de Crédito Até 12x sem juros Parcela mínima de R$ 100,00 Boleto Bancário Pagamento à vista Compensação em até 3 dias úteis",
        "\n\nForma | Condições | Observações\n--- | --- | ---\nPIX | Pagamento à vista | 5% de desconto sobre o preço de tabela\nCartão de Débito | Pagamento à vista | Todas as bandeiras aceitas\nCartão de Crédito | Até 12x sem juros | Parcela mínima de R$ 100,00\nBoleto Bancário | Pagamento à vista | Compensação em até 3 dias úteis\n\n",
    ),
    "5": (
        "Modalidade Prazo Estimado Rastreamento Seguro PAC (Correios) 5 a 12 dias úteis Sim Incluído SEDEX (Correios) 2 a 5 dias úteis Sim Incluído Jadlog (.package) 3 a 8 dias úteis Sim Incluído",
        "\n\nModalidade | Prazo estimado | Rastreamento | Seguro\n--- | --- | --- | ---\nPAC (Correios) | 5 a 12 dias úteis | Sim | Incluído\nSEDEX (Correios) | 2 a 5 dias úteis | Sim | Incluído\nJadlog (.package) | 3 a 8 dias úteis | Sim | Incluído\n\n",
    ),
}


def _clean_body(number: str, body: str) -> str:
    body = re.sub(rf"^{re.escape(HEADINGS[number])}\s+", "", body)
    body = re.sub(r"(?<!\d)(\d+\.\d+)\s+", r"\n### \1 ", body)
    body = re.sub(r"\s+•\s+", "\n- ", body)
    if number in TABLES:
        source, markdown = TABLES[number]
        body = body.replace(source, markdown)
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r" *\n *", "\n", body).replace("\n### ", "\n\n### ")
    for subnumber, title in SUBHEADINGS.items():
        body = body.replace(f"### {subnumber} {title} ", f"### {subnumber} {title}\n\n")
    return body


def extract_policy() -> str:
    pages = [page.extract_text() or "" for page in PdfReader(resolve_policy_pdf()).pages]
    text = " ".join(" ".join(page.split()) for page in pages)
    text = re.sub(r"Empório da Música Manual de Políticas e Procedimentos", "", text)
    text = re.sub(r"Página\s+\d+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    candidates = list(re.finditer(r"(?<!\d)(10|[1-9])\.\s+", text))
    starts = []
    for match in candidates:
        number = match.group(1)
        next_number = str(len(starts) + 1)
        if number == next_number:
            starts.append(match)
        if len(starts) == len(HEADINGS):
            break
    sections = []
    for index, match in enumerate(starts):
        number = match.group(1)
        if number not in HEADINGS:
            continue
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        body = _clean_body(number, text[match.end() : end].strip())
        sections.append(f"## {number}. {HEADINGS[number]}\n\n{body}")
    if len(sections) != len(HEADINGS):
        raise ValueError("Não foi possível identificar todas as seções do manual PDF.")
    return "# Manual de Políticas e Procedimentos\n\n" + "\n\n".join(sections) + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(extract_policy(), encoding="utf-8")
    print(f"Generated {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
