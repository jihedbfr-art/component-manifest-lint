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

Options: `--lang en|fr` (findings and report labels; read and parse errors stay in English), `--format text|json|md|sarif`, `--fail-on error|warn|never` (default `error`). Exit codes: `0` when no finding reaches the `--fail-on` level, `1` otherwise, `2` for an unreadable or invalid file.

## SARIF output

`--format sarif` writes SARIF 2.1.0 JSON. All twelve rules have English descriptions; result messages follow `--lang`. Levels map from `error`, `warn`, `info` to `error`, `warning`, `note`. Each result contains the file URI and a logical path prefixed with the zero-based YAML document index. No line number is guessed. Files inside the current working directory use relative, percent-encoded URIs; external files use absolute file URIs. Run from the repository root for portable reports.

Copy the following job fragment into your own GitHub Actions workflow after choosing a runner. It installs this checkout and checks an included fixture; replace the fixture path with your manifest. The upload also runs after findings cause exit 1, while the check remains failed. Read or parse errors (exit 2) skip upload and remain failures. This is documentation only; this repository's workflows are unchanged. GitHub upload and alert rendering have not been exercised by this change.

```yaml
permissions:
  contents: read
  security-events: write
steps:
  - uses: actions/checkout@v6
  - run: pip install .
  - name: Check manifests
    id: manifest
    shell: bash
    run: |
      set +e
      component-manifest-lint fixtures/order-desk.weak.yaml --format sarif > results.sarif
      status=$?
      echo "status=$status" >> "$GITHUB_OUTPUT"
      exit "$status"
  - name: Upload SARIF
    if: ${{ !cancelled() && (steps.manifest.outputs.status == '0' || steps.manifest.outputs.status == '1') }}
    uses: github/codeql-action/upload-sarif@v4
    with:
      sarif_file: results.sarif
      category: component-manifest-lint
```

References (accessed 2026-10-18): [GitHub SARIF upload documentation](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/integrate-with-existing-tools/upload-sarif-file), [SARIF 2.1.0 schema](https://json.schemastore.org/sarif-2.1.0.json).


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

44 tests. Fixtures are invented manifests in `fixtures/`.

Mutation counts, the fixed seed and minimized crash inputs are documented in [mutation checks](docs/mutation-testing.md).

## Study path

The ideas behind these checks are explained, with sources and exercises, in the bilingual study path [oda-learning-lab](https://github.com/jihedbfr-art/oda-learning-lab/blob/main/docs/en/05-components-in-practice.md) (Module 5).

## Licence and contact

Code: [Apache License 2.0](LICENSE). Advanced features can be discussed on request: see [COMMERCIAL.md](COMMERCIAL.md).

## Distribution checks

[Distribution checks](DISTRIBUTION.md) — Build and verify the source archive and wheel, then exercise the installed commands outside the checkout.

---

<p align="center">
  <img src="assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="80" height="80"><br>
  <sub>Built and maintained under <b>JihedAiLabs</b>.</sub>
</p>
