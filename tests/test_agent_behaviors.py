"""Offline behavior checks over isolated, synthetic source files."""

from __future__ import annotations

import os
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from unittest.mock import patch

from agent_cli import Evidence, load_evidence, local_answer, model_answer, print_response  # noqa: E402
from offline_answers import carry_over  # noqa: E402
from order_status import GENERIC_MISMATCH, lookup_order_status  # noqa: E402
from tool_calling import run_tool_agent  # noqa: E402


class AgentBehaviorTests(unittest.TestCase):
    def _tool_server(self, responses: list[dict[str, object]]):
        captured: list[dict[str, object]] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                captured.append(body)
                response = responses[min(len(captured) - 1, len(responses) - 1)]
                encoded = json.dumps(response).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def log_message(self, *_args: object) -> None:
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        return server, captured

    def test_model_prompt_directs_general_knowledge_to_refuse(self) -> None:
        server, captured = self._tool_server(
            [{"choices": [{"message": {"content": "Oi! Como posso ajudar com a loja?"}}]}]
        )
        with patch.dict(os.environ, {"OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}"}):
            run_tool_agent("Oi")
        system_prompt = captured[0]["messages"][0]["content"]
        self.assertIn("claramente sobre conhecimento geral", system_prompt)

    def test_tool_agent_preloads_catalog_overview_for_small_models(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "products.csv"
            csv_path.write_text(
                "product_id,price_brl,name,category_id,description,stock_quantity,status\n"
                "a,599.9,Yamaha C40,5,Violão clássico,3,active\n"
                "b,5400,Fender Stratocaster,6,Guitarra elétrica,2,active\n",
                encoding="utf-8",
            )
            server, captured = self._tool_server(
                [{"choices": [{"message": {"content": "Vendemos violões: 1; guitarras: 1."}}]}]
            )
            with (
                patch("agent_cli.PRODUCTS", csv_path),
                patch.dict(
                    os.environ, {"OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}"}
                ),
            ):
                answer = run_tool_agent("Oi, o que vocês vendem?")
            messages = captured[0]["messages"]
            self.assertIn("violões: 1 produto(s)", messages[-1]["content"])
            self.assertIn("guitarras: 1 produto(s)", messages[-1]["content"])
            self.assertIn("Vendemos violões", str(answer))

    def test_tool_agent_retrieves_explicit_guitar_category_after_violin_followup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "products.csv"
            csv_path.write_text(
                "product_id,price_brl,name,category_id,description,stock_quantity,status\n"
                "a,599.9,Yamaha C40,5,Violão clássico,3,active\n"
                "b,5400,Fender Stratocaster,6,Guitarra elétrica,2,active\n",
                encoding="utf-8",
            )
            server, captured = self._tool_server(
                [{"choices": [{"message": {"content": "Resposta incorreta do modelo."}}]}]
            )
            with (
                patch("agent_cli.PRODUCTS", csv_path),
                patch.dict(
                    os.environ, {"OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}"}
                ),
            ):
                first, previous = print_response("Quais violões vocês têm?")
                guitar, previous = print_response("e guitarra?", history=[], previous=previous)
                corrected_answer, corrected = print_response(
                    "Eu disse guitarra, não violão", history=[], previous=previous
                )
            self.assertIn("Categoria: violões", first)
            self.assertIn("Categoria: guitarras", guitar)
            self.assertIn("Fender Stratocaster", guitar)
            self.assertNotIn("Yamaha C40", guitar)
            self.assertIn("Categoria: guitarras", corrected.text)
            self.assertIn("Fender Stratocaster", corrected_answer)
            self.assertEqual([], captured)

    def test_tool_agent_dispatches_across_multiple_rounds(self) -> None:
        first = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "c1",
                                "type": "function",
                                "function": {
                                    "name": "search_products",
                                    "arguments": '{"query":"Takamine GD20"}',
                                },
                            }
                        ]
                    }
                }
            ]
        }
        second = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "c2",
                                "type": "function",
                                "function": {
                                    "name": "list_category",
                                    "arguments": '{"category":"violao","max_price":1000}',
                                },
                            }
                        ]
                    }
                }
            ]
        }
        third = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "c3",
                                "type": "function",
                                "function": {
                                    "name": "read_policy",
                                    "arguments": '{"section":"hours"}',
                                },
                            }
                        ]
                    }
                }
            ]
        }
        final = {
            "choices": [
                {
                    "message": {
                        "content": "O atendimento funciona de segunda a sexta, das 9h às 18h."
                    }
                }
            ]
        }
        server, captured = self._tool_server([first, second, third, final])
        with patch.dict(os.environ, {"OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}"}):
            answer = run_tool_agent("Qual o preço e horário? ")
        self.assertIn("O atendimento funciona", str(answer))
        self.assertEqual(4, len(captured))
        self.assertIn("Takamine GD20", str(captured[1]["messages"]))
        self.assertIn("Yamaha C40", str(captured[2]["messages"]))
        self.assertIn("## 2. Horário de Funcionamento", str(captured[3]["messages"]))

    def test_bad_and_unknown_tool_arguments_are_returned_safely(self) -> None:
        def tool_call(name: str, args: str) -> dict[str, object]:
            return {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "id": "c1",
                                    "type": "function",
                                    "function": {"name": name, "arguments": args},
                                }
                            ]
                        }
                    }
                ]
            }

        final = {"choices": [{"message": {"content": "Não consegui consultar essa informação."}}]}
        for call, expected in (
            (tool_call("list_category", "[]"), "Invalid arguments"),
            (tool_call("no_such_tool", "{}"), "Unknown tool"),
            (tool_call("list_category", "not-json"), "Invalid arguments"),
        ):
            with self.subTest(expected=expected):
                server, captured = self._tool_server([call, final])
                with patch.dict(
                    os.environ, {"OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}"}
                ):
                    run_tool_agent("Quero consultar")
                self.assertIn(expected, str(captured[1]["messages"]))
                server.shutdown()
                server.server_close()

    def test_tool_payload_redacts_customer_contact_data(self) -> None:
        final = {
            "choices": [{"message": {"content": "Posso ajudar com o pedido após a verificação."}}]
        }
        server, captured = self._tool_server([final])
        history = [{"role": "user", "content": "meu email ana@example.test e telefone 67999990000"}]
        with patch.dict(os.environ, {"OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}"}):
            run_tool_agent(
                "Pedido TESTE-100, email ana@example.test, telefone 67999990000", history
            )
        request_text = json.dumps(captured[0])
        self.assertNotIn("ana@example.test", request_text)
        self.assertNotIn("67999990000", request_text)
        self.assertNotIn("TESTE-100", request_text)
        self.assertIn("[redacted email]", request_text)

    def test_order_tool_keeps_verification_data_local(self) -> None:
        call = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "order-check",
                                "type": "function",
                                "function": {"name": "check_order_status", "arguments": "{}"},
                            }
                        ]
                    }
                }
            ]
        }
        final = {"choices": [{"message": {"content": "Seu pedido foi enviado."}}]}
        server, captured = self._tool_server([call, final])
        env = {
            "OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}",
            "ORDER_DATA_DIR": str(ROOT / "examples/fixtures"),
        }
        with (
            patch.dict(os.environ, env),
            patch("builtins.input", return_value="TESTE-100"),
            patch(
                "order_status.getpass.getpass", side_effect=["cliente@example.test", "67999990000"]
            ),
        ):
            run_tool_agent("Consulte meu pedido")
        tool_content = str(captured[1]["messages"][-1]["content"])
        self.assertEqual(
            "Status do pedido: enviado. Previsão de entrega: 2026-11-05.", tool_content
        )
        request_text = json.dumps(captured[1])
        self.assertNotIn("cliente@example.test", request_text)
        self.assertNotIn("67999990000", request_text)
        self.assertNotIn("TESTE-100", request_text)

    def test_tool_unsupported_endpoint_uses_legacy_evidence_path(self) -> None:
        responses = [
            {"choices": [{"message": {"content": "Resposta via caminho antigo."}}]},
            {"choices": [{"message": {"content": "Resposta via caminho antigo."}}]},
        ]
        server, captured = self._tool_server(responses)

        endpoint_calls = [0]

        class UnsupportedHandler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                endpoint_calls[0] += 1
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                captured.append(body)
                if endpoint_calls[0] == 1:
                    self.send_error(400, "tools unsupported")
                    return
                encoded = json.dumps(responses[1]).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def log_message(self, *_args: object) -> None:
                return

        server.shutdown()
        server.server_close()
        server = HTTPServer(("127.0.0.1", 0), UnsupportedHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(
                os.environ, {"OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}"}
            ):
                answer = model_answer(
                    "Quanto custa Takamine GD20?",
                    Evidence(
                        "product",
                        "products.csv",
                        "Name: Takamine GD20\nPrice (BRL): 2199\n"
                        "Stock in supplied CSV snapshot: 2\nStatus: active",
                    ),
                )
            self.assertEqual("Resposta via caminho antigo.", answer)
            self.assertIn("Evidência (product", str(captured[1]["messages"]))
            self.assertNotIn("tools", captured[1])
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

    def test_agent_tools_zero_skips_tool_request(self) -> None:
        response = {"choices": [{"message": {"content": "Legacy answer."}}]}
        server, captured = self._tool_server([response])
        with patch.dict(
            os.environ,
            {"OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}", "AGENT_TOOLS": "0"},
        ):
            answer = model_answer(
                "Quanto custa Takamine GD20?",
                Evidence(
                    "product",
                    "products.csv",
                    "Name: Takamine GD20\nPrice (BRL): 2199\nStock in supplied CSV snapshot: 3\nStatus: active",
                ),
            )
        self.assertEqual("Legacy answer.", answer)
        self.assertNotIn("tools", captured[0])

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

    def test_weak_model_catalog_transcript_is_answered_from_fresh_sorted_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "products.csv"
            csv_path.write_text(
                "product_id,price_brl,name,category_id,description,stock_quantity,status\n"
                "a,399,Giannini Start N-14,5,Violão clássico para iniciantes,2,active\n"
                "b,499,Yamaha C40,5,Violão clássico,1,active\n"
                "c,599.9,Yamaha C70,5,Violão clássico,3,active\n"
                "d,5400,Fender Stratocaster,6,Guitarra elétrica,2,active\n"
                "e,6500,Ibanez Bass,8,Baixo elétrico,1,active\n",
                encoding="utf-8",
            )
            bad = {"choices": [{"message": {"content": "Fender Stratocaster por R$ 20.000."}}]}
            server, captured = self._tool_server([bad])
            questions = [
                "violão para iniciante até 500",
                "e guitarra?",
                "E baixo?",
                "Vocês vendem Baixo?",
                "qual a guitarra mais barata",
            ]
            history: list[dict[str, str]] = []
            previous = None
            answers = []
            try:
                with patch("agent_cli.PRODUCTS", csv_path), patch.dict(
                    os.environ, {"OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}"}
                ):
                    for question in questions:
                        answer, previous = print_response(question, history=history, previous=previous)
                        answers.append(answer)
                        history.extend(
                            [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
                        )
                with patch("agent_cli.PRODUCTS", csv_path):
                    self.assertIn("Correspondências até R$ 500,00: 2", load_evidence(questions[0]).text)
                    self.assertIn("Categoria: guitarras", load_evidence(questions[1]).text)
                    guitar = load_evidence(questions[1]).text
                    self.assertIn("Limite de preço desta consulta: nenhum", guitar)
                    self.assertIn("Fender Stratocaster", guitar)
                    no_guitar_under_limit = load_evidence("guitarra até R$ 500")
                    self.assertIn("Correspondências dentro do limite: 0", no_guitar_under_limit.text)
                    self.assertIn("Fender Stratocaster — R$ 5.400,00", no_guitar_under_limit.text)
                    self.assertIn("Categoria: baixos", load_evidence(questions[2]).text)
                    self.assertIn("Ibanez Bass", load_evidence(questions[3]).text)
                self.assertIn("Fender Stratocaster", answers[-1])
                self.assertNotIn("Ibanez Bass", answers[-1])
                self.assertEqual(0, len(captured), "catalog answers should bypass weak model output")
            finally:
                server.shutdown()
                server.server_close()

    def test_model_product_price_not_in_evidence_falls_back_to_local_answer(self) -> None:
        server, _captured = self._tool_server(
            [{"choices": [{"message": {"content": "Custa R$ 99.999,00."}}]}]
        )
        evidence = Evidence(
            "product",
            "products.csv",
            "Name: Yamaha C40\nPrice (BRL): 599.9\nStock in supplied CSV snapshot: 2\nStatus: active",
        )
        try:
            with patch.dict(os.environ, {"OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}"}):
                answer = model_answer("Quanto custa Yamaha C40?", evidence)
            self.assertIn("Yamaha C40", answer)
            self.assertIn("R$ 599,90", answer)
            self.assertNotIn("99.999", answer)
        finally:
            server.shutdown()

    def test_category_without_budget_and_catalog_overview(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "products.csv"
            csv_path.write_text(
                "product_id,price_brl,name,category_id,description,stock_quantity,status\n"
                "a,599.9,Yamaha C40,5,Violão clássico ideal para iniciantes,3,active\n"
                "b,1699,Yamaha CG162S,5,Violão clássico com tampo sólido,2,active\n"
                "c,5400,Fender Telecaster,6,Guitarra elétrica,1,active\n"
                "d,199.9,Kala KA-15S,7,Ukulele soprano que lembra um violão pequeno,4,active\n",
                encoding="utf-8",
            )
            with patch("agent_cli.PRODUCTS", csv_path):
                beginner = local_answer("", load_evidence("Sou iniciante, qual violão recomenda?"))
                guitars = local_answer("", load_evidence("e guitarra?"))
                overview = local_answer("", load_evidence("O que vocês têm?"))
            self.assertTrue(beginner.index("Yamaha C40") < beginner.index("CG162S"))
            self.assertNotIn("Kala", beginner)
            self.assertIn("R$ 1.699,00", beginner)
            self.assertIn("Fender Telecaster", guitars)
            self.assertIn("guitarras: 1 produto(s)", overview)

    def test_follow_up_reuses_previous_catalog_evidence(self) -> None:
        listed = Evidence("category", "products.csv", "Yamaha C40 — R$ 599,90 — disponível")
        unresolved = Evidence("product", "products.csv", "Não encontrei esse produto.")
        policy = Evidence("policy", "policy.pdf", "texto")
        self.assertIs(carry_over(unresolved, listed), listed)
        self.assertIs(carry_over(None, listed, "quanto custa isso?"), listed)
        self.assertIsNone(carry_over(None, listed))
        self.assertIs(carry_over(policy, listed), policy)

    def test_follow_up_is_explicit_and_keeps_out_of_scope_clear(self) -> None:
        listed = Evidence("category", "products.csv", "Yamaha C40 — R$ 599,90")
        self.assertIs(carry_over(None, listed, "quanto custa isso?"), listed)
        self.assertIs(carry_over(None, listed, "e o mais barato?"), listed)
        self.assertIsNone(carry_over(None, listed, "qual é a capital da França?"))

    def test_price_language_and_low_price_do_not_route_to_bass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "products.csv"
            csv_path.write_text(
                "product_id,price_brl,name,category_id,description,stock_quantity,status\n"
                "a,599.9,Yamaha C40,5,Violão clássico,3,active\n"
                "b,1200,Tagima Memphis,5,Violão acústico,2,active\n",
                encoding="utf-8",
            )
            with patch("agent_cli.PRODUCTS", csv_path):
                thousand = local_answer("", load_evidence("violao até mil reais"))
                range_answer = local_answer("", load_evidence("violao entre 500 e 1000"))
                low_price = load_evidence("quero um preço baixo")
            self.assertIn("Yamaha C40", thousand)
            self.assertNotIn("Tagima", thousand)
            self.assertIn("Yamaha C40", range_answer)
            self.assertNotIn("Tagima", range_answer)
            self.assertIsNone(low_price)

    def test_category_typos_and_computer_battery_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "products.csv"
            csv_path.write_text(
                "product_id,price_brl,name,category_id,description,stock_quantity,status\n"
                "a,599.9,Yamaha C40,5,Violão clássico,3,active\n"
                "b,5400,Fender Stratocaster,6,Guitarra elétrica,2,active\n",
                encoding="utf-8",
            )
            with patch("agent_cli.PRODUCTS", csv_path):
                guitar = local_answer("", load_evidence("guitara"))
                guitar_tilde = local_answer("", load_evidence("violõa"))
                battery = load_evidence("bateria do celular")
            self.assertIn("Fender Stratocaster", guitar)
            self.assertIn("Yamaha C40", guitar_tilde)
            self.assertIsNone(battery)

    def test_unmatched_product_and_empty_model_reply_are_portuguese_and_grounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "products.csv"
            csv_path.write_text(
                "product_id,price_brl,name,category_id,description,stock_quantity,status\n",
                encoding="utf-8",
            )
            with patch("agent_cli.PRODUCTS", csv_path):
                answer = local_answer("violao inexistente", load_evidence("violao inexistente"))
            self.assertIn("Nenhum produto", answer)

    def test_model_receives_evidence_and_empty_reply_falls_back(self) -> None:
        captured: list[dict[str, object]] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                body = self.rfile.read(int(self.headers["Content-Length"]))
                captured.append(json.loads(body))
                response = json.dumps({"choices": [{"message": {"content": "  "}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

            def log_message(self, *_args: object) -> None:
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            evidence = Evidence(
                "product",
                "products.csv",
                "Name: Takamine GD20\nPrice (BRL): 2199\n"
                "Stock in supplied CSV snapshot: 3\nStatus: active",
            )
            with patch.dict(
                os.environ, {"OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}"}
            ):
                answer = model_answer("Quanto custa o Takamine GD20?", evidence)
            self.assertIn("Takamine GD20", str(captured[0]["messages"][-1]["content"]))
            self.assertIn("R$ 2.199,00", answer)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

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
            pending = lookup_order_status("B-1", "shared@example.test", "222", orders, customers)
            wrong_phone = lookup_order_status(
                "A-1", "shared@example.test", "222", orders, customers
            )
            unknown = lookup_order_status("Z-9", "shared@example.test", "111", orders, customers)
            self.assertIn("enviado", good)
            self.assertNotIn("shipped", good)
            self.assertIn("pendente", pending)
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

    def test_polite_short_messages_stay_in_portuguese(self) -> None:
        self.assertIn("Por nada", local_answer("obrigada", None))
        self.assertIn("Até mais", local_answer("tchau", None))
        self.assertIn("Posso ajudar", local_answer("🎸", None))


if __name__ == "__main__":
    unittest.main()
