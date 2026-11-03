"""Exercise the QA harness offline and through a fake OpenAI endpoint."""

from __future__ import annotations

import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from qa_runner import run  # noqa: E402


class QaRunnerTests(unittest.TestCase):
    def test_two_offline_scenarios(self) -> None:
        scenarios = [
            {"id": "catalog", "turns": [{"user": "O que vocês vendem?", "expect": {"category": "overview"}}]},
            {"id": "guitar", "turns": [{"user": "Quais guitarras vocês têm?", "expect": {"category": "guitarras"}}]},
        ]
        with patch.dict(os.environ, {"OPENAI_BASE_URL": ""}, clear=False):
            records, summary = run(scenarios)
        self.assertEqual(2, summary["passed_scenarios"])
        self.assertEqual(["offline", "offline"], [r["turns"][0]["mode"] for r in records])

    def test_two_scenarios_against_fake_openai_server(self) -> None:
        captured: list[dict] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                captured.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                payload = json.dumps({"choices": [{"message": {"content": "Consulta concluída."}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *_args: object) -> None:
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            scenarios = [
                {"id": "product", "turns": [{"user": "Quanto custa o Takamine GD20?", "expect": {}}]},
                {"id": "product-second", "turns": [{"user": "Qual o preço do Yamaha C40?", "expect": {}}]},
            ]
            with patch.dict(os.environ, {"OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}", "AGENT_TOOLS": "1"}):
                records, _ = run(scenarios)
            self.assertEqual(2, len(captured))
            self.assertTrue(all(r["turns"][0]["mode"] == "tools" for r in records))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
