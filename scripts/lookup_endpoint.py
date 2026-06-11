#!/usr/bin/env python3
"""Extract details for Ozon Seller API endpoints from the bundled OpenAPI spec.

The full spec is several MB — too big to dump into context. This script lets
you pull only what you need: the operation object, its parameters,
request/response schemas (with $ref resolved one level), and deprecation flags.

Usage:
    # Search for endpoints by keyword in path/summary/tag (case-insensitive):
    python3 lookup_endpoint.py search цены
    python3 lookup_endpoint.py search /product/info
    python3 lookup_endpoint.py search --tag FBS

    # Show full details for a specific path (and optionally method):
    python3 lookup_endpoint.py show /v3/product/info/list
    python3 lookup_endpoint.py show /v2/posting/fbs/get --method post

    # List all categories (tags) with endpoint counts:
    python3 lookup_endpoint.py tags
"""
import argparse
import json
import sys
from pathlib import Path

SPEC_PATH = Path(__file__).resolve().parent.parent / "references" / "ozon-seller-openapi.json"


def load_spec() -> dict:
    with SPEC_PATH.open() as f:
        return json.load(f)


def resolve_ref(spec: dict, ref: str) -> dict:
    # "#/components/schemas/Foo" -> spec["components"]["schemas"]["Foo"]
    parts = ref.lstrip("#/").split("/")
    node = spec
    for p in parts:
        node = node.get(p, {})
    return node


def deref_one_level(spec: dict, obj):
    """Resolve top-level $ref once. Nested $refs are left as-is to avoid blowup."""
    if isinstance(obj, dict):
        if "$ref" in obj and len(obj) == 1:
            return resolve_ref(spec, obj["$ref"])
        return {k: deref_one_level(spec, v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deref_one_level(spec, x) for x in obj]
    return obj


def _search_once(spec: dict, needle: str, tag_filter: str):
    hits = []
    for path, methods in spec["paths"].items():
        for method, op in methods.items():
            if method not in ("get", "post", "put", "delete", "patch"):
                continue
            tags = [t.lower() for t in op.get("tags", [])]
            if tag_filter and not any(tag_filter in t for t in tags):
                continue
            summary = op.get("summary", "")
            blob = f"{path} {summary} {' '.join(tags)}".lower()
            if needle and needle not in blob:
                continue
            hits.append((method.upper(), path, summary, op.get("tags", []), bool(op.get("deprecated"))))
    return hits


def cmd_search(spec: dict, args) -> int:
    needle = (args.query or "").lower()
    tag_filter = (args.tag or "").lower()
    hits = _search_once(spec, needle, tag_filter)

    # If no exact match and the needle is long enough, try a shorter stem.
    # This handles Russian inflections: "остатки" → "остатк" matches "остатками".
    used_stem = None
    if not hits and len(needle) >= 5 and not args.exact:
        stem = needle[: max(4, len(needle) - 2)]
        hits = _search_once(spec, stem, tag_filter)
        if hits:
            used_stem = stem

    if not hits:
        print("(no matches) — try a shorter query (Russian word stem) or use --tag")
        return 1
    if used_stem:
        print(f"(no exact match for '{needle}' — showing matches for stem '{used_stem}')\n")
    for method, path, summary, tags, dep in hits[:50]:
        tag_s = ", ".join(tags[:2]) if tags else "-"
        marker = " ⚠️ deprecated" if dep else ""
        print(f"{method:6s} {path}{marker}\n        [{tag_s}] {summary}")
    if len(hits) > 50:
        print(f"\n... {len(hits) - 50} more (refine your query)")
    return 0


def cmd_show(spec: dict, args) -> int:
    path = args.path
    if path not in spec["paths"]:
        # Try fuzzy: pick the only path containing the substring.
        candidates = [p for p in spec["paths"] if path in p]
        if len(candidates) == 1:
            path = candidates[0]
        elif len(candidates) > 1:
            print(f"ambiguous, candidates:\n  " + "\n  ".join(candidates[:20]), file=sys.stderr)
            return 2
        else:
            print(f"path not found: {args.path}", file=sys.stderr)
            return 2
    methods = spec["paths"][path]
    # In OpenAPI 3.0, `parameters` may live at the path-item level (shared by all
    # methods of that path) or at the operation level. We merge them so callers
    # see every parameter that applies to a given operation, dedup'd by (name, in).
    path_level_params = deref_one_level(spec, methods.get("parameters", []))

    def merge_params(op_params):
        op_params = deref_one_level(spec, op_params or [])
        seen = {(p.get("name"), p.get("in")) for p in op_params if isinstance(p, dict)}
        merged = list(op_params)
        for p in path_level_params:
            if isinstance(p, dict) and (p.get("name"), p.get("in")) not in seen:
                merged.append(p)
        return merged

    target_methods = [args.method.lower()] if args.method else [m for m in methods if m in ("get", "post", "put", "delete", "patch")]
    out = {"path": path, "operations": {}}
    for m in target_methods:
        op = methods.get(m)
        if not op:
            continue
        # Resolve top-level refs in requestBody/responses for readability.
        op_resolved = {
            "summary": op.get("summary"),
            "description": op.get("description"),
            "tags": op.get("tags"),
            "operationId": op.get("operationId"),
            "deprecated": op.get("deprecated"),
            "x-ozon-section": op.get("x-ozon-section"),
            "parameters": merge_params(op.get("parameters")),
            "requestBody": deref_one_level(spec, op.get("requestBody")),
            "responses": deref_one_level(spec, op.get("responses", {})),
        }
        out["operations"][m.upper()] = op_resolved
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_tags(spec: dict, args) -> int:
    counts = {}
    for path, methods in spec["paths"].items():
        for method, op in methods.items():
            if method not in ("get", "post", "put", "delete", "patch"):
                continue
            sect = op.get("x-ozon-section") or {}
            label = f"{sect.get('title')} ({sect.get('name')})" if sect.get("name") else "(untagged)"
            counts[label] = counts.get(label, 0) + 1
    for tag, n in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"{n:4d}  {tag}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Look up Ozon Seller API endpoints from the bundled OpenAPI spec.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search", help="search endpoints by keyword in path/summary/tag")
    p_search.add_argument("query", nargs="?", default="")
    p_search.add_argument("--tag", help="filter by tag (substring, case-insensitive)")
    p_search.add_argument("--exact", action="store_true", help="disable Russian-stem fallback")

    p_show = sub.add_parser("show", help="show full details of an endpoint")
    p_show.add_argument("path", help="exact path or unique substring, e.g. /v3/product/info/list")
    p_show.add_argument("--method", help="get/post/put/delete/patch (default: all defined for this path)")

    sub.add_parser("tags", help="list all sections with endpoint counts")

    args = parser.parse_args()
    spec = load_spec()
    if args.cmd == "search":
        return cmd_search(spec, args)
    if args.cmd == "show":
        return cmd_show(spec, args)
    if args.cmd == "tags":
        return cmd_tags(spec, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
