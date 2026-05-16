"""Compare FastAPI OpenAPI to the Node baseline (documentation/api_antiga.json).

Uses structural rules suited to FastAPI vs a hand-maintained Node spec:
- Every Node /api/v1 path+method exists in Python.
- For each operation, Node request/response schemas must be satisfied by the
  Python schemas (Python may document extra fields, stricter limits, or extra
  query parameters).
- Strips documented 401/403/404 AppError envelopes and FastAPI 422 vs Node 400
  validation blocks before comparing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import jsonref

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = REPO_ROOT / "documentation" / "api_antiga.json"

COSMETIC_KEYS = frozenset(
    {
        "summary",
        "example",
        "examples",
        "title",
        "operationId",
        "tags",
        "externalDocs",
        "deprecated",
    }
)


def strip_cosmetic(obj: Any) -> Any:
    """Remove documentation-only keys. Do not drop ``description`` dict keys that
    are JSON field names (e.g. game ``description`` property).
    """
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if k in COSMETIC_KEYS:
                continue
            if k == "description" and isinstance(v, str):
                continue
            out[k] = strip_cosmetic(v)
        return out
    if isinstance(obj, list):
        return [strip_cosmetic(x) for x in obj]
    return obj


def path_param_names(path: str) -> list[str]:
    return re.findall(r"\{([^}]+)\}", path)


def canonical_path_key(path: str) -> str:
    raw = path.rstrip("/") or "/"
    parts = raw.split("/")
    out: list[str] = []
    i = 0
    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            out.append(f"{{p{i}}}")
            i += 1
        else:
            out.append(part)
    return "/".join(out)


def rename_path_parameters(operation: dict[str, Any], path: str) -> None:
    names = path_param_names(path)
    mapping = {n: f"p{i}" for i, n in enumerate(names)}
    for param in operation.get("parameters") or []:
        if param.get("in") != "path":
            continue
        old = param.get("name")
        if isinstance(old, str) and old in mapping:
            param["name"] = mapping[old]


def simplify_anyof_null(obj: Any) -> Any:
    if isinstance(obj, list):
        return [simplify_anyof_null(x) for x in obj]
    if not isinstance(obj, dict):
        return obj
    if "anyOf" in obj and isinstance(obj["anyOf"], list):
        aos = obj["anyOf"]
        if len(aos) == 2 and all(isinstance(x, dict) for x in aos):
            t0, t1 = aos[0].get("type"), aos[1].get("type")
            if t0 == "null":
                merged = {k: v for k, v in obj.items() if k != "anyOf"}
                inner = simplify_anyof_null(aos[1])
                if isinstance(inner, dict):
                    merged.update(inner)
                return merged
            if t1 == "null":
                merged = {k: v for k, v in obj.items() if k != "anyOf"}
                inner = simplify_anyof_null(aos[0])
                if isinstance(inner, dict):
                    merged.update(inner)
                return merged
    return {k: simplify_anyof_null(v) for k, v in obj.items()}


def sort_parameters(operation: dict[str, Any]) -> None:
    params = operation.get("parameters")
    if not isinstance(params, list):
        return
    operation["parameters"] = sorted(
        params,
        key=lambda p: (p.get("in") or "", p.get("name") or ""),
    )


def strip_fastapi_validation_response(operation: dict[str, Any]) -> None:
    responses = operation.get("responses")
    if isinstance(responses, dict) and "422" in responses:
        del responses["422"]


def strip_baseline_zod_validation_response(operation: dict[str, Any]) -> None:
    responses = operation.get("responses")
    if not isinstance(responses, dict):
        return
    r400 = responses.get("400")
    if not isinstance(r400, dict):
        return
    desc = (r400.get("description") or "").lower()
    if "validation" in desc or "zod" in desc:
        del responses["400"]


def _is_app_error_response(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    content = entry.get("content")
    if not isinstance(content, dict):
        return False
    app_json = content.get("application/json")
    if not isinstance(app_json, dict):
        return False
    schema = app_json.get("schema")
    if not isinstance(schema, dict):
        return False
    props = schema.get("properties")
    if not isinstance(props, dict):
        return False
    success = props.get("success")
    if not isinstance(success, dict):
        return False
    return success.get("enum") == [False]


def strip_app_error_statuses(responses: dict[str, Any]) -> None:
    for code in list(responses):
        if code in ("401", "403", "404") and _is_app_error_response(
            responses.get(code)
        ):
            del responses[code]


def normalize_204_response(responses: dict[str, Any]) -> None:
    r204 = responses.get("204")
    if not isinstance(r204, dict):
        return
    content = r204.get("content")
    if content in (None, {}):
        responses["204"] = {}
        return
    if isinstance(content, dict):
        aj = content.get("application/json")
        if isinstance(aj, dict) and aj.get("schema") in ({}, None):
            responses["204"] = {}


def dereference(spec: dict[str, Any]) -> dict[str, Any]:
    replaced = jsonref.replace_refs(
        spec,
        lazy_load=False,
        proxies=False,
    )
    return json.loads(json.dumps(replaced))


def iter_api_v1_operations(
    paths: dict[str, Any],
) -> dict[tuple[str, str], tuple[str, str, dict[str, Any]]]:
    merged: dict[tuple[str, str], tuple[str, str, dict[str, Any]]] = {}
    for raw_path, path_item in paths.items():
        if not raw_path.startswith("/api/v1"):
            continue
        if not isinstance(path_item, dict):
            continue
        ck = canonical_path_key(raw_path)
        for method, operation in path_item.items():
            if method not in (
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "head",
                "options",
            ):
                continue
            if not isinstance(operation, dict):
                continue
            key = (ck, method.lower())
            if key in merged:
                _, _, existing = merged[key]
                if json.dumps(operation, sort_keys=True) != json.dumps(
                    existing, sort_keys=True
                ):
                    msg = f"Ambiguous paths merge to {key[0]} {key[1]}: {raw_path}"
                    raise SystemExit(msg)
            merged[key] = (raw_path, method.lower(), operation)
    return merged


def _number_bounds_ok(
    bsch: dict[str, Any],
    psch: dict[str, Any],
    *,
    direction: str,
) -> bool:
    if direction == "request":
        if "minimum" in bsch:
            if psch.get("minimum") is None:
                return bsch.get("minimum") == psch.get("minimum")
            if psch["minimum"] > bsch["minimum"]:
                return False
        if "maximum" in bsch:
            if psch.get("maximum") is None:
                return bsch.get("maximum") == psch.get("maximum")
            if psch["maximum"] < bsch["maximum"]:
                return False
    else:
        if "minimum" in bsch and psch.get("minimum") is not None:
            if psch["minimum"] > bsch["minimum"]:
                return False
        if "maximum" in bsch and psch.get("maximum") is not None:
            if psch["maximum"] < bsch["maximum"]:
                return False
    return True


def _normalize_baseline_type_array(schema: dict[str, Any]) -> dict[str, Any]:
    t = schema.get("type")
    if not isinstance(t, list):
        return schema
    ts = set(t)
    if ts == {"null", "string"}:
        return {**schema, "type": "string"}
    if ts == {"null", "integer"}:
        return {**schema, "type": "integer"}
    if ts == {"null", "number"}:
        return {**schema, "type": "number"}
    if ts == {"null", "boolean"}:
        return {**schema, "type": "boolean"}
    return schema


def baseline_schema_covered_by_python(
    baseline: Any,
    python: Any,
    *,
    direction: str,
    path: str,
) -> list[str]:
    """Return human-readable errors; empty means OK."""
    errs: list[str] = []

    if isinstance(baseline, dict):
        baseline = _normalize_baseline_type_array(dict(baseline))

    if baseline == python:
        return errs

    if isinstance(baseline, dict) and isinstance(python, dict):
        bt, pt = baseline.get("type"), python.get("type")
        if bt == "object" and pt == "object":
            b_props = baseline.get("properties") or {}
            p_props = python.get("properties") or {}
            b_req = list(baseline.get("required") or [])
            p_req = set(python.get("required") or [])

            for rk in b_req:
                if rk not in p_props:
                    errs.append(
                        f"{path}: baseline requires property {rk!r} missing in python"
                    )
                    continue
                psub = p_props[rk]
                if rk not in p_req and "default" not in (
                    psub if isinstance(psub, dict) else {}
                ):
                    errs.append(
                        f"{path}: baseline requires {rk!r} but python does not "
                        "mark it required and has no default",
                    )

            for name, bsch in b_props.items():
                if name not in p_props:
                    errs.append(f"{path}: baseline property {name!r} missing in python")
                    continue
                psch = p_props[name]
                errs.extend(
                    baseline_schema_covered_by_python(
                        bsch,
                        psch,
                        direction=direction,
                        path=f"{path}.{name}",
                    ),
                )
            return errs

        if bt in ("string", "integer", "number", "boolean") and bt == pt:
            if (
                bt == "boolean"
                and baseline.get("enum") == [False]
                and python.get("const") is False
            ):
                return errs
            if (
                bt == "boolean"
                and baseline.get("enum") == [False]
                and python.get("default") is False
                and python.get("type") == "boolean"
            ):
                return errs
                if "enum" not in python or not isinstance(python["enum"], list):
                    errs.append(f"{path}: python lacks enum baseline has")
                else:
                    bset, pset = set(baseline["enum"]), set(python["enum"])
                    if not bset.issubset(pset):
                        errs.append(f"{path}: python enum must contain baseline enum")
            if bt == "string":
                if "minLength" in baseline:
                    if (
                        python.get("minLength") is not None
                        and python["minLength"] > baseline["minLength"]
                    ):
                        errs.append(f"{path}: python minLength stricter than baseline")
                if "maxLength" in baseline:
                    if (
                        python.get("maxLength") is not None
                        and python["maxLength"] < baseline["maxLength"]
                    ):
                        errs.append(f"{path}: python maxLength stricter than baseline")
            if bt in ("integer", "number") and not _number_bounds_ok(
                baseline, python, direction=direction
            ):
                errs.append(f"{path}: incompatible numeric bounds")
            if baseline.get("format") and python.get("format"):
                if baseline["format"] != python["format"]:
                    errs.append(
                        f"{path}: format {baseline['format']!r} vs {python['format']!r}"
                    )
            return errs

        if bt == "array" and pt == "array":
            bi = baseline.get("items")
            pi = python.get("items")
            if bi is None or pi is None:
                return [f"{path}: array items missing"]
            errs.extend(
                baseline_schema_covered_by_python(
                    bi,
                    pi,
                    direction=direction,
                    path=f"{path}[]",
                ),
            )
            return errs

    errs.append(f"{path}: incompatible types or shapes {baseline!r} vs {python!r}")
    return errs


def _normalize_operation(raw_path: str, operation: dict[str, Any]) -> dict[str, Any]:
    op = deepcopy(operation)
    strip_fastapi_validation_response(op)
    strip_baseline_zod_validation_response(op)
    rename_path_parameters(op, raw_path)
    sort_parameters(op)
    op = simplify_anyof_null(op)
    responses = op.get("responses")
    if isinstance(responses, dict):
        strip_app_error_statuses(responses)
        normalize_204_response(responses)
    op = strip_cosmetic(op)
    return op


def _check_media_schema_pair(
    b_content: dict[str, Any] | None,
    p_content: dict[str, Any] | None,
    *,
    direction: str,
    label: str,
) -> list[str]:
    if not b_content:
        return []
    if not p_content:
        return [f"{label}: missing content in python"]
    b_app = b_content.get("application/json")
    p_app = p_content.get("application/json")
    if not isinstance(b_app, dict) or "schema" not in b_app:
        return []
    if not isinstance(p_app, dict) or "schema" not in p_app:
        return [f"{label}: python missing application/json schema"]
    return baseline_schema_covered_by_python(
        b_app["schema"],
        p_app["schema"],
        direction=direction,
        path=label,
    )


def _param_key(p: dict[str, Any]) -> tuple[str | None, str | None]:
    inn = p.get("in")
    name = p.get("name")
    if inn == "header" and isinstance(name, str):
        return inn, name.lower()
    return inn, name if isinstance(name, str) else None


def _empty_204_content(content: object) -> bool:
    if content in (None, {}):
        return True
    if not isinstance(content, dict):
        return False
    aj = content.get("application/json")
    if not isinstance(aj, dict):
        return False
    return aj.get("schema") in (None, {})


def compare_operations(
    raw_b: str,
    raw_p: str,
    op_b: dict[str, Any],
    op_p: dict[str, Any],
) -> list[str]:
    prep_b = _normalize_operation(raw_b, op_b)
    prep_p = _normalize_operation(raw_p, op_p)

    errs: list[str] = []

    b_sec = prep_b.get("security")
    p_sec = prep_p.get("security")
    if b_sec != p_sec:
        errs.append(f"security mismatch: {b_sec!r} vs {p_sec!r}")

    b_params = prep_b.get("parameters") or []
    p_params = prep_p.get("parameters") or []
    p_param_index = {_param_key(p): p for p in p_params if isinstance(p, dict)}
    for bp in b_params:
        if not isinstance(bp, dict):
            continue
        key = _param_key(bp)
        pp = p_param_index.get(key)
        if pp is None:
            errs.append(f"parameter missing in python: {key}")
            continue
        bsch = (bp.get("schema") or {}) if isinstance(bp.get("schema"), dict) else {}
        psch = (pp.get("schema") or {}) if isinstance(pp.get("schema"), dict) else {}
        errs.extend(
            baseline_schema_covered_by_python(
                bsch,
                psch,
                direction="request",
                path=f"param:{key}",
            ),
        )

    b_body = prep_b.get("requestBody")
    p_body = prep_p.get("requestBody")
    if isinstance(b_body, dict) and b_body.get("required"):
        b_cont = (
            (b_body.get("content") or {})
            if isinstance(b_body.get("content"), dict)
            else {}
        )
        p_cont = (p_body.get("content") or {}) if isinstance(p_body, dict) else {}
        errs.extend(
            _check_media_schema_pair(
                b_cont,
                p_cont,
                direction="request",
                label="requestBody",
            ),
        )

    b_resp = prep_b.get("responses") or {}
    p_resp = prep_p.get("responses") or {}
    if not isinstance(b_resp, dict) or not isinstance(p_resp, dict):
        return errs
    for status, b_entry in b_resp.items():
        if status not in p_resp:
            errs.append(f"response status {status} in baseline but missing in python")
            continue
        p_entry = p_resp[status]
        if not isinstance(b_entry, dict) or not isinstance(p_entry, dict):
            continue
        if status == "204":
            if _empty_204_content(b_entry.get("content")) and _empty_204_content(
                p_entry.get("content"),
            ):
                continue
        b_cont = b_entry.get("content")
        p_cont = p_entry.get("content")
        if isinstance(b_cont, dict):
            errs.extend(
                _check_media_schema_pair(
                    b_cont,
                    p_cont if isinstance(p_cont, dict) else None,
                    direction="response",
                    label=f"responses.{status}",
                ),
            )
    return errs


def load_python_openapi() -> dict[str, Any]:
    sys.path.insert(0, str(REPO_ROOT))
    from src.main import create_app  # noqa: PLC0415

    return create_app().openapi()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Node OpenAPI JSON (default: documentation/api_antiga.json)",
    )
    args = parser.parse_args()

    baseline_path = args.baseline
    if not baseline_path.is_file():
        print(f"Baseline not found: {baseline_path}", file=sys.stderr)
        return 2

    baseline_raw = json.loads(baseline_path.read_text(encoding="utf-8"))
    python_raw = load_python_openapi()

    baseline = dereference(baseline_raw)
    python = dereference(python_raw)

    b_ops = iter_api_v1_operations(baseline.get("paths") or {})
    p_ops = iter_api_v1_operations(python.get("paths") or {})

    missing = [f"{m.upper()} {ck}" for ck, m in sorted(b_ops) if (ck, m) not in p_ops]
    extra = [f"{m.upper()} {ck}" for ck, m in sorted(p_ops) if (ck, m) not in b_ops]

    failed = False
    for line in missing:
        print(f"MISSING {line}", file=sys.stderr)
        failed = True

    for key in sorted(b_ops):
        if key not in p_ops:
            continue
        raw_b, _, op_b = b_ops[key]
        raw_p, _, op_p = p_ops[key]
        op_errs = compare_operations(raw_b, raw_p, op_b, op_p)
        if op_errs:
            failed = True
            ck, m = key
            print(f"MISMATCH {m.upper()} {ck}", file=sys.stderr)
            for e in op_errs:
                print(f"  {e}", file=sys.stderr)

    if extra:
        print("Python-only /api/v1 routes (not in Node baseline):", file=sys.stderr)
        for line in extra:
            print(f"  {line}", file=sys.stderr)

    if not failed and not missing:
        print(
            f"OpenAPI parity OK: {len(b_ops)} /api/v1 operations covered "
            f"(subset rules; {len(extra)} python-only routes).",
        )
    return 1 if failed or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
