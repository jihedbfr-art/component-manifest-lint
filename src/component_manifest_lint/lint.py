"""Checks on Component manifests (YAML). Needs PyYAML; everything else is the standard library."""
import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml



_SafeLoader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


class _PlainLoader(_SafeLoader):
    """SafeLoader that keeps dates as text: the published schema types publicationDate as a string."""


def _no_duplicate_keys(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            continue  # '<<' merges are allowed and may be overridden on purpose
        key = loader.construct_object(key_node, deep=True)
        if isinstance(key, (str, int, float, bool)) and key in seen:
            raise yaml.constructor.ConstructorError(None, None, f"duplicate key '{key}'", key_node.start_mark)
        try:
            seen.add(key)
        except TypeError as error:
            raise yaml.constructor.ConstructorError(
                None, None, "mapping key must be hashable", key_node.start_mark) from error
    return _SafeLoader.construct_mapping(loader, node, deep)


_PlainLoader.add_constructor("tag:yaml.org,2002:map", _no_duplicate_keys)
_PlainLoader.yaml_implicit_resolvers = {
    key: [(tag, rx) for tag, rx in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in _SafeLoader.yaml_implicit_resolvers.items()
}

SCHEMA = json.loads((Path(__file__).with_name("schema.json")).read_text(encoding="utf-8"))
FUNCTIONS = ("coreFunction", "managementFunction", "securityFunction")
PINNED_AWAY = re.compile(
    r"^https?://(raw\.githubusercontent\.com/[^/]+/[^/]+|github\.com/[^/]+/[^/]+/(?:blob|raw))/(master|main|HEAD)/")
SEMVER = re.compile(r"^\d+\.\d+\.\d+([-+][0-9A-Za-z.-]+)?$")
ERROR, WARN, INFO = "error", "warn", "info"

MESSAGES = {
    "M001": ("field '{field}' is not in the published schema for {version}; the cluster will most likely drop it",
             "le champ '{field}' n'est pas dans le schéma publié pour {version} ; le cluster l'ignorera très probablement"),
    "M002": ("apiVersion '{value}' is not one of the versions of the published schema ({known})",
             "apiVersion '{value}' ne fait pas partie des versions du schéma publié ({known})"),
    "M003": ("label oda.tmforum.org/componentName should equal metadata.name",
             "le label oda.tmforum.org/componentName devrait être égal à metadata.name"),
    "M004": ("componentMetadata lacks {missing}", "componentMetadata n'a pas {missing}"),
    "M005": ("componentMetadata.version '{value}' is not MAJOR.MINOR.PATCH",
             "componentMetadata.version '{value}' n'est pas au format MAJEUR.MINEUR.CORRECTIF"),
    "M006": ("required field '{field}' is missing", "le champ obligatoire '{field}' est absent"),
    "M007": ("implementation '{value}' matches no Service in this file",
             "l'implémentation '{value}' ne correspond à aucun Service de ce fichier"),
    "M008": ("port {port} differs from the port of Service '{value}' ({service_ports})",
             "le port {port} diffère de celui du Service '{value}' ({service_ports})"),
    "M009": ("path '{value}' does not start with /{name}", "le chemin '{value}' ne commence pas par /{name}"),
    "M010": ("API name '{value}' appears twice in {function}", "le nom d'API '{value}' apparaît deux fois dans {function}"),
    "M011": ("specification URL follows a moving branch ({value}); pin a commit or tag",
             "l'URL de spécification suit une branche mouvante ({value}) ; figez un commit ou une étiquette"),
    "M012": ("field '{field}' should be {expected}, found {found}",
             "le champ '{field}' devrait être de type {expected}, trouvé {found}"),
}


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    where: str
    params: tuple = ()

    def message(self, lang="en"):
        text = dict(self.params).get("message", self.rule)
        en, fr = MESSAGES.get(self.rule, (text, text))
        return (fr if lang == "fr" else en).format(**dict(self.params))


def _f(rule, severity, where, **params):
    return Finding(rule, severity, where, tuple(params.items()))


_TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int, "number": (int, float)}


def _type_name(value):
    return type(value).__name__ if value is not None else "null"


def _walk(value, schema, path, version, out):
    """Compare a value against the schema tree: wrong types, unknown fields, missing required fields."""
    expected = schema.get("type")
    if value is None:
        return  # the cluster prunes nulls, so a null counts as absent (required fields report it)
    if expected and expected in _TYPES:
        ok = isinstance(value, _TYPES[expected]) and not (expected in ("integer", "number") and isinstance(value, bool))
        if not ok:
            out.append(_f("M012", ERROR, path, field=path, expected=expected, found=_type_name(value)))
            return
    if not isinstance(value, (dict, list)):
        return
    if isinstance(value, dict):
        props = schema.get("props")
        if props is None:
            return
        for key in value:
            if not path and key in ("apiVersion", "kind", "metadata", "status"):  # envelope and cluster-written state
                continue
            if key not in props:
                if schema.get("open"):
                    continue  # free-form node: extra fields are kept by the cluster
                out.append(_f("M001", WARN, f"{path}.{key}" if path else key, field=f"{path}.{key}" if path else key, version=version))
            else:
                _walk(value[key], props[key], f"{path}.{key}" if path else key, version, out)
        for key in schema.get("required", []):
            if value.get(key) is None:
                out.append(_f("M006", ERROR, path or "(root)", field=f"{path}.{key}" if path else key))
    elif isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            _walk(item, schema["items"], f"{path}[{index}]", version, out)


def _services(docs):
    """{name: [(namespace, ports, type)]}; malformed Services are skipped, they are not what is being checked."""
    found = {}
    for doc in docs:
        if not (isinstance(doc, dict) and doc.get("kind") == "Service"):
            continue
        meta = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
        spec = doc.get("spec") if isinstance(doc.get("spec"), dict) else {}
        raw = spec.get("ports") if isinstance(spec.get("ports"), list) else []
        ports = [p.get("port") for p in raw if isinstance(p, dict) and isinstance(p.get("port"), int)]
        if isinstance(meta.get("name"), str):
            found.setdefault(meta["name"], []).append((meta.get("namespace"), ports, spec.get("type")))
    return found


def _match(services, name, namespace):
    """Services called `name` that could be in the component's namespace (an unset namespace matches any)."""
    return [s for s in services.get(name, []) if s[0] is None or namespace is None or s[0] == namespace]


def check_component(doc, services):
    out = []
    api_version = doc.get("apiVersion", "")
    group, _, version = str(api_version).partition("/")
    known = SCHEMA["versions"]
    if group != SCHEMA["group"] or version not in known:
        out.append(_f("M002", WARN, "apiVersion", value=api_version, known=", ".join(f"{SCHEMA['group']}/{v}" for v in sorted(known))))
    else:
        _walk(doc, known[version], "", version, out)
    meta = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
    name = meta.get("name")
    label = (meta.get("labels") or {}).get("oda.tmforum.org/componentName") if isinstance(meta.get("labels"), dict) else None
    if name and label != name:
        out.append(_f("M003", INFO, "metadata.labels"))
    spec = doc.get("spec") if isinstance(doc.get("spec"), dict) else {}
    cm = spec.get("componentMetadata") if isinstance(spec.get("componentMetadata"), dict) else {}
    missing = [k for k in ("id", "name", "version", "description") if not cm.get(k)]
    if missing:
        out.append(_f("M004", INFO, "spec.componentMetadata", missing=", ".join(missing)))
    if cm.get("version") and not SEMVER.match(str(cm["version"])):
        out.append(_f("M005", WARN, "spec.componentMetadata.version", value=cm["version"]))
    for function in FUNCTIONS:
        block = spec.get(function) if isinstance(spec.get(function), dict) else {}
        names = []
        for kind in ("exposedAPIs", "dependentAPIs"):
            apis = block.get(kind) if isinstance(block.get(kind), list) else []
            for index, api in enumerate(apis):
                if not isinstance(api, dict):
                    continue
                where = f"spec.{function}.{kind}[{index}]"
                api_name = api.get("name")
                if isinstance(api_name, str) and api_name in names:
                    out.append(_f("M010", WARN, where, value=api_name, function=function))
                if isinstance(api_name, str):
                    names.append(api_name)
                specs = api.get("specification") if isinstance(api.get("specification"), list) else []
                for spec_item in specs:
                    url = spec_item.get("url") if isinstance(spec_item, dict) else None
                    hit = PINNED_AWAY.match(url) if isinstance(url, str) else None
                    if hit:
                        out.append(_f("M011", INFO, where, value=hit.group(2)))
                if kind != "exposedAPIs":
                    continue
                impl = api.get("implementation")
                if isinstance(impl, str) and impl and services:
                    candidates = _match(services, impl, meta.get("namespace"))
                    if not candidates:
                        out.append(_f("M007", WARN, where, value=impl))
                    elif isinstance(api.get("port"), int) and not isinstance(api["port"], bool):
                        usable = [c for c in candidates if c[2] != "ExternalName"]
                        ports = sorted({p for c in usable for p in c[1]})
                        if usable and api["port"] not in ports:
                            out.append(_f("M008", WARN, where, port=api["port"], value=impl,
                                          service_ports=", ".join(map(str, ports)) or "none"))
                path = api.get("path")
                if isinstance(path, str) and name and not path.startswith(f"/{name}"):
                    out.append(_f("M009", INFO, where, value=path, name=name))
    return out


def lint_text(text):
    """Return [(document_index, Finding)] for every Component in a multi-document YAML text."""
    if "{{" in text:
        raise ValueError("this looks like a Helm template ('{{'): render it first, for example with 'helm template'")
    try:
        docs = list(yaml.load_all(text, Loader=_PlainLoader))  # keep empty documents so numbering matches the file
    except yaml.YAMLError as error:
        raise ValueError(f"invalid YAML: {error}") from error
    services = _services(docs)
    results, count = [], 0
    for index, doc in enumerate(docs):
        if isinstance(doc, dict) and doc.get("kind") == SCHEMA["kind"]:
            count += 1
            results.extend((index, finding) for finding in check_component(doc, services))
    return results, count
