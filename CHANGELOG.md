# Changelog

[Version française](CHANGELOG.fr.md)

## 0.2.1

Fix malformed YAML mapping keys escaping as TypeError: list and dictionary keys now produce a readable parse error and exit 2. Add two subprocess regression tests and a fixed-seed 3,000-input mutation campaign, with the 30-second limit retained. See [mutation checks](docs/mutation-testing.md).

Reuse the CLI parser and per-report file URIs; use the existing accelerated safe YAML loader when available, with the pure Python fallback retained.

## 0.2.0

Add SARIF 2.1.0 output with English rule descriptions, localized findings, file URIs and logical document paths. Exit codes remain unchanged. Add a copyable GitHub Actions upload example without changing workflows. 40 tests.

## 0.1.1

Fixes found by an independent review, each reproduced first: no more tracebacks on wrongly typed `implementation`, `specification` or unnamed APIs, and malformed Services are skipped; null values count as absent (required fields report them); free-form nodes still check their declared required fields; `status` is accepted at the top level; Services are matched by namespace and a Service with no ports is reported (M008); M011 only flags GitHub raw/blob URLs on a moving branch; duplicate YAML keys are refused; document numbers follow the file and appear in the output when a file holds several Components. 33 tests.

## 0.1.0

First version: twelve checks on Component manifests (schema-based, consistency and judgement rules), English and French messages, text/JSON/Markdown output, schema extractor, 18 tests.
