from __future__ import annotations

import copy

import pytest

import dpdpkit_policies as pol
from dpdpkit_policies.cli import main

BASE = "dpdp-rules-2025.v1"
# Keys that are configuration, not legal numbers, and need no rule_map entry.
NON_LEGAL = {
    "id",
    "kind",
    "source",
    "published",
    "overlays",
    "commencement.immediate",
    "notice.default_language",
}


def _leaf_keys(data: dict, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for k, v in data.items():
        path = f"{prefix}{k}"
        if isinstance(v, dict) and k != "third_schedule":
            keys |= _leaf_keys(v, path + ".")
        else:
            keys.add(path)
    return keys


def test_every_shipped_pack_validates() -> None:
    assert BASE in pol.list_packs()
    for pack_id in pol.list_packs():
        data = pol.load_pack(pack_id)
        assert data["id"] == pack_id


def test_base_pack_numbers() -> None:
    pack = pol.load_pack(BASE)
    assert pack["retention"]["erasure_pre_notice_hours"] == 48
    assert pack["retention"]["min_log_retention_days"] == 365
    assert pack["rights"]["grievance_max_days"] == 90
    assert pack["children"]["age_of_majority"] == 18
    assert pack["breach"]["board_detailed_report_hours"] == 72
    assert set(pack["notice"]["required_links"]) == {"withdraw", "rights", "board_complaint"}
    assert pack["commencement"]["fiduciary_duties"] == "2027-05-13"


def test_unknown_pack_is_refused() -> None:
    with pytest.raises(pol.UnknownPolicyError):
        pol.load_pack("dpdp-rules-1999.v1")


def test_typo_in_legal_key_fails_validation() -> None:
    pack = copy.deepcopy(pol.load_pack(BASE))
    pack["retention"]["erasure_prenotice_hours"] = 24
    with pytest.raises(pol.PolicyValidationError) as exc:
        pol.validate_pack(pack)
    assert "erasure_prenotice_hours" in str(exc.value)


def test_wrong_type_fails_validation() -> None:
    pack = copy.deepcopy(pol.load_pack(BASE))
    pack["rights"]["grievance_max_days"] = "ninety"
    with pytest.raises(pol.PolicyValidationError):
        pol.validate_pack(pack)


def test_overlay_merge_and_applies_to() -> None:
    pack = pol.load_pack(BASE)
    overlay = {
        "id": "cert-in-test",
        "kind": "overlay",
        "source": "test",
        "applies_to": ["dpdp-rules-2025"],
        "set": {"breach": {"cert_in_report_hours": 6}, "retention": {"log_retention_in_india_days": 180}},
    }
    pol.validate_overlay(overlay)
    merged = pol.merge_overlays(pack, [overlay])
    assert merged["breach"]["cert_in_report_hours"] == 6
    assert merged["breach"]["board_detailed_report_hours"] == 72
    assert merged["overlays"] == ["cert-in-test"]
    assert "cert_in_report_hours" not in pack["breach"], "base pack must not be mutated"

    other = dict(overlay, applies_to=["some-other-law"])
    with pytest.raises(pol.PolicyValidationError):
        pol.merge_overlays(pack, [other])


def test_overlay_cannot_introduce_unknown_keys() -> None:
    overlay = {
        "id": "bad",
        "kind": "overlay",
        "source": "t",
        "applies_to": ["dpdp"],
        "set": {"breach": {"x": 1}},
    }
    with pytest.raises(pol.PolicyValidationError):
        pol.merge_overlays(pol.load_pack(BASE), [overlay])


def test_rule_map_covers_every_legal_key() -> None:
    pack = pol.load_pack(BASE)
    mapped = {r["key"] for r in pol.load_rule_map()}
    legal = _leaf_keys(pack) - NON_LEGAL
    missing = sorted(k for k in legal if not any(k == m or k.startswith(m + ".") for m in mapped))
    assert not missing, f"pack keys without a rule_map entry: {missing}"
    leaves = _leaf_keys(pack)
    unknown = sorted(m for m in mapped if m not in leaves)
    assert not unknown, f"rule_map keys not in pack: {unknown}"


def test_cli_validate_and_rule_map(capsys: pytest.CaptureFixture[str], tmp_path) -> None:  # type: ignore[no-untyped-def]
    assert main(["validate"]) == 0
    assert main(["rule-map"]) == 0
    out = capsys.readouterr().out
    assert "retention.erasure_pre_notice_hours" in out

    bad = tmp_path / "bad.yaml"
    bad.write_text("id: x.v1\nkind: pack\n", encoding="utf-8")
    assert main(["validate", str(bad)]) == 1
