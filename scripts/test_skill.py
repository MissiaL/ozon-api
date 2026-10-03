#!/usr/bin/env python3
"""Offline checks for enrichment and endpoint lookup; no API calls."""
import copy
import io
import json
from contextlib import redirect_stdout, redirect_stderr
from types import SimpleNamespace

from build_spec import enrich, METHODS
from lookup_endpoint import cmd_show, load_spec, resolve_ref


def main():
    external = "../../components/schemas/rpcStatus.yaml"
    assert resolve_ref({}, external) == {"$ref": external}
    assert resolve_ref({}, "#/missing") == {"$ref": "#/missing"}
    assert resolve_ref({"components": {"schemas": {"A/B~": {"type": "string"}}}}, "#/components/schemas/A~1B~0") == {"type": "string"}
    for api in ("seller", "performance"):
        spec = load_spec(api)
        original = copy.deepcopy(spec)
        sections = enrich(spec)
        assert spec == original, "Enrichment must be idempotent"
        assert sum(map(len, sections.values())) == sum(m in METHODS for item in spec["paths"].values() for m in item)
        for path, item in spec["paths"].items():
            for method in item.keys() & METHODS:
                output = io.StringIO()
                with redirect_stdout(output):
                    assert cmd_show(spec, SimpleNamespace(path=path, method=method)) == 0
                assert method.upper() in json.loads(output.getvalue())["operations"]

    sample = {"tags": [{"name": "Ad", "x-displayName": "Ads"}], "x-tagGroups": [{"name": "Methods", "tags": ["Ad"]}], "paths": {"/campaign": {"parameters": [{"name": "id", "in": "path"}], "patch": {"tags": ["Ad", "Edit"], "responses": {"200": {"$ref": "#/components/responses/OK"}}}}}, "components": {"responses": {"OK": {"description": "ok"}}}}
    original = copy.deepcopy(sample)
    enrich(sample)
    assert sample["paths"]["/campaign"]["patch"]["tags"] == ["Ad", "Edit", "Ads"]
    sample["paths"]["/campaign"]["patch"].pop("x-ozon-section")
    sample["paths"]["/campaign"]["patch"]["tags"].pop()
    assert sample == original, "Enrichment must preserve the official document"
    output = io.StringIO()
    with redirect_stdout(output):
        assert cmd_show(sample, SimpleNamespace(path="/campaign", method="patch")) == 0
    operation = json.loads(output.getvalue())["operations"]["PATCH"]
    assert operation["parameters"] == original["paths"]["/campaign"]["parameters"]
    assert operation["responses"]["200"] == {"description": "ok"}
    with redirect_stderr(io.StringIO()):
        assert cmd_show(sample, SimpleNamespace(path="/campaign", method="get")) == 2
        assert cmd_show(sample, SimpleNamespace(path="/campaign", method="parameters")) == 2
        assert cmd_show(sample, SimpleNamespace(path="/missing", method=None)) == 2
    print("Skill checks passed for both snapshots and lookup failures")


if __name__ == "__main__":
    main()
