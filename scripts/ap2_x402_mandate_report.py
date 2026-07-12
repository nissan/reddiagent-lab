#!/usr/bin/env python3
"""Static AP2 mandate and x402 payment-extension mapping report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_FLAGS = {
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "paymentAccess": False,
    "mcpInvocation": False,
}
AP2_MANDATES = ["IntentMandate", "CartMandate", "PaymentMandate"]
MANDATE_FIELDS = ["id", "vcRef", "issuer", "subject", "scope", "expiresAt", "auditRef"]
LIVE_ACCESS_FLAGS = {
    "runtimeExecutionAllowed",
    "networkAccess",
    "paymentAccess",
    "mcpInvocation",
}
UNSAFE_FIELD_NAMES = {
    "serverUrl",
    "url",
    "endpoint",
    "command",
    "env",
    "walletPrivateKey",
    "privateKey",
    "rawSignature",
    "credential",
    "credentials",
    "apiKey",
    "secret",
}
LIVE_ENDPOINT_SCHEMES = ("http://", "https://")


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict:
    resolved = path if path.is_absolute() else ROOT / path
    return json.loads(resolved.read_text())


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


def finding(category: str, path: str, reason: str, status: str = "fail") -> dict:
    return {"category": category, "path": path, "status": status, "reason": reason}


def mandate(doc: dict, name: str) -> dict:
    value = doc.get("ap2", {}).get("mandates", {}).get(name)
    return value if isinstance(value, dict) else {}


def required_field_findings(doc: dict) -> list[dict]:
    findings: list[dict] = []
    x402 = doc.get("x402", {})
    extension = doc.get("reddiPaymentExtension", {})
    for object_name in ["PaymentRequired", "PaymentSignature", "PaymentResponse"]:
        if not isinstance(x402.get(object_name), dict):
            findings.append(
                finding("missing", f"x402.{object_name}", "Required x402 object is missing.")
            )
    accepts = x402.get("PaymentRequired", {}).get("accepts")
    if not isinstance(accepts, list) or not accepts:
        findings.append(
            finding(
                "missing",
                "x402.PaymentRequired.accepts",
                "PaymentRequired must include accepted x402 payment options.",
            )
        )
    for object_name in AP2_MANDATES:
        value = mandate(doc, object_name)
        if not value:
            findings.append(
                finding("missing", f"ap2.mandates.{object_name}", "Required AP2 mandate is missing.")
            )
            continue
        for field in MANDATE_FIELDS:
            if value.get(field) in (None, "", [], {}):
                findings.append(
                    finding(
                        "missing",
                        f"ap2.mandates.{object_name}.{field}",
                        "AP2 mandate required field is missing.",
                    )
                )
    for path, value in [
        ("reddiPaymentExtension.intentId", extension.get("intentId")),
        ("reddiPaymentExtension.budget.maxAmount", extension.get("budget", {}).get("maxAmount")),
        ("reddiPaymentExtension.receipt.required", extension.get("receipt", {}).get("required")),
        (
            "reddiPaymentExtension.receipt.serviceResultStatus",
            extension.get("receipt", {}).get("serviceResultStatus"),
        ),
        (
            "reddiPaymentExtension.receipt.requiredEvalGateStatus",
            extension.get("receipt", {}).get("requiredEvalGateStatus"),
        ),
    ]:
        if value in (None, "", [], {}):
            findings.append(
                finding("missing", path, "Reddi payment extension mapping field is missing.")
            )
    return findings


def unsafe_findings(doc: dict) -> list[dict]:
    findings: list[dict] = []
    for path, value in walk(doc):
        key = path.split(".")[-1].split("[")[0]
        if key in LIVE_ACCESS_FLAGS and value is not False:
            findings.append(
                finding(
                    "unsafe",
                    path,
                    "AP2/x402 mapping input must not claim runtime, network, payment, or MCP access.",
                )
            )
        if key in UNSAFE_FIELD_NAMES and value not in (None, "", [], {}):
            findings.append(
                finding(
                    "unsafe",
                    path,
                    "AP2/x402 mapping input contains a live endpoint, executable, credential, or wallet field.",
                )
            )
            continue
        if isinstance(value, str) and value.startswith(LIVE_ENDPOINT_SCHEMES):
            findings.append(
                finding(
                    "unsafe",
                    path,
                    "AP2/x402 mapping input contains a live URL; use static refs only.",
                )
            )
    for object_name in AP2_MANDATES:
        scope = mandate(doc, object_name).get("scope")
        if scope in ("*", "any", "unrestricted"):
            findings.append(
                finding(
                    "unsafe",
                    f"ap2.mandates.{object_name}.scope",
                    "AP2 mandate scope must be constrained.",
                )
            )
    budget = doc.get("reddiPaymentExtension", {}).get("budget", {})
    if budget.get("maxAmount") in (None, "", "unbounded", "unlimited"):
        findings.append(
            finding(
                "unsafe",
                "reddiPaymentExtension.budget.maxAmount",
                "Payment budget must define a bounded max amount.",
            )
        )
    return findings


def unsupported_findings(doc: dict) -> list[dict]:
    findings: list[dict] = []
    x402 = doc.get("x402", {})
    extension = doc.get("reddiPaymentExtension", {})
    payment = mandate(doc, "PaymentMandate")
    response = x402.get("PaymentResponse", {})
    receipt = extension.get("receipt", {})
    if payment.get("settlementRail") not in {option.get("rail") for option in x402.get("PaymentRequired", {}).get("accepts", [])}:
        findings.append(
            finding(
                "unsupported",
                "ap2.mandates.PaymentMandate.settlementRail",
                "PaymentMandate settlement rail must match an accepted x402 rail.",
            )
        )
    if payment.get("asset") != extension.get("budget", {}).get("asset"):
        findings.append(
            finding(
                "unsupported",
                "ap2.mandates.PaymentMandate.asset",
                "PaymentMandate asset must match the Reddi payment budget asset.",
            )
        )
    if response.get("success") is True and receipt.get("serviceResultStatus") != "pass":
        findings.append(
            finding(
                "unsupported",
                "reddiPaymentExtension.receipt.serviceResultStatus",
                "Payment success alone cannot satisfy Reddi/RAP receipt semantics.",
            )
        )
    if receipt.get("requiredEvalGateStatus") != "pass":
        findings.append(
            finding(
                "unsupported",
                "reddiPaymentExtension.receipt.requiredEvalGateStatus",
                "Required eval gates must pass before reputation or RAP handoff is ready.",
            )
        )
    return findings


def mandate_mapping(doc: dict, findings: list[dict]) -> list[dict]:
    if findings:
        return []
    extension = doc["reddiPaymentExtension"]
    return [
        {
            "from": "reddiPaymentExtension.intentId",
            "to": "ap2.mandates.IntentMandate.id",
            "status": "ap2-ready",
            "value": extension["intentId"],
        },
        {
            "from": "reddiPaymentExtension.cartRef",
            "to": "ap2.mandates.CartMandate.cartRef",
            "status": "ap2-ready",
            "value": extension.get("cartRef"),
        },
        {
            "from": "reddiPaymentExtension.budget",
            "to": "ap2.mandates.PaymentMandate",
            "status": "ap2-ready",
            "value": {
                "maxAmount": extension["budget"]["maxAmount"],
                "asset": extension["budget"]["asset"],
                "rails": extension["budget"]["rails"],
            },
        },
        {
            "from": "x402.PaymentRequired.accepts",
            "to": "ap2.mandates.PaymentMandate.settlementRail",
            "status": "metadata-only",
            "value": doc["x402"]["PaymentRequired"]["accepts"],
        },
        {
            "from": "reddiPaymentExtension.receipt",
            "to": "rap.facilitatorProfile.receiptPolicy",
            "status": "rap-ready",
            "value": extension["receipt"],
        },
    ]


def metadata_only(doc: dict) -> list[dict]:
    entries = []
    for section, reason in [
        ("ap2.mandates.IntentMandate", "Verifiable Credential reference is preserved; no VC verification is performed."),
        ("ap2.mandates.CartMandate", "Cart authorization evidence is preserved as static metadata."),
        ("ap2.mandates.PaymentMandate", "Payment authorization is reviewed, not executed."),
        ("x402.PaymentRequired", "Accepted payment options are preserved; no quote is fetched."),
        ("x402.PaymentSignature", "Payment proof reference is preserved; no signing is performed."),
        ("x402.PaymentResponse", "Payment response reference is preserved; no settlement is verified."),
        ("rap.facilitatorProfile", "RAP facilitator profile is static documentation only."),
    ]:
        entries.append({"section": section, "reason": reason})
    return entries


def report(path: Path) -> dict:
    doc = read_json(path)
    findings = required_field_findings(doc) + unsafe_findings(doc) + unsupported_findings(doc)
    status = "fail" if findings else "pass"
    return {
        "source": display_path(path),
        "mode": "static-ap2-x402-mandate-report",
        "status": status,
        "ap2Ready": status == "pass",
        "rapFacilitatorProfile": "metadata-only" if status == "pass" else "blocked",
        "mandateMapping": mandate_mapping(doc, findings),
        "metadataOnly": metadata_only(doc),
        "unsupported": [item for item in findings if item["category"] == "unsupported"],
        "unsafe": [item for item in findings if item["category"] == "unsafe"],
        "findings": findings,
        "preservedVocabulary": {
            "ap2": AP2_MANDATES,
            "x402": ["PaymentRequired", "PaymentSignature", "PaymentResponse"],
            "reddi": ["intentId", "budget", "receipt", "reputation"],
            "rap": ["facilitatorProfile", "receiptPolicy", "authorityConstraints"],
        },
        **BOUNDARY_FLAGS,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()

    result = report(args.fixture)
    print(json.dumps(result, indent=2))
    return 2 if result["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
