"""Versioned DPDP policy packs and sector overlays for dpdpkit.

This package holds data only: YAML packs, overlays, and the JSON Schema that validates them.
dpdpkit-core reads a pack through :func:`load_pack` and refuses to start if it does not validate.
"""

from __future__ import annotations

import copy
import datetime as _dt
import json
from collections.abc import Iterable, Mapping
from importlib import resources
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

__version__ = "2026.10.0"

__all__ = [
    "PolicyValidationError",
    "UnknownPolicyError",
    "list_overlays",
    "list_packs",
    "load_overlay",
    "load_pack",
    "load_rule_map",
    "merge_overlays",
    "read_policy_file",
    "schema",
    "validate_overlay",
    "validate_pack",
]

_ROOT = resources.files(__name__)


class UnknownPolicyError(LookupError):
    """Raised when a pack or overlay id is not shipped in this package."""


class PolicyValidationError(ValueError):
    """Raised when a pack or overlay does not match its JSON Schema."""

    def __init__(self, source: str, errors: list[str]) -> None:
        self.source = source
        self.errors = errors
        super().__init__(f"{source}: " + "; ".join(errors))


def _normalise(value: Any) -> Any:
    """YAML parses ISO dates into ``date`` objects; the schema expects strings."""
    if isinstance(value, dict):
        return {str(k): _normalise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalise(v) for v in value]
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    return value


def read_policy_file(path: str | Path) -> dict[str, Any]:
    """Read a pack or overlay YAML/JSON file from disk without validating it."""
    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text) if str(path).endswith(".json") else yaml.safe_load(text)
    if not isinstance(data, dict):
        raise PolicyValidationError(str(path), ["top level must be a mapping"])
    return _normalise(data)  # type: ignore[no-any-return]


def schema(kind: str = "pack") -> dict[str, Any]:
    """Return the JSON Schema for ``pack`` or ``overlay`` documents."""
    if kind not in ("pack", "overlay"):
        raise ValueError("kind must be 'pack' or 'overlay'")
    return json.loads((_ROOT / "schema" / f"{kind}.schema.json").read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _errors(data: Mapping[str, Any], kind: str) -> list[str]:
    validator = Draft202012Validator(schema(kind), format_checker=FormatChecker())
    out = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        where = ".".join(str(p) for p in err.absolute_path) or "<root>"
        out.append(f"{where}: {err.message}")
    return out


def validate_pack(data: Mapping[str, Any], source: str = "<pack>") -> None:
    errors = _errors(data, "pack")
    if errors:
        raise PolicyValidationError(source, errors)


def validate_overlay(data: Mapping[str, Any], source: str = "<overlay>") -> None:
    errors = _errors(data, "overlay")
    if errors:
        raise PolicyValidationError(source, errors)


def _ids(folder: str) -> list[str]:
    return sorted(
        p.name.removesuffix(".yaml") for p in (_ROOT / folder).iterdir() if p.name.endswith(".yaml")
    )


def list_packs() -> list[str]:
    """Ids of every pack shipped in this release, oldest first."""
    return _ids("packs")


def list_overlays() -> list[str]:
    return _ids("overlays")


def _load(folder: str, ident: str) -> dict[str, Any]:
    ref = _ROOT / folder / f"{ident}.yaml"
    if not ref.is_file():
        available = ", ".join(_ids(folder)) or "none"
        raise UnknownPolicyError(f"unknown {folder[:-1]} {ident!r}; available: {available}")
    data = yaml.safe_load(ref.read_text(encoding="utf-8"))
    return _normalise(data)  # type: ignore[no-any-return]


def load_overlay(overlay_id: str) -> dict[str, Any]:
    data = _load("overlays", overlay_id)
    validate_overlay(data, overlay_id)
    return data


def _deep_merge(base: dict[str, Any], patch: Mapping[str, Any]) -> dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def merge_overlays(pack: Mapping[str, Any], overlays: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Deep-merge overlays into a copy of ``pack`` and validate the result."""
    merged = copy.deepcopy(dict(pack))
    applied: list[str] = list(merged.get("overlays", []))
    for overlay in overlays:
        prefixes = overlay["applies_to"]
        if not any(str(merged["id"]).startswith(p) for p in prefixes):
            raise PolicyValidationError(
                overlay["id"], [f"does not apply to pack {merged['id']} (applies to {prefixes})"]
            )
        _deep_merge(merged, overlay["set"])
        applied.append(overlay["id"])
    merged["overlays"] = applied
    validate_pack(merged, f"{merged['id']} + {', '.join(applied) or 'no overlays'}")
    return merged


def load_pack(pack_id: str, overlays: Iterable[str] = ()) -> dict[str, Any]:
    """Load a shipped pack by id, apply overlays by id, and validate.

    Raises :class:`UnknownPolicyError` or :class:`PolicyValidationError`; never returns defaults.
    """
    data = _load("packs", pack_id)
    validate_pack(data, pack_id)
    overlay_ids = list(overlays)
    if not overlay_ids:
        return data
    return merge_overlays(data, [load_overlay(o) for o in overlay_ids])


def load_rule_map() -> list[dict[str, Any]]:
    """Entries mapping each pack key to its legal source and the dpdpkit code that uses it."""
    data = yaml.safe_load((_ROOT / "rule_map.yaml").read_text(encoding="utf-8"))
    return list(data["rules"])
