"""Cases found by an independent review of 0.1.0. Each one used to crash or give a wrong answer."""
import contextlib
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from component_manifest_lint import cli  # noqa: E402
from component_manifest_lint.lint import lint_text  # noqa: E402

HEAD = "apiVersion: oda.tmforum.org/v1\nkind: Component\n"


def rules(text):
    return [f.rule for _, f in lint_text(text)[0] if f.rule != "M004"]


def api(body):
    return HEAD + "spec: {coreFunction: {exposedAPIs: [" + body + "]}}\n"


class RegressionTests(unittest.TestCase):
    def test_wrongly_typed_implementation_and_specification_do_not_crash(self):
        self.assertEqual(rules(api("{name: x, specification: [], implementation: []}")), ["M012"])
        self.assertEqual(rules(api("{name: x, specification: 5}")), ["M012"])

    def test_unnamed_apis_report_the_missing_name_not_a_crash(self):
        self.assertEqual(rules(api("{specification: []}, {specification: []}")), ["M006", "M006"])

    def test_malformed_services_are_skipped(self):
        for text in ("kind: Service\nspec: x\n", "kind: Service\nmetadata: x\n", "kind: Service\nspec: {ports: 5}\n"):
            with self.subTest(text=text):
                self.assertEqual(lint_text(text), ([], 0))

    def test_null_required_values_count_as_absent(self):
        self.assertEqual(rules(api("{name: null, specification: null}")), ["M006", "M006"])

    def test_free_form_node_still_checks_required_fields(self):
        self.assertEqual(rules(HEAD + "spec: {securityFunction: {secretsManagement: {}}}\n"), ["M006", "M006"])

    def test_status_is_accepted_at_the_top_level(self):
        self.assertEqual(rules(HEAD + "status: {}\n"), [])

    def test_service_in_another_namespace_does_not_match(self):
        text = (HEAD + "metadata: {namespace: a}\nspec: {coreFunction: {exposedAPIs: [{name: x, specification: [], implementation: s, port: 80}]}}\n"
                "---\nkind: Service\nmetadata: {name: s, namespace: b}\nspec: {ports: [{port: 80}]}\n")
        self.assertEqual(rules(text), ["M007"])

    def test_service_without_namespace_matches_any(self):
        text = (HEAD + "metadata: {namespace: a}\nspec: {coreFunction: {exposedAPIs: [{name: x, specification: [], implementation: s, port: 80}]}}\n"
                "---\nkind: Service\nmetadata: {name: s}\nspec: {ports: [{port: 80}]}\n")
        self.assertEqual(rules(text), [])

    def test_service_without_ports_is_reported_unless_external_name(self):
        base = HEAD + "spec: {coreFunction: {exposedAPIs: [{name: x, specification: [], implementation: s, port: 80}]}}\n---\nkind: Service\nmetadata: {name: s}\n"
        self.assertEqual(rules(base + "spec: {}\n"), ["M008"])
        self.assertEqual(rules(base + "spec: {type: ExternalName}\n"), [])

    def test_named_ports_and_several_ports(self):
        text = (api("{name: x, specification: [], implementation: s, port: 9000}")
                + "---\nkind: Service\nmetadata: {name: s}\nspec: {ports: [{name: a, port: 80}, {name: b, port: 9000}]}\n")
        self.assertEqual(rules(text), [])

    def test_pinned_url_with_a_main_directory_is_not_a_moving_branch(self):
        pinned = "https://raw.githubusercontent.com/example/repo/0123456789abcdef0123456789abcdef01234567/main/openapi.yaml"
        self.assertEqual(rules(api('{name: x, specification: [{url: "' + pinned + '"}]}')), [])
        moving = "https://raw.githubusercontent.com/example/repo/main/openapi.yaml"
        self.assertEqual(rules(api('{name: x, specification: [{url: "' + moving + '"}]}')), ["M011"])

    def test_duplicate_keys_are_refused(self):
        with self.assertRaisesRegex(ValueError, "duplicate key 'spec'"):
            lint_text(HEAD + "spec: {a: 1}\nspec: {}\n")

    def test_anchors_and_merge_keys_still_work(self):
        text = HEAD + "spec:\n  coreFunction:\n    exposedAPIs:\n      - &base {name: a, specification: []}\n      - {<<: *base, name: b}\n"
        self.assertEqual(rules(text), [])

    def test_document_numbering_follows_the_file(self):
        results, _ = lint_text("---\n---\n" + HEAD)
        self.assertEqual({index for index, _ in results}, {1})

    def test_several_components_are_told_apart_in_the_output(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "two.yaml"
            path.write_text(HEAD + "---\n" + HEAD, encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                cli.main([str(path), "--fail-on", "never"])
        self.assertIn("two.yaml#0", out.getvalue())
        self.assertIn("two.yaml#1", out.getvalue())


if __name__ == "__main__":
    unittest.main()
