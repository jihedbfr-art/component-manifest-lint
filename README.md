<p align="center">
  <img src="assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="120" height="120">
</p>

# component-manifest-lint

[Version française](README.fr.md)

Check a telecom component manifest (the Kubernetes `Component` resource of the Open Digital Architecture Canvas) before it reaches a cluster: unknown or misspelled fields, missing required fields, wrong types, and mismatches between the manifest and its own services. Offline, one dependency (PyYAML), no AI.

> Independent project. Not affiliated with, endorsed by or certified by TM Forum. A clean result says nothing about conformance or certification.

## Why it exists

The published schema for a `Component` has few required fields and does not keep unknown ones, so a misspelled `exposedApis` is not an error: the cluster will most likely just ignore it, and you find out when the component does not expose what you wrote. This tool reads the same published schema and tells you before you deploy. It also checks what the schema cannot: that `implementation` names a real Service and the port matches, that API names are unique, that the specification URLs do not follow a moving branch.

## Quick start

Python 3.10 or later and PyYAML:

```bash
git clone https://github.com/jihedbfr-art/component-manifest-lint.git
cd component-manifest-lint
pip install pyyaml
PYTHONPATH=src python -m component_manifest_lint fixtures/order-desk.weak.yaml
```

Or `pip install .` and run `component-manifest-lint FILE [FILE ...]`. Several documents per file are fine; only `kind: Component` documents are checked (findings in a multi-component file carry the document number, `file#N`), and the Services in the same file are used for the cross-checks. A null value counts as absent, since the cluster prunes nulls. Duplicate keys in a mapping are refused. A Helm template must be rendered first (`helm template`): the tool refuses files that still contain `{{`.

Options: `--lang en|fr` (findings and report labels; read and parse errors stay in English), `--format text|json|md`, `--fail-on error|warn|never` (default `error`). Exit codes: `0` when no finding reaches the `--fail-on` level, `1` otherwise, `2` for an unreadable or invalid file.

## What it checks

| Rule | Level | Based on | Checks |
|---|---|---|---|
| M001 | warn | published schema | a field that the schema of this `apiVersion` does not define |
| M002 | warn | published schema | `apiVersion` is not one of the published versions (`v1`, `v1beta2`, `v1beta3`, `v1beta4`) |
| M006 | error | published schema | a field the schema marks as required is missing |
| M012 | error | published schema | a field has the wrong type (for example `dependentAPIs` is a string) |
| M003 | info | two public examples | label `oda.tmforum.org/componentName` equals `metadata.name` |
| M004 | info | judgement | `componentMetadata` has id, name, version, description |
| M005 | warn | judgement | `componentMetadata.version` looks like MAJOR.MINOR.PATCH |
| M007 | warn | consistency | `implementation` names a Service in the same file (only when the file has Services) |
| M008 | warn | consistency | the API `port` is one of that Service's ports |
| M009 | info | two public examples | the API `path` starts with `/` + the component name |
| M010 | warn | consistency | an API name appears twice in one function section |
| M011 | info | judgement | a specification URL points at `master`, `main` or `HEAD` instead of a commit or tag |

The evidence behind each rule, and the commit the schema was taken from, is in [docs/evidence.md](docs/evidence.md).

## Limits

- Static checks on files. No cluster, no admission webhook, no network: a live Canvas may accept or reject differently.
- The schema file in the package is a snapshot (see the evidence page). Regenerate it with `tools/extract_schema.py` when the published schema changes.
- Free-form parts of the schema (such as secrets management) are not checked inside.
- Judgement rules are suggestions; with `--fail-on error` only schema errors fail the run.

## Tests

```bash
python -m unittest discover -s tests
```

33 tests. Fixtures are invented manifests in `fixtures/`.

## Licence and contact

Code: [Apache License 2.0](LICENSE). Advanced features can be discussed on request: see [COMMERCIAL.md](COMMERCIAL.md).

---

<p align="center">
  <img src="assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="80" height="80"><br>
  <sub>Built and maintained under <b>JihedAiLabs</b>.</sub>
</p>
