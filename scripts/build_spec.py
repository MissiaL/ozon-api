#!/usr/bin/env python3
"""Enrich a downloaded official Ozon OpenAPI snapshot and rebuild its index."""
import argparse
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

REFS_DIR = Path(__file__).resolve().parent.parent / "references"
METHODS = {"get", "post", "put", "delete", "patch", "head", "options", "trace"}


def enrich(spec):
    groups = {tag: group["name"] for group in spec.get("x-tagGroups", []) for tag in group["tags"]}
    tags = {tag["name"]: tag for tag in spec.get("tags", [])}
    sections = defaultdict(list)
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if method not in METHODS:
                continue
            name = next((tag for tag in op.get("tags", []) if tag in tags and tag in groups), None)
            if name is None:
                raise ValueError(f"No documented section for {method.upper()} {path}")
            title = tags[name].get("x-displayName") or name
            op["x-ozon-section"] = {"name": name, "title": title, "group": groups[name]}
            if title not in op["tags"]:
                op["tags"].append(title)
            sections[(name, title, groups[name])].append((path, method, op))
    return sections


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True, choices=["seller", "performance"])
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--checked-at", required=True, type=date.fromisoformat)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    spec = json.loads(raw)
    if not str(spec.get("openapi", "")).startswith("3.") or not isinstance(spec.get("paths"), dict) or not spec["paths"]:
        parser.error("input must be an OpenAPI 3 JSON document with nonempty paths")
    sections = enrich(spec)
    source = f"https://docs.ozon.ru/api/{args.api}/swagger.json"
    spec["x-source"] = {"url": source, "checked_at": args.checked_at.isoformat(), "sha256": hashlib.sha256(raw).hexdigest()}
    name = f"ozon-{args.api}-openapi.json"
    data = json.dumps(spec, ensure_ascii=False, indent=2) + "\n"
    operations = sum(len(items) for items in sections.values())
    title = "Ozon Seller API" if args.api == "seller" else "Ozon Performance API (реклама)"
    lines = [f"# {title} — индекс категорий", "", f"Источник: [официальный OpenAPI]({source}), проверен {args.checked_at}. Полный спек: [{name}](./{name}) ({len(spec['paths'])} путей / {operations} операций).", "", "**Не читай OpenAPI целиком.** Используй `scripts/lookup_endpoint.py` (`tags`/`search`/`show`).", "", "Категории отсортированы по числу эндпоинтов.", ""]
    for (tag, label, group), items in sorted(sections.items(), key=lambda entry: (-len(entry[1]), entry[0][1])):
        lines.extend([f"## {label} (`{tag}`, {len(items)}) — группа «{group}»", ""])
        for path, method, op in sorted(items, key=lambda item: (item[0], item[1])):
            deprecated = " ⚠️ deprecated" if op.get("deprecated") else ""
            lines.append(f"- `{method.upper():6s} {path}`{deprecated} — {op.get('summary', '')}")
        lines.append("")
    (REFS_DIR / name).write_text(data, encoding="utf-8")
    index = "index.md" if args.api == "seller" else "index-performance.md"
    (REFS_DIR / index).write_text("\n".join(lines), encoding="utf-8")
    print(f"{args.api}: {operations} operations, {len(sections)} sections")


if __name__ == "__main__":
    main()
