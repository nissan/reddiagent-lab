#!/usr/bin/env python3
"""Static x402/MCP-to-RAP bridge report checker."""

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
X402_OBJECTS = ["PaymentRequired", "PaymentSignature", "PaymentResponse"]
LIVE_FIELD_NAMES = {
    "serverUrl",
    "url",
    "endpoint",
    "facilitatorUrl",
    "command",
    "env",
    "wallet",
    "walletAddress",
    "walletPrivateKey",
    "privateKey",
    "rawSignature",
    "credential",
    "credentials",
    "apiKey",
    "secret",
    "settlementEndpoint",
    "settlementUrl",
    "settlementCommand",
}
LIVE_ACCESS_FLAGS = {
    "runtimeExecutionAllowed",
    "networkAccess",
    "paymentAccess",
    "mcpInvocation",
}
LIVE_ENDPOINT_SCHEMES = ("http://", "https://")
CONFORMANCE_CHECKS = [
    "x402-payment-evidence",
    "authority-mandate-bounded",
    "receipt-payment-plus-service-result",
    "reputation-after-receipt",
    "unsafe-live-field-scan",
]
RECEIPT_REPUTATION_CHECKS = [
    "x402-receipt-payment-ref-bound",
    "ap2-authority-ref-bound",
    "service-result-pass-required",
    "required-eval-gate-pass-required",
    "reputation-signals-after-receipt",
]
REQUIRED_REPUTATION_SIGNALS = {
    "receipt_verified",
    "service_result_pass",
    "required_eval_gate_pass",
}


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


def required_field_findings(doc: dict) -> list[dict]:
    findings: list[dict] = []
    required_paths = [
        ("service.mcp.serverRef", doc.get("service", {}).get("mcp", {}).get("serverRef")),
        ("service.mcp.toolName", doc.get("service", {}).get("mcp", {}).get("toolName")),
        ("x402.direction", doc.get("x402", {}).get("direction")),
        ("authority.mandateId", doc.get("authority", {}).get("mandateId")),
        ("authority.scope", doc.get("authority", {}).get("scope")),
        ("authority.maxAmount", doc.get("authority", {}).get("maxAmount")),
        ("authority.expiresAt", doc.get("authority", {}).get("expiresAt")),
        ("authority.revocationRef", doc.get("authority", {}).get("revocationRef")),
        ("authority.auditRef", doc.get("authority", {}).get("auditRef")),
        ("receipts.requestHash", doc.get("receipts", {}).get("requestHash")),
        ("receipts.responseHash", doc.get("receipts", {}).get("responseHash")),
        ("receipts.paymentRef", doc.get("receipts", {}).get("paymentRef")),
        ("receipts.serviceResultStatus", doc.get("receipts", {}).get("serviceResultStatus")),
        (
            "receipts.requiredEvalGateStatus",
            doc.get("receipts", {}).get("requiredEvalGateStatus"),
        ),
        ("conformance.level", doc.get("conformance", {}).get("level")),
    ]
    for path, value in required_paths:
        if value in (None, "", [], {}):
            findings.append(finding("missing", path, "RAP bridge required field is missing."))

    x402 = doc.get("x402", {})
    for object_name in X402_OBJECTS:
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
                "PaymentRequired must include accepted payment options.",
            )
        )
    checks = doc.get("conformance", {}).get("checks")
    if not isinstance(checks, list):
        findings.append(
            finding("missing", "conformance.checks", "RAP dry-run conformance checks are missing.")
        )
    else:
        missing_checks = [check for check in CONFORMANCE_CHECKS if check not in checks]
        for check in missing_checks:
            findings.append(
                finding(
                    "missing",
                    "conformance.checks",
                    f"RAP dry-run conformance check is missing: {check}.",
                )
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
                    "Bridge input must not claim runtime, network, payment, or MCP access.",
                )
            )
        if key in LIVE_FIELD_NAMES and value not in (None, "", [], {}):
            findings.append(
                finding(
                    "unsafe",
                    path,
                    "Bridge input contains a live endpoint, executable, credential, or wallet field.",
                )
            )
            continue
        if (
            isinstance(value, str)
            and value.startswith(LIVE_ENDPOINT_SCHEMES)
            and (path.startswith("service.mcp.") or path.startswith("x402."))
        ):
            findings.append(
                finding(
                    "unsafe",
                    path,
                    "Bridge input contains a live endpoint URL in MCP or x402 metadata.",
                )
            )

    authority = doc.get("authority", {})
    if authority.get("scope") in ("*", "unrestricted", "any"):
        findings.append(
            finding("unsafe", "authority.scope", "Authority scope must be constrained.")
        )
    if authority.get("maxAmount") in (None, "", "unbounded", "unlimited"):
        findings.append(
            finding("unsafe", "authority.maxAmount", "Authority must define a bounded max amount.")
        )
    conformance = doc.get("conformance", {})
    if conformance.get("reportOnly") is not True:
        findings.append(
            finding(
                "unsafe",
                "conformance.reportOnly",
                "RAP bridge conformance must remain report-only.",
            )
        )
    if conformance.get("liveBridgeAllowed") is not False:
        findings.append(
            finding(
                "unsafe",
                "conformance.liveBridgeAllowed",
                "RAP bridge conformance must not allow a live bridge.",
            )
        )
    return findings


