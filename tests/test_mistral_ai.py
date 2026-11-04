import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import mistral_ai as ai


def issue(**changes):
    data = {"category": "illegal_dumping", "summary": "Mattress blocks the sidewalk at 16th and Mission.",
            "location": {"lat": 37.7652, "lon": -122.4195}, "report_count": 10, "status": "open",
            "created_at": "2026-11-03T17:00:00Z", "updated_at": "2026-11-03T18:00:00Z",
            "reporters": ["private@example.test"], "report_texts": ["private resident text"]}
    return data | changes


class MistralTests(unittest.TestCase):
    def test_classifies_three_examples(self):
        examples = [
            ("Mattress dumped on the sidewalk at 16th and Mission.", {"category": "illegal_dumping", "summary": "Dumped mattress.", "severity": 3}),
            ("Graffiti on the brick wall on Valencia.", {"category": "graffiti", "summary": "Graffiti on a wall.", "severity": 1}),
            ("Something is wrong around here.", {"needs_clarification": True}),
        ]
        for text, output in examples:
            with self.subTest(text=text), patch.object(ai, "_complete", return_value=output):
                if output.get("needs_clarification"):
                    with self.assertRaises(ai.ClarificationNeeded):
                        ai.classify_report(text)
                else:
                    self.assertEqual(ai.classify_report(text), output)

    def test_rejects_invalid_classification(self):
        valid = {"category": "graffiti", "summary": "Paint on a wall.", "severity": 2}
        for changes in [{"category": "unknown"}, {"severity": True}, {"severity": "3"},
                        {"severity": 6}, {"summary": ""}, {"summary": ["text"]}]:
            with self.subTest(changes=changes), patch.object(ai, "_complete", return_value=valid | changes):
                with self.assertRaises(ai.MistralError):
                    ai.classify_report("Graffiti on the wall.")

    def test_invalid_input_does_not_call_provider(self):
        with patch.object(ai, "_complete") as complete:
            for text in ("", "  ", None, "x" * 6001):
                with self.assertRaises(ValueError):
                    ai.classify_report(text)
            complete.assert_not_called()

    def test_match_requires_boolean(self):
        for decision in (True, False):
            with patch.object(ai, "_complete", return_value={"same_issue": decision}):
                self.assertIs(ai.is_same_issue("Graffiti on shelter.", "Graffiti on wall."), decision)
        for decision in ("false", "yes", 1, None):
            with patch.object(ai, "_complete", return_value={"same_issue": decision}):
                with self.assertRaises(ai.MistralError):
                    ai.is_same_issue("New report", "Existing issue")

    def test_drafts_exclude_reporter_details(self):
        with patch.object(ai, "_complete", return_value={"draft": "Subject: Please review"}) as complete:
            self.assertEqual(ai.draft_authority_email(issue(), "Public Works"), "Subject: Please review")
            payload = complete.call_args.args[1]
            self.assertEqual(payload["report_count"], 10)
            self.assertEqual(payload["updated_at"], issue()["updated_at"])
            self.assertNotIn("reporters", payload)
            self.assertNotIn("private@", json.dumps(payload))
            self.assertNotIn("report_texts", payload)

    def test_resolution_requires_resolved_status(self):
        with patch.object(ai, "_complete", return_value={"draft": "Thank you."}) as complete:
            with self.assertRaises(ValueError):
                ai.draft_resolution_notice(issue())
            complete.assert_not_called()
            self.assertEqual(ai.draft_resolution_notice(issue(status="resolved")), "Thank you.")

    def test_invalid_issue_facts(self):
        for changes in [{"location": {"lat": float("nan"), "lon": 0}}, {"location": {"lat": 0, "lon": 181}},
                        {"report_count": True}, {"report_count": 0}, {"created_at": "yesterday"},
                        {"updated_at": "2026-11-03T16:00:00Z"}, {"created_at": "2026-11-03T17:00:00"}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                ai.draft_authority_email(issue(**changes), "Public Works")

    def test_empty_draft_is_rejected(self):
        with patch.object(ai, "_complete", return_value={"draft": " "}):
            with self.assertRaises(ai.MistralError):
                ai.draft_authority_email(issue(), "Public Works")

    def test_missing_key_fails_without_network(self):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": ""}), patch.object(ai, "urlopen") as network:
            with self.assertRaises(ai.MistralError):
                ai.classify_report("Mattress dumped at the corner.")
            network.assert_not_called()

    @patch.dict(os.environ, {"MISTRAL_API_KEY": "test-key", "MISTRAL_TIMEOUT_SECONDS": "30"})
    def test_wire_payload_and_parsing(self):
        envelope = {"choices": [{"finish_reason": "stop", "message": {"content": '{"same_issue":false}'}}]}
        with patch.object(ai, "urlopen", return_value=io.BytesIO(json.dumps(envelope).encode())) as network:
            self.assertFalse(ai.is_same_issue("Paint on shelter.", "Paint on wall."))
            request = network.call_args.args[0]
            sent = json.loads(request.data)
            self.assertEqual(sent["response_format"], {"type": "json_object"})
            self.assertEqual(request.full_url, ai.API_URL)
            self.assertIn("untrusted", sent["messages"][0]["content"])

    @patch.dict(os.environ, {"MISTRAL_API_KEY": "test-key", "MISTRAL_TIMEOUT_SECONDS": "30"})
    def test_invalid_provider_envelopes(self):
        for envelope in [{}, {"choices": []}, {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]},
                         {"choices": [{"finish_reason": "stop", "message": {"content": "not json"}}]}]:
            with self.subTest(envelope=envelope), patch.object(ai, "urlopen", return_value=io.BytesIO(json.dumps(envelope).encode())):
                with self.assertRaises(ai.MistralError):
                    ai.is_same_issue("One", "Two")

    @patch.dict(os.environ, {"MISTRAL_API_KEY": "test-key", "MISTRAL_TIMEOUT_SECONDS": "30"})
    def test_provider_errors_are_safe(self):
        for error in [HTTPError(ai.API_URL, 401, "private response", {}, None),
                      HTTPError(ai.API_URL, 429, "private response", {}, None),
                      URLError("private host detail"), TimeoutError(), ConnectionResetError()]:
            with self.subTest(error=error), patch.object(ai, "urlopen", side_effect=error):
                with self.assertRaises(ai.MistralError) as context:
                    ai.is_same_issue("One", "Two")
                self.assertNotIn("private", str(context.exception))


if __name__ == "__main__":
    unittest.main()
