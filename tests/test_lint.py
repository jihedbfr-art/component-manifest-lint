import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import yaml  # noqa: E402

from component_manifest_lint import cli  # noqa: E402
from component_manifest_lint.lint import SCHEMA, check_component, lint_text  # noqa: E402

FIX = ROOT / "fixtures"
GOOD = (FIX / "order-desk.good.yaml").read_text(encoding="utf-8")
WEAK = (FIX / "order-desk.weak.yaml").read_text(encoding="utf-8")


def rules(text):
    return {f.rule for _, f in lint_text(text)[0]}


def component(**changes):
    doc = [d for d in yaml.safe_load_all(GOOD) if d["kind"] == "Component"][0]
    for dotted, value in changes.items():
        node = doc
        *parents, last = dotted.split("__")
        for part in parents:
            node = node[part]
        node[last] = value
    return doc


class LintTests(unittest.TestCase):
    def test_good_fixture_is_clean(self):
        self.assertEqual(lint_text(GOOD)[0], [])

    def test_weak_fixture_triggers_each_rule_but_the_version_one(self):
        self.assertEqual(rules(WEAK), {"M001", "M003", "M004", "M005", "M006", "M007", "M008", "M009", "M010", "M011", "M012"})

    def test_unknown_apiversion_is_reported_and_schema_skipped(self):
        found = check_component(component(apiVersion="oda.tmforum.org/v2"), {})
        self.assertEqual([f.rule for f in found], ["M002"])

    def test_older_published_version_is_accepted(self):
        self.assertNotIn("M002", {f.rule for f in check_component(component(apiVersion="oda.tmforum.org/v1beta4"), {})})

    def test_typo_in_field_name_is_reported_with_its_path(self):
        doc = component()
        doc["spec"]["coreFunction"]["exposedApis"] = doc["spec"]["coreFunction"].pop("exposedAPIs")
        found = [f for f in check_component(doc, {}) if f.rule == "M001"]
        self.assertEqual([dict(f.params)["field"] for f in found], ["spec.coreFunction.exposedApis"])

    def test_free_form_objects_are_not_checked(self):
        doc = component()
        doc["spec"]["securityFunction"]["secretsManagement"] = {"type": "sidecar", "podSelector": {"a": "b"}, "extra": {"goes": 1}}
        self.assertEqual(check_component(doc, {}), [])  # the published schema keeps unknown fields here

    def test_required_api_fields_are_reported_as_errors(self):
        doc = component()
        del doc["spec"]["coreFunction"]["exposedAPIs"][0]["specification"]
        found = check_component(doc, {})
        self.assertEqual([(f.rule, f.severity) for f in found], [("M006", "error")])

    def test_wrong_type_is_an_error(self):
        doc = component()
        doc["spec"]["coreFunction"]["exposedAPIs"][0]["port"] = "8080"
        self.assertEqual([(f.rule, f.severity) for f in check_component(doc, {})], [("M012", "error")])

    def test_boolean_is_not_accepted_as_integer(self):
        doc = component()
        doc["spec"]["coreFunction"]["exposedAPIs"][0]["port"] = True
        self.assertEqual([f.rule for f in check_component(doc, {})], ["M012"])

    def test_dates_stay_text(self):
        text = GOOD.replace("status: specified", "status: specified\n    publicationDate: 2023-08-22T00:00:00.000Z")
        self.assertEqual(lint_text(text)[0], [])

    def test_service_checks_need_a_service_in_the_file(self):
        doc = component()
        self.assertEqual(check_component(doc, {}), [])
        self.assertEqual([f.rule for f in check_component(doc, {"other": [80]})], ["M007"])

    def test_other_kinds_are_ignored(self):
        results, count = lint_text("apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: x\n")
        self.assertEqual((results, count), ([], 0))

    def test_helm_templates_are_refused_with_a_hint(self):
        with self.assertRaisesRegex(ValueError, "helm template"):
            lint_text("name: {{ .Release.Name }}")

    def test_invalid_yaml_is_a_readable_error(self):
        with self.assertRaisesRegex(ValueError, "invalid YAML"):
            lint_text("a: [unclosed")

    def test_shipped_schema_is_pinned_and_has_four_versions(self):
        self.assertIn("c39da6340dbc", SCHEMA["source"])
        self.assertEqual(sorted(SCHEMA["versions"]), ["v1", "v1beta2", "v1beta3", "v1beta4"])


class CliTests(unittest.TestCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_exit_codes(self):
        self.assertEqual(self.run_cli(str(FIX / "order-desk.good.yaml"))[0], 0)
        self.assertEqual(self.run_cli(str(FIX / "order-desk.weak.yaml"))[0], 1)
        self.assertEqual(self.run_cli(str(FIX / "order-desk.weak.yaml"), "--fail-on", "never")[0], 0)
        code, _, err = self.run_cli(str(FIX / "missing.yaml"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)

    def test_json_french_and_several_files(self):
        _, out, _ = self.run_cli("--lang", "fr", "--format", "json", str(FIX / "order-desk.good.yaml"), str(FIX / "order-desk.weak.yaml"), "--fail-on", "never")
        data = json.loads(out)
        self.assertTrue(all(d["file"].endswith("weak.yaml") for d in data))
        self.assertIn("le champ obligatoire", " ".join(d["message"] for d in data))

    def test_file_without_component_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "x.yaml"
            other.write_text("kind: ConfigMap\n", encoding="utf-8")
            code, _, err = self.run_cli(str(other))
        self.assertEqual(code, 0)
        self.assertIn("no Component found", err)


if __name__ == "__main__":
    unittest.main()