def unsupported_findings(doc: dict) -> list[dict]:
    findings: list[dict] = []
    x402 = doc.get("x402", {})
    signature = x402.get("PaymentSignature", {})
    response = x402.get("PaymentResponse", {})
    receipts = doc.get("receipts", {})
    authority = doc.get("authority", {})
    reputation = doc.get("reputation", {})

    if response.get("success") is True and receipts.get("serviceResultStatus") != "pass":
        findings.append(
            finding(
                "unsupported",
                "receipts.serviceResultStatus",
                "Payment success alone cannot prove task success for RAP receipt handoff.",
            )
        )
    if receipts.get("requiredEvalGateStatus") != "pass":
        findings.append(
            finding(
                "unsupported",
                "receipts.requiredEvalGateStatus",
                "Required eval gate must pass before reputation signals are RAP-ready.",
            )
        )
    if receipts.get("emissionPolicy") == "emit-after-payment-only":
        findings.append(
            finding(
                "unsupported",
                "receipts.emissionPolicy",
                "RAP receipts must bind payment evidence to service result and eval evidence.",
            )
        )

    response_ref = response.get("transactionRef") or response.get("transactionHash")
    if response_ref and receipts.get("paymentRef") and receipts.get("paymentRef") != response_ref:
        findings.append(
            finding(
                "unsupported",
                "receipts.paymentRef",
                "Receipt payment reference must match the static x402 payment response reference.",
            )
        )
    if signature.get("authorizationRef") and authority.get("mandateId"):
        if signature["authorizationRef"] != authority["mandateId"]:
            findings.append(
                finding(
                    "unsupported",
                    "x402.PaymentSignature.authorizationRef",
                    "Payment authorization reference must match the AP2-like authority mandate.",
                )
            )
    selected_rail = signature.get("selectedRail")
    accepted_rails = {
        option.get("rail")
        for option in x402.get("PaymentRequired", {}).get("accepts", [])
        if isinstance(option, dict)
    }
    authority_rails = set(authority.get("rails") or [])
    if selected_rail and (selected_rail not in accepted_rails or selected_rail not in authority_rails):
        findings.append(
            finding(
                "unsupported",
                "x402.PaymentSignature.selectedRail",
                "Selected payment rail must be accepted and authorized by the mandate.",
            )
        )
    missing_signals = sorted(REQUIRED_REPUTATION_SIGNALS - set(reputation.get("signals") or []))
    for signal in missing_signals:
        findings.append(
            finding(
                "unsupported",
                "reputation.signals",
                f"Reputation signal requires prior receipt evidence: {signal}.",
            )
        )
    return findings


def metadata_only(doc: dict) -> list[dict]:
    entries = []
    x402 = doc.get("x402", {})
    for object_name in X402_OBJECTS:
        if object_name in x402:
            entries.append(
                {
                    "section": f"x402.{object_name}",
                    "reason": "Preserved as payment evidence vocabulary; no settlement is executed.",
                }
            )
    for section, reason in [
        ("x402.facilitator", "Facilitator is policy metadata only."),
        ("authority", "AP2-like mandate constraints are reviewed, not enforced by runtime."),
        ("receipts", "Receipt evidence is static handoff data."),
        ("reputation", "Reputation signals require future RAP verification."),
        ("conformance", "Dry-run bridge conformance is static evidence only."),
    ]:
        if doc.get(section.split(".")[0]):
            entries.append({"section": section, "reason": reason})
    return entries


def rap_ready(doc: dict, findings: list[dict]) -> list[str]:
    if findings:
        return []
    accepts = doc["x402"]["PaymentRequired"]["accepts"]
    rails = sorted({option.get("rail") for option in accepts if option.get("rail")})
    assets = sorted({option.get("asset") for option in accepts if option.get("asset")})
    signals = doc.get("reputation", {}).get("signals", [])
    return [
        f"paymentDirection:{doc['x402']['direction']}",
        f"rails:{','.join(rails)}",
        f"assets:{','.join(assets)}",
        "x402Vocabulary:PaymentRequired,PaymentSignature,PaymentResponse",
        "authority:bounded-mandate",
        "receipts:payment-plus-service-result",
        f"reputationSignals:{len(signals)}",
        "staticBoundary:runtimeExecutionAllowed=false",
    ]


