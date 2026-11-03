"""Evidence-in-prompt compatibility path for endpoints without tool support."""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from offline_answers import Evidence, local_answer

HISTORY_MESSAGES = 6


def _model_safe(text: str) -> str:
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[redacted email]", text)
    text = re.sub(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)", "[redacted phone]", text)
    return re.sub(
        r"\b((?:pedido|order|ordem)\s*(?:n[ºo.]?\s*)?[:#-]?\s*)[A-Z0-9][A-Z0-9-]{2,}\b",
        r"\1[redacted order id]",
        text,
        flags=re.IGNORECASE,
    )


def answer(
    question: str, evidence: Evidence | None, history: list[dict[str, str]] | None = None
) -> str:
    instructions = (
        "Você atende a Empório da Música. Responda em português brasileiro, com tom informal e profissional. "
        "Use somente as evidências fornecidas. Não invente preço, estoque, regra ou condição. "
        "Ao citar um produto, escreva o nome e o preço exatamente como na evidência. O estoque é uma fotografia do CSV, não tempo real. "
        "Em perguntas sobre arrependimento de compra online, inclua o prazo, as condições do produto, "
        "quem paga o frete de devolução, a forma e o prazo do reembolso, se constarem na evidência. "
        "Se a evidência não responder, diga isso e sugira falar com a equipe. Nunca exponha dados pessoais. "
        "Sem evidência, responda cumprimentos de forma breve; para assuntos fora da loja, não responda a pergunta "
        "e ofereça ajuda com instrumentos, preços, disponibilidade, pedidos e políticas da loja."
    )
    context = (
        "Nenhuma evidência das fontes da loja corresponde a esta mensagem."
        if evidence is None
        else f"Evidência ({evidence.kind}, fonte {evidence.source}):\n{evidence.text}"
    )
    payload = json.dumps(
        {
            "model": os.getenv("OPENAI_MODEL", "lfm3-omni-2b"),
            "messages": [
                {"role": "system", "content": instructions},
                *[
                    {**message, "content": _model_safe(message.get("content", ""))}
                    for message in (history or [])[-HISTORY_MESSAGES:]
                ],
                {
                    "role": "user",
                    "content": f"Pergunta do cliente: {_model_safe(question)}\n\n{context}",
                },
            ],
        }
    ).encode()
    request = Request(
        f"{os.getenv('OPENAI_BASE_URL', '').rstrip('/')}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', 'local')}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            result: dict[str, Any] = json.loads(response.read())
        content = result["choices"][0]["message"]["content"].strip()
        return content or local_answer(question, evidence)
    except (
        HTTPError,
        URLError,
        TimeoutError,
        ValueError,
        KeyError,
        IndexError,
        TypeError,
    ) as error:
        print(
            f"API indisponível ({error}); usando resposta local baseada na fonte.", file=sys.stderr
        )
        return local_answer(question, evidence)
