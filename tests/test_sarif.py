import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from component_manifest_lint import cli
from component_manifest_lint.lint import MESSAGES, lint_text
from component_manifest_lint.sarif import artifact_uri


class SarifTests(unittest.TestCase):
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main([*map(str, args), "--format", "sarif"])
        return code, out.getvalue(), err.getvalue()

    def test_findings_levels_locations_and_rule_catalogue(self):
        path = ROOT / "fixtures/order-desk.weak.yaml"
        expected, _ = lint_text(path.read_text(encoding="utf-8"))
        code, out, err = self.run_cli(path)
        data = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        self.assertEqual(data["version"], "2.1.0")
        run = data["runs"][0]
        self.assertEqual(run["tool"]["driver"]["version"], "0.2.0")
        self.assertEqual({r["id"] for r in run["tool"]["driver"]["rules"]}, set(MESSAGES))
        self.assertTrue(all(r["shortDescription"]["text"] for r in run["tool"]["driver"]["rules"]))
        self.assertEqual(len(run["results"]), len(expected))
        self.assertEqual({r["level"] for r in run["results"]}, {"error", "warning", "note"})
        for result, (document, finding) in zip(run["results"], expected):
            self.assertEqual(result["ruleId"], finding.rule)
            self.assertEqual(result["level"], {"error": "error", "warn": "warning", "info": "note"}[finding.severity])
            location = result["locations"][0]
            self.assertEqual(location["physicalLocation"], {"artifactLocation": {"uri": "fixtures/order-desk.weak.yaml"}})
            self.assertEqual(location["logicalLocations"][0]["fullyQualifiedName"], f"document[{document}].{finding.where}")

    def test_clean_file_has_empty_results(self):
        code, out, _ = self.run_cli(ROOT / "fixtures/order-desk.good.yaml")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["runs"][0]["results"], [])

    def test_french_messages_keep_english_descriptions(self):
        path = ROOT / "fixtures/order-desk.weak.yaml"
        _, en, _ = self.run_cli(path)
        _, fr, _ = self.run_cli(path, "--lang", "fr")
        french = json.loads(fr)["runs"][0]
        self.assertEqual(french["tool"], json.loads(en)["runs"][0]["tool"])
        self.assertEqual([r["message"]["text"] for r in french["results"]], [f.message("fr") for _, f in lint_text(path.read_text(encoding="utf-8"))[0]])

    def test_fail_on_never_preserves_exit_code(self):
        self.assertEqual(self.run_cli(ROOT / "fixtures/order-desk.weak.yaml", "--fail-on", "never")[0], 0)

    def test_read_and_parse_failures_remain_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.yaml"
            for content in (None, "a: [unclosed"):
                if content is not None:
                    path.write_text(content, encoding="utf-8")
                code, out, err = self.run_cli(path)
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertTrue(err)

    def test_multi_document_file_does_not_add_fragment_to_uri(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "two #é.yaml"
            path.write_text("---\n---\nkind: Component\n---\nkind: Component\n", encoding="utf-8")
            _, out, _ = self.run_cli(path)
            results = json.loads(out)["runs"][0]["results"]
            self.assertEqual({r["properties"]["document"] for r in results}, {1, 2})
            self.assertTrue(all(r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == path.as_uri() for r in results))

    def test_relative_uri_encodes_reserved_characters(self):
        self.assertEqual(artifact_uri(Path.cwd() / "fixtures" / "a #é%.yaml"), "fixtures/a%20%23%C3%A9%25.yaml")


if __name__ == "__main__":
    unittest.main()
