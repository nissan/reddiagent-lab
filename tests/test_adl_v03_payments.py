#!/usr/bin/env python3
"""Check the ADL v0.3 payment contract: assets, mode, charge intents, fee and receipt v2 (#452)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SCHEMA = json.loads((ROOT / "specs" / "ADL-v0.3.schema.json").read_text())
EXAMPLES = sorted((ROOT / "examples" / "v0.3").glob("*.yaml"))
INVALID = sorted((ROOT / "examples" / "invalid").glob("adl-v0.3-*.yaml"))
LIVE = ROOT / "examples" / "v0.3" / "live-solana-provider-agent.yaml"
# Fail closed at Level 0 by design in v0.2 as well: they declare payment metadata below Level 3.
EXPECTED_CONFORMANCE_FAILURES = {"adapter-loss-export-agent.yaml", "permission-policy-agent.yaml"}
# Valid against the schema; rejected by Level 3 conformance.
CONFORMANCE_ONLY = {
    "adl-v0.3-mainnet-mint-not-allowlisted.yaml": "is not the allowlisted AUDD mint on solana-mainnet-beta",
    "adl-v0.3-wrong-protocol-fee.yaml": "extensions.x402.protocolFee.bps must be 5",
    "adl-v0.3-live-unsupported-rail.yaml": "rail=stripe is an unsupported live payment rail",
    "adl-v0.3-live-charge-missing-protocol-fee.yaml": "extensions.x402.protocolFee is required for a live charge",
}


def schema_errors(doc: dict) -> list[str]:
    return [error.message for error in jsonschema.Draft202012Validator(SCHEMA).iter_errors(doc)]


def report(path: Path) -> tuple[int, dict]:
    result = subprocess.run(
        [PYTHON, "scripts/adl_v03_conformance.py", str(path)], cwd=ROOT, text=True, capture_output=True
    )
    return result.returncode, json.loads(result.stdout)[0]


def missing(rep: dict) -> list[str]:
    return [field for fields in rep["missingFieldsByLevel"].values() for field in fields]


def live_doc() -> dict:
    return yaml.safe_load(LIVE.read_text())


def test_example_sets_are_present() -> None:
    assert len(EXAMPLES) == 17
    assert len(INVALID) == 16


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_every_v03_example_is_schema_valid_and_meets_its_requested_level(path: Path) -> None:
    assert schema_errors(yaml.safe_load(path.read_text())) == []
    code, rep = report(path)
    if path.name in EXPECTED_CONFORMANCE_FAILURES:
        assert (code, rep["status"]) == (1, "fail")
    else:
        assert (code, rep["status"]) == (0, "pass"), missing(rep)


@pytest.mark.parametrize("path", INVALID, ids=lambda p: p.name)
def test_every_v03_negative_fixture_is_rejected(path: Path) -> None:
    code, rep = report(path)
    assert (code, rep["status"]) == (1, "fail")
    if path.name in CONFORMANCE_ONLY:
        assert rep["schemaDiagnostics"] == []
        assert any(CONFORMANCE_ONLY[path.name] in field for field in missing(rep)), missing(rep)
    else:
        assert rep["schemaDiagnostics"] != []


@pytest.mark.parametrize("symbol,mint", [
    ("USDC", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"),
    ("AUDD", "AUDDttiEpCydTm7joUMbYddm72jAWXZnCpPZtDoxqBSw"),
    ("PYUSD", "2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo"),
    ("USDG", "2u1tszSeqZ3qBWF3uNGPFc8TzMk2tdiwknnRMWGWjGWH"),
    ("SOL", None),
])
def test_a_live_charge_in_each_v1_asset_passes_level_3(tmp_path: Path, symbol: str, mint: str | None) -> None:
    """ADL-03-S1 and ADL-03-S3."""
    doc = live_doc()
    asset = {"symbol": symbol, "network": "solana-mainnet-beta", **({"mint": mint} if mint else {})}
    for intent in doc["extensions"]["x402"]["intents"]:
        intent["asset"] = dict(asset)
        if "authority" in intent:
            intent["authority"]["asset"] = dict(asset)
    for policy in doc["harness"]["policies"]:
        if isinstance(policy.get("limits"), dict) and "asset" in policy["limits"]:
            policy["limits"]["asset"] = symbol
    path = tmp_path / "agent.yaml"
    path.write_text(yaml.safe_dump(doc, sort_keys=False))
    code, rep = report(path)
    assert (code, rep["achievedLevel"], rep["status"]) == (0, 3, "pass"), missing(rep)
    assert rep["payment"] == {"mode": "live", "paymentMade": False, "liveRailDeclared": True}


def test_dry_run_mode_reports_no_payment_whatever_the_rail(tmp_path: Path) -> None:
    """ADL-03-S4."""
    doc = live_doc()
    doc["extensions"]["x402"]["mode"] = "dry-run"
    for intent in doc["extensions"]["x402"]["intents"]:
        intent["rail"] = "stripe"
        if "authority" in intent:
            intent["authority"]["rail"] = "stripe"
    path = tmp_path / "agent.yaml"
    path.write_text(yaml.safe_dump(doc, sort_keys=False))
    code, rep = report(path)
    assert (code, rep["status"]) == (0, "pass"), missing(rep)
    assert rep["payment"] == {"mode": "dry-run", "paymentMade": False, "liveRailDeclared": False}
    assert rep["boundary"]["paymentAccess"] is False


def test_a_v02_document_fails_and_points_to_the_migration_note() -> None:
    """ADL-03-S5."""
    code, rep = report(ROOT / "examples" / "v0.2" / "payment-agent.yaml")
    assert (code, rep["achievedLevel"]) == (1, -1)
    assert "docs/ADL-V0.2-TO-V0.3-MIGRATION.md" in rep["schemaDiagnostics"][0]["message"]
    assert (ROOT / "docs" / "ADL-V0.2-TO-V0.3-MIGRATION.md").exists()


def test_a_charge_policy_must_bound_the_price_in_the_same_asset(tmp_path: Path) -> None:
    for change in ({"asset": "USDC"}, {"maxAmount": "9.99"}, {"requireReceipt": False}):
        doc = live_doc()
        intent = doc["extensions"]["x402"]["intents"][0]
        for policy in doc["harness"]["policies"]:
            if policy.get("resource") == f"x402:intent:{intent['id']}":
                policy["limits"].update(change)
        path = tmp_path / "agent.yaml"
        path.write_text(yaml.safe_dump(doc, sort_keys=False))
        code, rep = report(path)
        assert code == 1 and f"harness.policies[payment:x402:intent:{intent['id']}]" in missing(rep), change


def test_schema_has_no_v02_payment_vocabulary_left() -> None:
    text = json.dumps(SCHEMA)
    for gone in ("x402-dry-run", '"GBP"', '"EUR"', '"currency"', '"rails"'):
        assert gone not in text, gone
    spec = (ROOT / "specs" / "ADL-v0.3.md").read_text()
    assert "reddi.receipt.v2" in spec and "`x402-dry-run` is no longer a rail" in spec


def test_asset_schema_rules() -> None:
    doc = live_doc()
    intent = doc["extensions"]["x402"]["intents"][0]
    assert schema_errors(doc) == []
    for bad in (
        {"symbol": "USDC", "network": "solana-devnet"},
        {"symbol": "SOL", "network": "solana-devnet", "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"},
        {"symbol": "USDC", "network": "solana-devnet", "mint": "not-base58-0OIl"},
        {"symbol": "USDC", "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"},
    ):
        changed = copy.deepcopy(doc)
        changed["extensions"]["x402"]["intents"][0]["asset"] = bad
        assert schema_errors(changed) != [], bad
    assert intent["price"]["per"] == "call"
