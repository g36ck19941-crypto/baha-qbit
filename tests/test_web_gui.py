from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from anime_bridge.gui import AnimeBridgeWebServer, WebGUIController


class WebGUITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        settings_path = Path(self.temp.name) / "config.json"
        self.server = AnimeBridgeWebServer(WebGUIController(settings_path), "test-token")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp.cleanup()

    def post(self, path, payload, token="test-token"):
        request = Request(
            f"http://127.0.0.1:{self.server.server_port}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-Anime-Bridge-Token": token},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def test_page_and_status_api_use_session_token(self):
        with urlopen(self.server.url, timeout=5) as response:
            page = response.read().decode("utf-8")
        self.assertIn('content="test-token"', page)
        self.assertIn('id="migration-plan"', page)
        status = self.post("/api/status", {})
        self.assertTrue(status["ok"])
        self.assertEqual(status["result"]["settings"]["integration_folder"], "bangumi1")
        with self.assertRaises(HTTPError) as caught:
            self.post("/api/status", {}, token="wrong")
        self.assertEqual(caught.exception.code, 403)

    def test_remote_qbittorrent_setting_is_refused(self):
        payload = {
            "vault_path": str(Path(self.temp.name) / "Vault"),
            "integration_folder": "bangumi1",
            "formal_root": "C/bangumi",
            "qbit_base_url": "http://192.168.1.8:8080",
        }
        with self.assertRaises(HTTPError) as caught:
            self.post("/api/settings", payload)
        self.assertEqual(caught.exception.code, 400)

    def test_write_endpoint_requires_visible_confirmation(self):
        with self.assertRaises(HTTPError) as caught:
            self.post("/api/obsidian/apply", {"candidate_path": "candidate.md"})
        self.assertEqual(caught.exception.code, 400)
        with self.assertRaises(HTTPError) as migration:
            self.post("/api/migration/apply", {"runner_path": "anime-bridge.exe"})
        self.assertEqual(migration.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
