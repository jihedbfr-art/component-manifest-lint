"""Minimal subprocess reproductions for malformed YAML mapping keys."""
import os
import importlib
from unittest.mock import patch
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class MappingKeyRegressionTests(unittest.TestCase):
    def assert_read_error(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "key.yaml"
            path.write_text(text, encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
            for output_format in ("text", "json", "md", "sarif"):
                with self.subTest(format=output_format):
                    result = subprocess.run(
                        [sys.executable, "-m", "component_manifest_lint", str(path), "--format", output_format],
                        env=env, capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("invalid YAML", result.stderr)
                    self.assertIn("mapping key must be hashable", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_list_mapping_key_is_read_error(self):
        self.assert_read_error("{[]: 0}")

    def test_dictionary_mapping_key_is_read_error(self):
        self.assert_read_error("{ {}: 0 }")


class SafeLoaderRegressionTests(unittest.TestCase):
    def test_safe_backends_preserve_dates_merges_and_rejections(self):
        sys.path.insert(0, str(ROOT / "src"))
        import yaml
        from component_manifest_lint import lint as implementation
        backends = (yaml.SafeLoader, getattr(yaml, "CSafeLoader", yaml.SafeLoader))
        try:
            for backend in backends:
                with self.subTest(backend=backend.__name__), patch.object(yaml, "CSafeLoader", backend, create=True):
                    importlib.reload(implementation)
                    loaded = yaml.load("date: 2026-10-19\nbase: &b {x: old}\nvalue: {<<: *b, x: new}\n", Loader=implementation._PlainLoader)
                    self.assertEqual(loaded["date"], "2026-10-19")
                    self.assertEqual(loaded["value"], {"x": "new"})
                    for invalid in ("{a: 1, a: 2}", "{[]: 0}", "{ {}: 0 }", "!!python/object:builtins.object {}"):
                        with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                            implementation.lint_text(invalid)
        finally:
            importlib.reload(implementation)


if __name__ == "__main__":
    unittest.main()
