"""SARIF 2.1.0 serialization using only the standard library."""
from pathlib import Path
from urllib.parse import quote

from . import __version__

DESCRIPTIONS = {
    "M001": "Field absent from the published schema",
    "M002": "Unrecognized API version",
    "M003": "Component name label differs from metadata name",
    "M004": "Incomplete component metadata",
    "M005": "Component version does not use semantic versioning",
    "M006": "Required field missing",
    "M007": "Implementation has no matching Service",
    "M008": "API port differs from Service ports",
    "M009": "API path does not start with the component name",
    "M010": "Duplicate API name",
    "M011": "Specification URL follows a moving branch",
    "M012": "Field has the wrong type",
}
LEVELS = {"error": "error", "warn": "warning", "info": "note"}


def artifact_uri(path):
    """Use workspace-relative URIs, or file URIs for external inputs."""
    absolute = Path(path).resolve()
    try:
        return quote(absolute.relative_to(Path.cwd().resolve()).as_posix(), safe="/")
    except ValueError:
        return absolute.as_uri()


def report(rows, lang="en"):
    results = []
    for path, document, finding in rows:
        results.append({
            "ruleId": finding.rule,
            "level": LEVELS[finding.severity],
            "message": {"text": finding.message(lang)},
            "locations": [{
                "physicalLocation": {"artifactLocation": {"uri": artifact_uri(path)}},
                "logicalLocations": [{"fullyQualifiedName": f"document[{document}].{finding.where}"}],
            }],
            "properties": {"document": document, "where": finding.where},
        })
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "component-manifest-lint",
                "version": __version__,
                "rules": [{"id": rule, "shortDescription": {"text": text}}
                          for rule, text in sorted(DESCRIPTIONS.items())],
            }},
            "results": results,
        }],
    }
