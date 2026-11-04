import json
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import ui_server


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), ui_server.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, action, data, origin=None):
        headers = {"Content-Type": "application/json"}
        if origin:
            headers["Origin"] = origin
        return urlopen(Request(self.base + "/api/" + action, data=json.dumps(data).encode(), headers=headers))

    def test_static_page_and_config_do_not_expose_key(self):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "secret-key"}):
            with urlopen(self.base + "/api/config") as response:
                body = response.read().decode()
                self.assertTrue(json.loads(body)["configured"])
                self.assertNotIn("secret-key", body)
        with urlopen(self.base) as response:
            self.assertIn(b"Report it once", response.read())
            self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])

    def test_classify_calls_person_b_contract(self):
        expected = {"category": "graffiti", "summary": "Paint on wall.", "severity": 1}
        with patch.object(ui_server.ai, "classify_report", return_value=expected) as classify:
            with self.post("classify", {"text": "Paint on wall."}) as response:
                self.assertEqual(json.load(response), {"result": expected, "mode": "live"})
            classify.assert_called_once_with("Paint on wall.")

    def test_other_actions_are_wired(self):
        cases = [("match", {"text": "a", "existing_summary": "b"}, "is_same_issue", False, {"same_issue": False}),
                 ("agency", {"issue": {}, "agency": "Public Works"}, "draft_authority_email", "Draft", {"draft": "Draft"}),
                 ("resolution", {"issue": {}}, "draft_resolution_notice", "Notice", {"draft": "Notice"})]
        for action, payload, function, value, expected in cases:
            with self.subTest(action=action), patch.object(ui_server.ai, function, return_value=value):
                with self.post(action, payload) as response:
                    self.assertEqual(json.load(response)["result"], expected)

    def test_cross_origin_calls_are_rejected(self):
        with self.assertRaises(HTTPError) as error:
            self.post("classify", {"text": "Report"}, "https://example.com")
        self.assertEqual(error.exception.code, 403)

    def test_missing_key_and_bad_inputs_are_visible_errors(self):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": ""}):
            with self.assertRaises(HTTPError) as error:
                self.post("classify", {"text": "Mattress at 16th and Mission"})
            self.assertEqual(error.exception.code, 503)
            self.assertIn("MISTRAL_API_KEY", json.load(error.exception)["error"])
        with self.assertRaises(HTTPError) as error:
            self.post("classify", [])
        self.assertEqual(error.exception.code, 400)

    def test_unknown_paths_are_not_served(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base + "/.env")
        self.assertEqual(error.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
