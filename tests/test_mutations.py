"""Deterministic CLI mutations; the harness uses only the standard library."""
import contextlib
import io
import json
import random
import re
import sys
import tempfile
import time
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from component_manifest_lint import cli

SEED = 20261019
COUNT = 3000
BUDGET_SECONDS = 120  # a guard against hangs: the test is about robustness, and slower machines take 2x CI
OPERATIONS = ("delete", "null", "number", "list", "dict", "string", "duplicate", "empty", "truncate")
FORMATS = ("text", "json", "md", "sarif")
KEY = re.compile(r"^(\s*(?:-\s+)?[^:#\n]+):(?:\s.*)?$")
VALUES = {
    "null": ("null",),
    "number": ("0", "-1", "1.5", "1e300"),
    "list": ("[]", "[null, 1, {}]", "[[]]"),
    "dict": ("{}", "{x: null}", "{[]: null}", "{ {}: 0 }"),
    "string": tuple(json.dumps(s) for s in ("", "changed", "é # [] :", "null", "{x}")),
}


def subtree_end(lines, start):
    indent = len(lines[start]) - len(lines[start].lstrip())
    end = start + 1
    while end < len(lines) and len(lines[end]) - len(lines[end].lstrip()) > indent:
        end += 1
    return end


def mutate(text, operation, rng):
    if operation == "truncate":
        return text[:rng.randrange(len(text))]
    lines = text.splitlines(keepends=True)
    if operation == "duplicate":
        choices = [i for i, line in enumerate(lines) if line.lstrip().startswith("- ")]
        start = rng.choice(choices)
        end = subtree_end(lines, start)
        lines[end:end] = lines[start:end]
    else:
        choices = [i for i, line in enumerate(lines) if KEY.match(line.rstrip("\n"))]
        if operation == "empty":
            choices = [i for i in choices if lines[i].rstrip().endswith(":")]
        start = rng.choice(choices)
        end = subtree_end(lines, start)
        if operation == "delete":
            lines[start:end] = []
        else:
            prefix = KEY.match(lines[start].rstrip("\n")).group(1)
            value = "{}" if operation == "empty" else rng.choice(VALUES[operation])
            lines[start:end] = [f"{prefix}: {value}\n"]
    return "".join(lines)


class MutationTests(unittest.TestCase):
    def test_fixture_mutations_never_escape_cli(self):
        started = time.perf_counter()
        rng = random.Random(SEED)
        fixtures = [(p.name, p.read_text(encoding="utf-8")) for p in sorted((ROOT / "fixtures").glob("*.yaml"))]
        self.assertTrue(fixtures)
        counts, statuses = Counter(), Counter()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mutated.yaml"
            with path.open("w", encoding="utf-8") as writer:
                for index in range(COUNT):
                    name, original = fixtures[index % len(fixtures)]
                    operation = OPERATIONS[index % len(OPERATIONS)]
                    text = mutate(original, operation, rng)
                    writer.seek(0)
                    writer.write(text)
                    writer.truncate()
                    writer.flush()
                    out, err = io.StringIO(), io.StringIO()
                    with self.subTest(seed=SEED, case=index, fixture=name, operation=operation, text=text):
                        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                            status = cli.main([str(path), "--format", FORMATS[index % len(FORMATS)], "--lang", ("en", "fr")[(index // len(FORMATS)) % 2]])
                        self.assertIn(status, (0, 1, 2))
                        self.assertNotIn("Traceback", out.getvalue() + err.getvalue())
                        if status == 2:
                            self.assertTrue(err.getvalue().strip())
                        counts[operation] += 1
                        statuses[status] += 1
        self.assertEqual(sum(counts.values()), COUNT)
        self.assertEqual(set(counts), set(OPERATIONS))
        elapsed = time.perf_counter() - started
        print(f"mutations={COUNT} seed={SEED} seconds={elapsed:.3f} operations={dict(counts)} exits={dict(statuses)}")
        self.assertLess(elapsed, BUDGET_SECONDS, f"Mutation suite exceeded its {BUDGET_SECONDS}-second budget")


if __name__ == "__main__":
    unittest.main()
