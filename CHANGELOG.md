# Changelog

## 0.1.1

Fixes found by an independent review, each reproduced first: no more tracebacks on wrongly typed `implementation`, `specification` or unnamed APIs, and malformed Services are skipped; null values count as absent (required fields report them); free-form nodes still check their declared required fields; `status` is accepted at the top level; Services are matched by namespace and a Service with no ports is reported (M008); M011 only flags GitHub raw/blob URLs on a moving branch; duplicate YAML keys are refused; document numbers follow the file and appear in the output when a file holds several Components. 33 tests.

## 0.1.0

First version: twelve checks on Component manifests (schema-based, consistency and judgement rules), English and French messages, text/JSON/Markdown output, schema extractor, 18 tests.
