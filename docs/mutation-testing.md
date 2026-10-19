# Mutation checks

[Version française](mutation-testing.fr.md)

Run from the repository root:

```bash
python -m unittest discover -s tests
python -m unittest discover -s tests -p test_mutations.py
python -m unittest discover -s tests -p test_mapping_keys.py
```

The mutation harness uses only the standard library and calls the real `cli.main` against a temporary file. The application still uses its existing PyYAML dependency. The two YAML fixtures supply 3,000 inputs with seed `20261019`: delete a key, replace a value with null/number/list/dictionary/string, duplicate a list item, empty an object, or truncate the text. Types and formats rotate independently; text, JSON, Markdown and SARIF outputs and both message languages are exercised. Malformed inputs are passed to the command, not discarded.

Every call must return 0, 1 or 2 without an uncaught exception. Exit 2 must include a nonempty stderr message. Neither stream may contain `Traceback`. The test prints operation counts, exit counts and elapsed time, and fails above 30 seconds. The fixed seed repeats the same mutations for the same fixture contents and interpreter; it does not exhaust possible inputs.

## Defect reproduced before correction

The duplicate-key check inserted YAML keys into a Python set before the YAML loader could reject keys that cannot be hashed. Lists and dictionaries therefore escaped as `TypeError`. On the 0.2.0 baseline, 176 of the 3,000 mutations hit this single defect. The following independent minimal files also produced tracebacks:

```yaml
{[]: 0}
```

```yaml
{ {}: 0 }
```

Replay either variant from a source checkout:

```bash
python -c "from pathlib import Path; Path('list-key.yaml').write_text('{[]: 0}', encoding='utf-8'); Path('dict-key.yaml').write_text('{ {}: 0 }', encoding='utf-8')"
PYTHONPATH=src python -m component_manifest_lint list-key.yaml
PYTHONPATH=src python -m component_manifest_lint dict-key.yaml
```

Both now return 2, with an `invalid YAML` diagnostic and no traceback. Separate subprocess tests cover each variant in all four output formats. The fix converts only the failed key insertion into a YAML construction error; it does not catch all exceptions at the command boundary.

## Measured scope

On Windows with Python 3.12.0, the unchanged 3,000-case campaign passed in 18.993 seconds on 2026-10-19: 1,115 exits 0, 1,648 exits 1 and 237 exits 2. Delete/null/number each ran 334 times; the other six operations each ran 333 times. Machine load can change the elapsed time. This campaign covers fixture-based YAML mutations, not exhaustive fuzzing, memory exhaustion, arbitrary encodings or every possible YAML feature. No JSON fixture exists in this repository.

The CLI reuses its parser definition and resolves each URI once per report. The accelerated safe CSafeLoader is used when available, with a SafeLoader fallback; text dates, YAML merges, duplicate rejection and unsafe object-tag rejection are tested on both paths. The full timing uses CSafeLoader; the pure-Python fallback timing budget has not been validated. The test holds the temporary writer open and flushes before every real CLI read. No mutation or assertion was removed.

Source consulted 2026-10-19: [PyYAML documentation](https://pyyaml.org/wiki/PyYAMLDocumentation), on safe loaders and constructors.
