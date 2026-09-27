"""``dpdpkit-policies`` command line: validate packs and print the rule-to-code map."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from . import (
    PolicyValidationError,
    list_overlays,
    list_packs,
    load_overlay,
    load_pack,
    load_rule_map,
    read_policy_file,
    validate_overlay,
    validate_pack,
)


def _validate(paths: Sequence[str]) -> int:
    failures = 0
    if not paths:
        targets: list[tuple[str, str]] = [("pack", p) for p in list_packs()]
        targets += [("overlay", o) for o in list_overlays()]
        for kind, ident in targets:
            try:
                (load_pack if kind == "pack" else load_overlay)(ident)
                print(f"ok      {kind} {ident}")
            except PolicyValidationError as exc:
                failures += 1
                print(f"FAILED  {kind} {ident}")
                for err in exc.errors:
                    print(f"          {err}")
        return 1 if failures else 0

    for path in paths:
        try:
            data = read_policy_file(path)
            if data.get("kind") == "overlay":
                validate_overlay(data, path)
            else:
                validate_pack(data, path)
            print(f"ok      {path}")
        except PolicyValidationError as exc:
            failures += 1
            print(f"FAILED  {path}")
            for err in exc.errors:
                print(f"          {err}")
    return 1 if failures else 0


def _rule_map(fmt: str) -> int:
    rules = load_rule_map()
    if fmt == "json":
        print(json.dumps(rules, indent=2))
        return 0
    pack = load_pack(list_packs()[-1])
    print(f"| Pack key | Value in `{pack['id']}` | Legal source | What it controls | Code |")
    print("| --- | --- | --- | --- | --- |")
    for rule in rules:
        value: object = pack
        for part in rule["key"].split("."):
            value = value[part] if isinstance(value, dict) else None
        shown = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        code = ", ".join(f"`{m}`" for m in rule["used_by"])
        print(f"| `{rule['key']}` | `{shown}` | {rule['source']} | {rule['summary']} | {code} |")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dpdpkit-policies", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    val = sub.add_parser("validate", help="validate shipped packs, or the given files")
    val.add_argument("paths", nargs="*")
    sub.add_parser("list", help="list shipped packs and overlays")
    rmap = sub.add_parser("rule-map", help="print the rule-to-code map")
    rmap.add_argument("--format", choices=["md", "json"], default="md")
    args = parser.parse_args(argv)

    if args.command == "validate":
        return _validate(args.paths)
    if args.command == "list":
        for p in list_packs():
            print(f"pack     {p}")
        for o in list_overlays():
            print(f"overlay  {o}")
        return 0
    return _rule_map(args.format)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
