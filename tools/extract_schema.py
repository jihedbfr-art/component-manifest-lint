"""Turn the published Component CRD into the small schema tree the linter ships.

Usage: python tools/extract_schema.py CRD.yaml "<source url @ commit>" OUT.json

The CRD is a Helm template; the few {{ ... }} expressions are replaced by a placeholder before parsing.
Output: {"source": ..., "versions": {"v1": tree, ...}} where a tree node is
{"type", "required", "props", "items", "open"}.
"""
import json
import re
import sys

import yaml


def node(schema):
    if not isinstance(schema, dict):
        return {}
    out = {}
    if schema.get("type"):
        out["type"] = schema["type"]
    if schema.get("required"):
        out["required"] = sorted(schema["required"])
    if schema.get("properties"):
        out["props"] = {name: node(sub) for name, sub in sorted(schema["properties"].items())}
    if isinstance(schema.get("items"), dict):
        out["items"] = node(schema["items"])
    if schema.get("x-kubernetes-preserve-unknown-fields") or (
            schema.get("type") == "object" and not schema.get("properties")):
        out["open"] = True  # free-form: children are not checked
    return out


def main(crd_path, source, out_path):
    text = open(crd_path, encoding="utf-8").read()
    doc = yaml.safe_load(re.sub(r"\{\{.*?\}\}", "X", text))
    group = doc["spec"]["group"]
    versions = {}
    for version in doc["spec"]["versions"]:
        tree = node(version["schema"]["openAPIV3Schema"])
        tree["props"].pop("status", None)  # written by the cluster, never by authors
        versions[version["name"]] = tree
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump({"source": source, "group": group, "kind": doc["spec"]["names"]["kind"], "versions": versions},
                  handle, indent=1, sort_keys=True)
        handle.write("\n")


if __name__ == "__main__":
    main(*sys.argv[1:4])
