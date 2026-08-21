from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
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

    def post(self, path, payload, token="test-token", bridge_token=None):
        headers = {"Content-Type": "application/json"}
        if bridge_token is None:
            headers["X-Anime-Bridge-Token"] = token
        else:
            headers["X-Anime-Bridge-Bridge-Token"] = bridge_token
        request = Request(
            f"http://127.0.0.1:{self.server.server_port}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def test_page_and_status_api_use_session_token(self):
        with urlopen(self.server.url, timeout=5) as response:
            page = response.read().decode("utf-8")
        self.assertIn('content="test-token"', page)
        self.assertIn('id="migration-plan"', page)
        self.assertIn('id="rss-batch-plan"', page)
        self.assertIn('href="/bahamut-export.user.js?token=test-token"', page)
        with self.assertRaises(HTTPError) as missing_token:
            urlopen(
                f"http://127.0.0.1:{self.server.server_port}/bahamut-export.user.js",
                timeout=5,
            )
        self.assertEqual(missing_token.exception.code, 403)
        with urlopen(
            f"http://127.0.0.1:{self.server.server_port}/bahamut-export.user.js?token=test-token",
            timeout=5,
        ) as response:
            helper = response.read().decode("utf-8")
        self.assertIn("anime-bridge-bahamut-favorites", helper)
        self.assertIn("GM_xmlhttpRequest", helper)
        self.assertIn(f"127.0.0.1:{self.server.server_port}/api/bahamut/ingest", helper)
        self.assertIn(self.server.controller.browser_bridge_token, helper)
        self.assertNotIn("__ANIME_BRIDGE_BRIDGE_TOKEN__", helper)
        status = self.post("/api/status", {})
        self.assertTrue(status["ok"])
        self.assertEqual(status["result"]["settings"]["integration_folder"], "bangumi1")
        with self.assertRaises(HTTPError) as caught:
            self.post("/api/status", {}, token="wrong")
        self.assertEqual(caught.exception.code, 403)
        self.assertNotIn(
            self.server.controller.browser_bridge_token,
            json.dumps(status, ensure_ascii=False),
        )

    def test_browser_bridge_authenticates_saves_and_triggers_scan(self):
        payload = {
            "format": "anime-bridge-bahamut-favorites",
            "schema_version": 1,
            "exported_at": "2026-08-21T10:00:00.000Z",
            "source_url": "https://ani.gamer.com.tw/mygather.php",
            "pages_scanned": 1,
            "complete": True,
            "warnings": [],
            "favorites": [
                {
                    "title": "测试动画",
                    "href": "https://ani.gamer.com.tw/animeRef.php?sn=123",
                    "sn": 123,
                    "page": 1,
                }
            ],
        }
        with self.assertRaises(HTTPError) as wrong_token:
            self.post("/api/bahamut/ingest", payload, bridge_token="wrong")
        self.assertEqual(wrong_token.exception.code, 403)

        expected_scan = {"count": 4, "output": "candidate.md"}
        with patch.object(
            self.server.controller, "_scan_with_export", return_value=expected_scan.copy()
        ) as scan:
            result = self.post(
                "/api/bahamut/ingest",
                payload,
                bridge_token=self.server.controller.browser_bridge_token,
            )
        self.assertTrue(result["ok"])
        self.assertTrue(result["result"]["automatic_sync"])
        self.assertEqual(result["result"]["pages_scanned"], 1)
        scan.assert_called_once()
        saved = json.loads(
            self.server.controller.latest_bahamut_export_path.read_text(encoding="utf-8")
        )
        self.assertEqual(saved["favorites"][0]["sn"], 123)

    def test_browser_bridge_refuses_incomplete_export(self):
        payload = {
            "format": "anime-bridge-bahamut-favorites",
            "schema_version": 1,
            "exported_at": "2026-08-21T10:00:00.000Z",
            "source_url": "https://ani.gamer.com.tw/mygather.php",
            "pages_scanned": 1,
            "complete": False,
            "warnings": ["pagination changed"],
            "favorites": [],
        }
        with self.assertRaises(HTTPError) as incomplete:
            self.post(
                "/api/bahamut/ingest",
                payload,
                bridge_token=self.server.controller.browser_bridge_token,
            )
        self.assertEqual(incomplete.exception.code, 400)
        self.assertFalse(self.server.controller.latest_bahamut_export_path.exists())

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
        with self.assertRaises(HTTPError) as rss_batch:
            self.post("/api/qbit/batch-apply", {"candidate_path": "candidate.md"})
        self.assertEqual(rss_batch.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
