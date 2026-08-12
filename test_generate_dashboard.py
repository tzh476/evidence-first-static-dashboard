import json
import tempfile
import unittest
from pathlib import Path

from generate_dashboard import generate, validate_snapshot


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "source" / "metrics.json"
TIMESTAMP = "2026-08-11T00:00:00+00:00"


class GenerateDashboardTest(unittest.TestCase):
    def test_generates_all_outputs_and_preserves_source_states(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generate(FIXTURE, output, TIMESTAMP)
            payload = json.loads((output / "dashboard.json").read_text())
            self.assertEqual(payload["generated_at"], TIMESTAMP)
            self.assertEqual([item["state"] for item in payload["sources"]], ["ok", "stale", "failed"])
            html = (output / "index.html").read_text()
            self.assertIn("This page is not a fully current view.", html)
            self.assertIn("HTTP 503 from upstream", html)

    def test_rejects_failed_source_without_error(self):
        with self.assertRaisesRegex(ValueError, "failed sources need an error"):
            validate_snapshot({"title": "x", "sources": [{"name": "x", "state": "failed"}]})


if __name__ == "__main__":
    unittest.main()
