#!/usr/bin/env python3
"""Execute deterministic local RAP bridge dry-run scenarios."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "tests" / "fixtures" / "rap-bridge-local-dry-run-scenarios.json"

BOUNDARY_FLAGS = {
    "localOnly": True,
    "liveRapBridgeCall": False,
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "mcpInvocation": False,
    "providerApiAccess": False,
    "credentialAccess": False,
    "walletAccess": False,
    "facilitatorAccess": False,
    "paymentRailAccess": False,
    "settlementAccess": False,
    "devnetAccess": False,
    "mainnetAccess": False,
    "externalSpend": False,
}
APPROVED_RAILS = {"dry-run-usdc", "dry-run-x402"}
REQUIRED_BOUND_REFERENCES = {
    "trace": "traceId",
    "receipt": "receiptId",
    "paymentHandoff": "handoffId",
    "operatorTranscript": "transcriptId",
    "rollback": "rollbackId",
    "source": "sourceCheckId",
    "budget": "budgetId",
}
REQUIRED_TRACE_EVENTS = {
    "rap_bridge.intent.accepted",
    "rap_bridge.quote.prepared",
    "rap_bridge.payment_handoff.prepared",
    "rap_bridge.receipt.emitted",
    "rap_bridge.reputation.prepared",
    "rap_bridge.rollback.proven",
}
FORBIDDEN_REQUEST_FLAGS = {
    "liveRapBridgeCall": "live-rap-bridge-denied",
    "liveMcpRequest": "live-mcp-denied",
    "providerApiRequest": "provider-api-denied",
    "credentialRequest": "credential-access-denied",
    "walletRequest": "wallet-access-denied",
    "facilitatorRequest": "facilitator-access-denied",
    "settlementRequest": "settlement-denied",
    "devnetRequest": "devnet-denied",
    "mainnetRequest": "mainnet-denied",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError("RAP bridge dry-run fixture root must be a JSON object.")
    return doc


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def artifact_id(prefix: str, run_id: str, salt: str) -> str:
    return f"{prefix}:{stable_hash(f'{run_id}:{salt}')[:16]}"


def finding(path: str, reason: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    run_id = scenario.get("runId")
    require(isinstance(run_id, str) and run_id, "runId", "Run id is required.")

    refs = scenario.get("boundReferences")
    require(isinstance(refs, dict), "boundReferences", "Bound reference map is required.")
    if isinstance(refs, dict):
        for ref_name in REQUIRED_BOUND_REFERENCES:
            require(
                refs.get(ref_name) == run_id,
                f"boundReferences.{ref_name}",
                "Trace, receipt, payment handoff, operator, rollback, source, and budget references must bind to the same run id.",
            )

    for flag, reason in FORBIDDEN_REQUEST_FLAGS.items():
        require(scenario.get(flag) in (None, False), flag, reason)

    quote = scenario.get("quote", {})
    require(isinstance(quote, dict), "quote", "Quote metadata is required.")
    if isinstance(quote, dict):
        require(quote.get("rail") in APPROVED_RAILS, "quote.rail", "Payment rail must be an approved dry-run rail.")
        require(quote.get("amount") not in (None, "", "unbounded", "unlimited"), "quote.amount", "Quote must include a bounded amount.")
        require(quote.get("currency") in {"USDC", "USDG"}, "quote.currency", "Quote currency must be reviewable.")

    receipt = scenario.get("receipt", {})
    require(isinstance(receipt, dict), "receipt", "Receipt evidence is required.")
    if isinstance(receipt, dict):
        require(receipt.get("runId") == run_id, "receipt.runId", "Receipt must bind to run id.")
        require(receipt.get("traceId") == run_id, "receipt.traceId", "Receipt must bind to trace id.")
        require(receipt.get("paymentHandoffId") == run_id, "receipt.paymentHandoffId", "Receipt must bind to payment handoff id.")
        require(receipt.get("serviceResultStatus") == "pass", "receipt.serviceResultStatus", "Receipt requires service result pass.")
        require(receipt.get("requiredEvalGateStatus") == "pass", "receipt.requiredEvalGateStatus", "Receipt requires eval gate pass.")

    runtime_trace = scenario.get("runtimeTrace", {})
    require(isinstance(runtime_trace, dict), "runtimeTrace", "Runtime trace evidence is required.")
    if isinstance(runtime_trace, dict):
        require(runtime_trace.get("runId") == run_id, "runtimeTrace.runId", "Runtime trace must bind to run id.")
        events = runtime_trace.get("events")
        require(isinstance(events, list), "runtimeTrace.events", "Runtime trace events are required.")
        if isinstance(events, list):
            event_names = {event.get("event") for event in events if isinstance(event, dict)}
            missing = sorted(REQUIRED_TRACE_EVENTS - event_names)
            require(not missing, "runtimeTrace.events", f"Missing trace events: {', '.join(missing)}")

    transcript = scenario.get("operatorTranscript", {})
    require(isinstance(transcript, dict), "operatorTranscript", "Operator transcript is required.")
    if isinstance(transcript, dict):
        require(transcript.get("runId") == run_id, "operatorTranscript.runId", "Operator transcript must bind to run id.")
        commands = transcript.get("commands")
        require(isinstance(commands, list) and commands, "operatorTranscript.commands", "Operator transcript commands are required.")
        if isinstance(commands, list):
            for index, command in enumerate(commands):
                if isinstance(command, dict):
                    require(command.get("dryRun") is True, f"operatorTranscript.commands[{index}].dryRun", "Operator command must be marked dry-run.")
                    require(command.get("exitCode") == 0, f"operatorTranscript.commands[{index}].exitCode", "Operator command must succeed in dry-run transcript.")

    source = scenario.get("source")
    require(isinstance(source, dict), "source", "Source evidence is required.")
    if isinstance(source, dict):
        require(source.get("runId") == run_id, "source.runId", "Source evidence must bind to run id.")
        require(source.get("status") == "pass", "source.status", "Source checks must pass.")

    budget = scenario.get("budget", {})
    require(isinstance(budget, dict), "budget", "Budget evidence is required.")
    if isinstance(budget, dict):
        require(budget.get("runId") == run_id, "budget.runId", "Budget evidence must bind to run id.")
        require(budget.get("estimatedUsd", 1) <= budget.get("ceilingUsd", 0), "budget.estimatedUsd", "Estimated spend must be within ceiling.")

    rollback = scenario.get("rollback", {})
    require(isinstance(rollback, dict), "rollback", "Rollback evidence is required.")
    if isinstance(rollback, dict):
        require(rollback.get("runId") == run_id, "rollback.runId", "Rollback evidence must bind to run id.")
        require(rollback.get("status") == "pass", "rollback.status", "Rollback proof must pass.")

    reputation = scenario.get("reputation", {})
    require(isinstance(reputation, dict), "reputation", "Reputation evidence is required.")
    if isinstance(reputation, dict):
        require(reputation.get("runId") == run_id, "reputation.runId", "Reputation evidence must bind to run id.")
        require(reputation.get("source") == "receipt-and-eval", "reputation.source", "Reputation must derive from receipt and eval evidence.")
        require(reputation.get("emittedLive") is False, "reputation.emittedLive", "Reputation must not be emitted live.")

    return findings


def trace_event(run_id: str, event_name: str, status: str = "pass", **fields: Any) -> dict[str, Any]:
    return {
        "event": event_name,
        "status": status,
        "runId": run_id,
        "traceId": run_id,
        **fields,
        **BOUNDARY_FLAGS,
    }


def build_success_artifact(scenario: dict[str, Any]) -> dict[str, Any]:
    run_id = scenario["runId"]
    quote = scenario["quote"]
    return {
        "runId": run_id,
        "intent": {
            "intentId": artifact_id("rap-intent", run_id, "intent"),
            "adl": scenario["adl"],
            "task": scenario["task"],
            "dryRun": True,
        },
        "quote": {
            "quoteId": artifact_id("quote", run_id, "quote"),
            "rail": quote["rail"],
            "amount": quote["amount"],
            "currency": quote["currency"],
            "expiresAfterSeconds": quote["expiresAfterSeconds"],
        },
        "paymentHandoff": {
            "handoffId": artifact_id("handoff", run_id, "payment"),
            "runId": run_id,
            "mode": "metadata-only",
            "selectedRail": quote["rail"],
            "livePaymentPrepared": False,
        },
        "receipt": {
            "receiptId": artifact_id("receipt", run_id, "receipt"),
            "runId": run_id,
            "paymentHandoffId": run_id,
            "serviceResultStatus": "pass",
            "requiredEvalGateStatus": "pass",
            "requestHash": scenario["receipt"]["requestHash"],
            "responseHash": scenario["receipt"]["responseHash"],
        },
        "operatorEvidence": scenario["operatorTranscript"],
        "sourceEvidence": scenario["source"],
        "budgetEvidence": scenario["budget"],
        "rollbackEvidence": scenario["rollback"],
        "reputationEvidence": scenario["reputation"],
        "traceEvents": [
            trace_event(run_id, "rap_bridge.intent.accepted", adl=scenario["adl"]),
            trace_event(run_id, "rap_bridge.quote.prepared", quoteRail=quote["rail"]),
            trace_event(run_id, "rap_bridge.payment_handoff.prepared", paymentRailAccess=False),
            trace_event(run_id, "rap_bridge.receipt.emitted", receiptMode="dry-run"),
            trace_event(run_id, "rap_bridge.reputation.prepared", emittedLive=False),
            trace_event(run_id, "rap_bridge.rollback.proven", rollbackStatus=scenario["rollback"]["status"]),
        ],
        **BOUNDARY_FLAGS,
    }


def evaluate_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    status = "fail" if findings else "pass"
    result: dict[str, Any] = {
        "id": scenario.get("id"),
        "kind": scenario.get("kind"),
        "expectedStatus": scenario.get("expectedStatus"),
        "status": status,
        "failClosed": status == "fail",
        "findings": findings,
        **BOUNDARY_FLAGS,
    }
    if status == "pass":
        result["artifact"] = build_success_artifact(scenario)
        result["artifactHash"] = stable_hash(json.dumps(result["artifact"], sort_keys=True))
    else:
        result["artifact"] = None
        result["denialTranscript"] = {
            "runId": scenario.get("runId"),
            "reason": findings[0]["reason"] if findings else "unknown",
            "nextMode": "local-only",
            "liveActionTaken": False,
            **BOUNDARY_FLAGS,
        }
    return result


def build_report(doc: dict[str, Any]) -> dict[str, Any]:
    results = [evaluate_scenario(scenario) for scenario in doc.get("scenarios", [])]
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    boundaries = doc.get("boundaries", {})
    require(isinstance(boundaries, dict), "boundaries", "Boundary flags are required.")
    if isinstance(boundaries, dict):
        for flag, expected in BOUNDARY_FLAGS.items():
            require(boundaries.get(flag) is expected, f"boundaries.{flag}", f"Boundary must remain {expected}.")

    require(any(result["kind"] == "positive" for result in results), "scenarios", "At least one positive scenario is required.")
    negative_count = sum(1 for result in results if result["kind"] == "negative")
    require(negative_count >= 7, "scenarios", "At least seven fail-closed negative scenarios are required.")
    for index, result in enumerate(results):
        require(
            result["status"] == result["expectedStatus"],
            f"results[{index}].status",
            "Scenario status must match the expected status.",
        )
        if result["kind"] == "negative":
            require(result["failClosed"] is True, f"results[{index}].failClosed", "Negative scenarios must fail closed.")

    all_findings = findings + [
        item
        for result in results
        for item in result["findings"]
    ]
    passing = [result for result in results if result["status"] == "pass"]
    return {
        "mode": "rap-bridge-local-executable-dry-run-prototype",
        "issue": 245,
        "parentEpic": 220,
        "status": "pass" if not findings else "fail",
        "findings": findings,
        "summary": {
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": negative_count,
            "failClosedScenarios": sum(1 for result in results if result["failClosed"]),
            "allScenarioFindings": len(all_findings),
            "artifactHashes": [result["artifactHash"] for result in passing],
        },
        "results": results,
        **BOUNDARY_FLAGS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", nargs="?", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = build_report(load_json(Path(args.fixture)))
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = args.output if args.output.is_absolute() else ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 3


if __name__ == "__main__":
    sys.exit(main())