def dry_run_bridge_conformance(doc: dict, findings: list[dict]) -> dict:
    declared = doc.get("conformance", {}).get("checks", [])
    if not isinstance(declared, list):
        declared = []
    failed_paths = {item["path"] for item in findings}
    status = "fail" if findings else "pass"
    return {
        "level": doc.get("conformance", {}).get("level"),
        "status": status,
        "reportOnly": doc.get("conformance", {}).get("reportOnly") is True,
        "liveBridgeAllowed": doc.get("conformance", {}).get("liveBridgeAllowed") is True,
        "requiredChecks": CONFORMANCE_CHECKS,
        "declaredChecks": declared,
        "passedChecks": CONFORMANCE_CHECKS if status == "pass" else [],
        "failedChecks": [] if status == "pass" else sorted(failed_paths),
        "evidenceRefs": doc.get("conformance", {}).get("evidenceRefs", []),
        **BOUNDARY_FLAGS,
    }


def receipt_reputation_conformance(doc: dict, findings: list[dict]) -> dict:
    x402 = doc.get("x402", {})
    payment_required = x402.get("PaymentRequired", {})
    payment_signature = x402.get("PaymentSignature", {})
    payment_response = x402.get("PaymentResponse", {})
    authority = doc.get("authority", {})
    receipts = doc.get("receipts", {})
    reputation = doc.get("reputation", {})
    status = "fail" if findings else "pass"
    accepted_options = payment_required.get("accepts", [])
    if not isinstance(accepted_options, list):
        accepted_options = []
    reputation_signals = reputation.get("signals", [])
    if not isinstance(reputation_signals, list):
        reputation_signals = []
    return {
        "status": status,
        "requiredChecks": RECEIPT_REPUTATION_CHECKS,
        "passedChecks": RECEIPT_REPUTATION_CHECKS if status == "pass" else [],
        "failedChecks": [] if status == "pass" else sorted({item["path"] for item in findings}),
        "x402ReceiptEvidence": {
            "direction": x402.get("direction"),
            "requiredObject": "PaymentRequired",
            "signatureObject": "PaymentSignature",
            "responseObject": "PaymentResponse",
            "acceptedRailCount": len(accepted_options),
            "selectedRail": payment_signature.get("selectedRail"),
            "paymentRef": receipts.get("paymentRef"),
            "responseRef": payment_response.get("transactionRef")
            or payment_response.get("transactionHash"),
        },
        "authorityEvidence": {
            "mandateId": authority.get("mandateId"),
            "authorizationRef": payment_signature.get("authorizationRef"),
            "scope": authority.get("scope"),
            "maxAmount": authority.get("maxAmount"),
            "expiresAt": authority.get("expiresAt"),
            "revocationRef": authority.get("revocationRef"),
            "auditRef": authority.get("auditRef"),
        },
        "serviceResultEvidence": {
            "requestHash": receipts.get("requestHash"),
            "responseHash": receipts.get("responseHash"),
            "serviceResultStatus": receipts.get("serviceResultStatus"),
            "requiredEvalGateStatus": receipts.get("requiredEvalGateStatus"),
            "emissionPolicy": receipts.get("emissionPolicy"),
        },
        "reputationEvidence": {
            "signals": reputation_signals,
            "requiredSignals": sorted(REQUIRED_REPUTATION_SIGNALS),
            "disputeRef": reputation.get("disputeRef"),
        },
        **BOUNDARY_FLAGS,
    }


def report(path: Path) -> dict:
    doc = read_json(path)
    missing = required_field_findings(doc)
    unsafe = unsafe_findings(doc)
    unsupported = unsupported_findings(doc)
    findings = missing + unsafe + unsupported
    status = "fail" if findings else "pass"
    return {
        "source": display_path(path),
        "mode": "static-x402-mcp-rap-bridge-report",
        "status": status,
        "bridgeReady": status == "pass",
        "rapReady": rap_ready(doc, findings),
        "dryRunBridgeConformance": dry_run_bridge_conformance(doc, findings),
        "receiptReputationConformance": receipt_reputation_conformance(doc, findings),
        "metadataOnly": metadata_only(doc),
        "unsupported": [item for item in findings if item["category"] == "unsupported"],
        "unsafe": [item for item in findings if item["category"] == "unsafe"],
        "findings": findings,
        "preservedVocabulary": {
            "x402": X402_OBJECTS,
            "authority": ["mandateId", "scope", "maxAmount", "expiresAt", "revocationRef", "auditRef"],
            "receipts": ["requestHash", "responseHash", "paymentRef", "serviceResultStatus"],
            "reputation": doc.get("reputation", {}).get("signals", []),
            "conformance": CONFORMANCE_CHECKS,
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
