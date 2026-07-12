#!/usr/bin/env python3
"""Emit a deterministic dry-run receipt report for a payment-capable ReddiAgent."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_FLAGS = {
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "paymentAccess": False,
    "mcpInvocation": False,
}
LIVE_ACCESS_FLAGS = {
    "runtimeExecutionAllowed",
    "networkAccess",
    "paymentAccess",
    "mcpInvocation",
}
UNSAFE_FIELD_NAMES = {
    "facilitatorUrl",
    "serverUrl",
    "url",
    "endpoint",
    "walletPrivateKey",
    "privateKey",
    "rawSignature",
    "settlementReference",
    "settlementRef",
    "paymentReference",
    "paymentRef",
    "credential",
    "credentials",
    "apiKey",
    "secret",
}
LIVE_ENDPOINT_SCHEMES = ("http://", "https://")


def digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_yaml(path: Path) -> dict:
    resolved = path if path.is_absolute() else ROOT / path
    return yaml.safe_load(resolved.read_text())


def walk(obj: object, prefix: str = "") -> list[tuple[str, object]]:
    items: list[tuple[str, object]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            items.append((path, value))
            items.extend(walk(value, path))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            path = f"{prefix}[{index}]"
            items.append((path, value))
            items.extend(walk(value, path))
    return items


def finding(category: str, path: str, reason: str) -> dict:
    return {"category": category, "path": path, "status": "fail", "reason": reason}


def unsafe_findings(doc: dict) -> list[dict]:
    findings: list[dict] = []
    for path, value in walk(doc):
        key = path.split(".")[-1].split("[")[0]
        if key in LIVE_ACCESS_FLAGS and value is not False:
            findings.append(
                finding(
                    "unsafe",
                    path,
                    "Dry-run receipt input must not claim runtime, network, payment, or MCP access.",
                )
            )
        if key in UNSAFE_FIELD_NAMES and value not in (None, "", [], {}):
            findings.append(
                finding(
                    "unsafe",
                    path,
                    "Dry-run receipt input contains a live endpoint, credential, wallet, or signature field.",
                )
            )
            continue
        if isinstance(value, str) and value.startswith(LIVE_ENDPOINT_SCHEMES):
            findings.append(
                finding(
                    "unsafe",
                    path,
                    "Dry-run receipt input contains a live URL; use static refs only.",
                )
            )
    return findings


def unsupported_findings(doc: dict) -> list[dict]:
    findings: list[dict] = []
    extensions = doc.get("extensions", {})
    x402 = extensions.get("x402", {})
    receipts = extensions.get("receipts", {})
    intents = x402.get("intents") or []
    if not x402.get("enabled"):
        findings.append(finding("unsupported", "extensions.x402.enabled", "x402 must be enabled."))
    if not intents:
        findings.append(
            finding("unsupported", "extensions.x402.intents", "At least one payment intent is required.")
        )
        return findings
    intent = intents[0]
    if intent.get("direction") not in {"spend", "charge", "both"}:
        findings.append(
            finding(
                "unsupported",
                "extensions.x402.intents[0].direction",
                "Payment direction must be spend, charge, or both.",
            )
        )
    if not intent.get("rails"):
        findings.append(
            finding("unsupported", "extensions.x402.intents[0].rails", "Payment intent must list rail candidates.")
        )
    if intent.get("maxAmount") in (None, "", "unbounded", "unlimited"):
        findings.append(
            finding(
                "unsupported",
                "extensions.x402.intents[0].maxAmount",
                "Payment receipt requires a bounded max amount.",
            )
        )
    if intent.get("requireReceipt") is not True or receipts.get("required") is not True:
        findings.append(
            finding(
                "unsupported",
                "extensions.receipts.required",
                "Dry-run payment receipts must be required before completion.",
            )
        )
    return findings


def receipt(doc: dict) -> dict:
    x402 = doc["extensions"]["x402"]
    intent = x402["intents"][0]
    agent = doc["metadata"]["name"]
    task_id = "dry-run-example-task"
    return {
        "receiptVersion": "reddiagent.receipt/v0.2",
        "agent": agent,
        "taskId": task_id,
        "paymentIntentId": intent["id"],
        "paymentDirection": intent["direction"],
        "railCandidates": intent["rails"],
        "amount": intent["maxAmount"],
        "currency": intent["currency"],
        "requestHash": digest(agent + ":" + task_id + ":request"),
        "responseHash": digest(agent + ":" + task_id + ":response"),
        "paymentRef": "dry-run:none",
        "settlementReference": None,
        "serviceResultStatus": "pass",
        "requiredEvalGateStatus": "pass",
        "emissionPolicy": "emit-after-payment-and-service-pass",
        "policyResults": [{"id": "task-budget", "status": "pass"}],
        "evalResults": [{"id": "receipt-required", "status": "pass"}],
        "reputationSignalsAllowed": doc.get("extensions", {}).get("reputation", {}).get("emitSignals", []),
    }


def metadata_only(doc: dict) -> list[dict]:
    entries = [
        {
            "section": "extensions.x402",
            "reason": "Payment intent and x402 vocabulary are preserved; no quote, proof, facilitator, wallet, or settlement path is used.",
        },
        {
            "section": "extensions.receipts",
            "reason": "Receipt evidence is deterministic dry-run data only.",
        },
    ]
    if doc.get("extensions", {}).get("reputation"):
        entries.append(
            {
                "section": "extensions.reputation",
                "reason": "Reputation signals are allowed only after receipt and eval evidence; no reputation service is called.",
            }
        )
    if doc.get("harness", {}).get("runtime", {}).get("target") != "local-python":
        entries.append(
            {
                "section": "harness.runtime",
                "reason": "Non-local runtime targets are preserved as metadata; no runtime is activated.",
            }
        )
    return entries


def report(path: Path) -> dict:
    doc = read_yaml(path)
    findings = unsafe_findings(doc) + unsupported_findings(doc)
    status = "fail" if findings else "pass"
    return {
        "source": display_path(path),
        "mode": "static-payment-dry-run-receipt-report",
        "status": status,
        "receiptReady": status == "pass",
        "receipt": receipt(doc) if status == "pass" else None,
        "metadataOnly": metadata_only(doc),
        "unsupported": [item for item in findings if item["category"] == "unsupported"],
        "unsafe": [item for item in findings if item["category"] == "unsafe"],
        "findings": findings,
        "preservedVocabulary": {
            "x402": ["PaymentRequired", "PaymentSignature", "PaymentResponse"],
            "reddi": ["intentId", "budget", "receipt", "reputation"],
            "rap": ["payment-plus-service-result", "required-eval-gate", "authority-constraints"],
        },
        **BOUNDARY_FLAGS,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("adl", nargs="?", type=Path, default=ROOT / "examples" / "payment-agent.yaml")
    args = parser.parse_args()

    result = report(args.adl)
    print(json.dumps(result, indent=2))
    return 2 if result["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
