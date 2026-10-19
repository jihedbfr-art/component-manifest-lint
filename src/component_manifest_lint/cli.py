"""Command line: component-manifest-lint FILE [FILE ...]"""
import argparse
from functools import lru_cache
import json
import sys
from pathlib import Path

from .lint import ERROR, WARN, lint_text
from .sarif import report

LABELS = {
    "en": {"head": "| File | Rule | Severity | Where | Message |", "none": "No findings.", "nocomp": "no Component found in {path}"},
    "fr": {"head": "| Fichier | Règle | Gravité | Où | Message |", "none": "Aucun constat.", "nocomp": "aucun Component trouvé dans {path}"},
}


@lru_cache(maxsize=1)
def _parser():
    parser = argparse.ArgumentParser(prog="component-manifest-lint",
                                     description="Check Component manifests (YAML) against the published schema. Offline.")
    parser.add_argument("files", nargs="+")
    parser.add_argument("--lang", choices=("en", "fr"), default="en")
    parser.add_argument("--format", choices=("text", "json", "md", "sarif"), default="text")
    parser.add_argument("--fail-on", choices=("error", "warn", "never"), default="error")
    return parser


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)
    rows, sarif_rows, status = [], [], 0
    for name in args.files:
        path = Path(name)
        try:
            results, count = lint_text(path.read_text(encoding="utf-8-sig"))
        except OSError as error:
            print(f"error: cannot read {path}: {error.strerror or error}", file=sys.stderr)
            return 2
        except ValueError as error:
            print(f"error: {path}: {error}", file=sys.stderr)
            return 2
        if count == 0:
            print("warning: " + LABELS[args.lang]["nocomp"].format(path=path), file=sys.stderr)
        sarif_rows.extend((path, index, finding) for index, finding in results)
        rows.extend((f"{path}#{index}" if count > 1 else str(path), index, finding) for index, finding in results)
    bad = {"error": (ERROR,), "warn": (ERROR, WARN), "never": ()}[args.fail_on]
    if any(f.severity in bad for _, _, f in rows):
        status = 1
    if args.format == "sarif":
        print(json.dumps(report(sarif_rows, args.lang), ensure_ascii=False, indent=2))
    elif args.format == "json":
        print(json.dumps([{"file": p, "document": i, "rule": f.rule, "severity": f.severity, "where": f.where,
                           "message": f.message(args.lang)} for p, i, f in rows], ensure_ascii=False, indent=2))
    elif args.format == "md":
        print(LABELS[args.lang]["head"] + "\n|---|---|---|---|---|")
        for p, _, f in rows:
            print(f"| {p} | {f.rule} | {f.severity} | `{f.where}` | {f.message(args.lang)} |")
    else:
        for p, _, f in rows:
            print(f"{f.severity.upper():5} {f.rule} {p} {f.where}: {f.message(args.lang)}")
        if not rows:
            print(LABELS[args.lang]["none"])
    return status


if __name__ == "__main__":
    sys.exit(main())
