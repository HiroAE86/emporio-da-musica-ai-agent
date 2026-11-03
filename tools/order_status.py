"""Verify and return limited order status locally."""

from __future__ import annotations

import csv
import getpass
import os
from pathlib import Path

from project_paths import ROOT, resolve_data_dir

DATA = resolve_data_dir()
SAMPLE_DATA = ROOT / "examples" / "fixtures"


def is_order_request(question: str) -> bool:
    query = question.casefold()
    return "pedido" in query and any(
        term in query for term in ("status", "rastre", "andamento", "onde")
    )


def _order_files() -> tuple[Path, Path] | None:
    configured = os.getenv("ORDER_DATA_DIR")
    data_dir = Path(configured) if configured else DATA
    orders = next(data_dir.glob("*orders.csv"), None)
    customers = next(data_dir.glob("*customers.csv"), None)
    if orders and customers:
        return orders, customers
    if configured:
        return None
    orders = next(SAMPLE_DATA.glob("*orders.csv"), None)
    customers = next(SAMPLE_DATA.glob("*customers.csv"), None)
    return (orders, customers) if orders and customers else None


def answer_order_status() -> str:
    try:
        order_id = input("Número do pedido: ").strip()
        email = getpass.getpass("E-mail cadastrado: ").strip().casefold()
    except (EOFError, KeyboardInterrupt):
        return "Consulta cancelada."
    if not order_id or not email:
        return "Informe o número do pedido e o e-mail cadastrado."
    files = _order_files()
    if files is None:
        return "Não consegui consultar pedidos agora. Fale com a equipe da loja."
    orders_path, customers_path = files
    try:
        with customers_path.open(encoding="utf-8-sig", newline="") as file:
            customers = {
                row["customer_id"]: row for row in csv.DictReader(file) if row.get("customer_id")
            }
        with orders_path.open(encoding="utf-8-sig", newline="") as file:
            matches = [
                row for row in csv.DictReader(file) if row.get("order_id", "").strip() == order_id
            ]
        if len(matches) != 1:
            return "Não encontrei um pedido com esses dados. Confira e tente novamente."
        order = matches[0]
        customer = customers.get(order.get("customer_id", ""))
        if not customer or customer.get("email", "").strip().casefold() != email:
            return "Não encontrei um pedido com esses dados. Confira e tente novamente."
        status = order.get("status", "").strip() or "não informado"
        delivery = order.get("estimated_delivery", "").strip() or "não informada"
        source = orders_path.name
        return f"Status do pedido: {status}. Previsão de entrega: {delivery}. Fonte: {source}."
    except (OSError, KeyError, csv.Error):
        return "Não consegui consultar pedidos agora. Fale com a equipe da loja."
