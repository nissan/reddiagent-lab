#!/usr/bin/env python3
"""Build deterministic beta runtime service activation evidence gate output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-runtime-service-activation-evidence-gate-scenarios.json"
PINNED_APPROVAL_PACKET_PATH = "tests/fixtures/beta-runtime-service-activation-approval-packet.json"
PINNED_APPROVAL_PACKET_SHA256 = "b5bd8232d1cca34387a24b71c412dec7e60a5e53c90d84d1a0737a3eef65227e"
REQUIRED_RUN_ID = "reddiagent-beta-0-runtime-service-activation-evidence-gate"
REQUIRED_PACKET_ID = "reddiagent-beta-0-runtime-service-activation-approval-packet"
REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_PACKET_STOP_CUE = (
    "STOP: this packet is approval evidence only; run a separate explicit live activation gate "
    "before any service, runtime, Docker, Coolify, devnet, payment, package, or mainnet action."
)
REQUIRED_NEXT_STEP_CUE = (
    "Hold after this explicit local evidence gate; live service activation still requires a separately "
    "approved bounded run with current operator approval, rollback path, trace/eval evidence, and no "
    "mainnet risk."
)
REQUIRED_OPERATOR_APPROVALS = (
    "runtime_owner_approval",
    "rollback_owner_approval",
    "security_reviewer_approval",
    "separate_live_activation_run_approval",
)
REQUIRED_ENV_SECRET_NAMES = (
    "REDDIAGENT_RUNTIME_ACTIVATION_APPROVED",
    "REDDIAGENT_RUNTIME_DISABLE_SWITCH",
    "REDDIAGENT_TRACE_EVIDENCE_PATH",
    "REDDIAGENT_ROLLBACK_PLAN_PATH",
)
UNSAFE_FLAG_FIELDS = (
    "liveRuntimeRequested",
    "liveServiceActivationRequested",
    "serviceStartRequested",
    "dockerStartRequested",
    "surfpoolStartRequested",
    "coolifyDeploymentRequested",
    "providerApiAccessRequested",
    "credentialAccessRequested",
    "hostedFetchRequested",
    "liveMcpRequested",
    "walletRequested",
    "paymentRequested",
    "facilitatorRequested",
    "settlementRequested",
    "deploymentRequested",
    "packagePublishingRequested",
    "archivePublishingRequested",
    "packageArchivePublishRequested",
    "publicPublishingRequested",
    "productionClaimRequested",
    "devnetRequested",
    "mainnetRequested",
    "mainnetEnabled",
    "activationCompleted",
)

sys.path.insert(0, str(ROOT / "scripts"))
import beta_e2e_acceptance_smoke_runner as smoke  # noqa: E402
import beta_runtime_activation_evidence_gate as gate  # noqa: E402
import beta_runtime_service_activation_approval_packet as packet  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return doc


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def finding(path: str, reason: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


def merge_scenario(defaults: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(defaults))
    for key, value in scenario.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def expected_hash_map(scenario: dict[str, Any]) -> dict[str, str]:
    return {
        item["path"]: item.get("sha256", "")
        for item in scenario.get("expectedArtifactHashes", [])
        if isinstance(item, dict) and item.get("path")
    }


def accepted_packet_result(doc: dict[str, Any]) -> dict[str, Any] | None:
    for result in doc.get("results", []):
        if result.get("id") == "runtime-service-approval-packet-ready-pass":
            return result
    for result in doc.get("results", []):
        if result.get("status") == "pass" and result.get("verdict") == "approval-packet-ready":
            return result
    return None


def false_boundary_findings(boundaries: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for field in (
        "serviceStarted",
        "networkAccess",
        "credentialAccess",
        "providerApiAccess",
        "hostedFetch",
        "liveMcpInvocation",
        "liveRuntimeActivation",
        "dockerStarted",
        "surfpoolStarted",
        "coolifyDeployment",
        "walletAccess",
        "paymentAccess",
        "facilitatorAccess",
        "settlementAccess",
        "devnetAccess",
        "mainnetAccess",
        "deploymentPublished",
        "packagePublished",
        "archivePublished",
        "publicPublished",
        "externalSpend",
    ):
        if boundaries.get(field) is not False:
            findings.append(finding(f"{prefix}.{field}", f"{field} must remain false."))
    return findings


def approval_packet_findings(doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if doc.get("mode") != "beta-runtime-service-activation-approval-packet":
        findings.append(finding("approvalPacketFixture.mode", "Pinned #291 fixture must be the approval packet."))
    if doc.get("issue") != 291 or doc.get("parentEpic") != 220:
        findings.append(finding("approvalPacketFixture.issue", "Pinned fixture must belong to issue #291 and parent #220."))
    if doc.get("follows") != [289, 287, 285]:
        findings.append(finding("approvalPacketFixture.follows", "Pinned #291 packet must preserve #289/#287/#285 lineage."))
    if doc.get("status") != "pass":
        findings.append(finding("approvalPacketFixture.status", "Pinned #291 fixture must pass."))
    findings.extend(false_boundary_findings(doc.get("boundaries", {}), "approvalPacketFixture.boundaries"))
    result = accepted_packet_result(doc)
    if not result:
        findings.append(finding("approvalPacketFixture.results", "Pinned #291 fixture must include accepted approval-packet evidence."))
        return findings
    if result.get("status") != "pass" or result.get("verdict") != "approval-packet-ready":
        findings.append(finding("approvalPacketFixture.results.verdict", "Accepted #291 result must pass with approval-packet-ready verdict."))
    packet_doc = result.get("approvalPacket", {})
    if not isinstance(packet_doc, dict):
        findings.append(finding("approvalPacketFixture.results.approvalPacket", "Accepted #291 approval packet must be an object."))
        return findings
    if packet_doc.get("approvalPacketId") != REQUIRED_PACKET_ID:
        findings.append(finding("approvalPacketFixture.results.approvalPacketId", f"Packet id must be `{REQUIRED_PACKET_ID}`."))
    selected = packet_doc.get("selectedRuntimePath", {})
    if selected.get("adlPath") != gate.REQUIRED_ADL_PATH or selected.get("reviewedCommand") != gate.LOCAL_COMMAND_PREFIX:
        findings.append(finding("approvalPacketFixture.results.selectedRuntimePath", "Accepted #291 packet may select only examples/simple-agent.yaml."))
    if tuple(packet_doc.get("requiredOperatorApprovals", [])) != REQUIRED_OPERATOR_APPROVALS:
        findings.append(finding("approvalPacketFixture.results.requiredOperatorApprovals", "Accepted #291 packet must require all operator approvals."))
    secret_names = tuple(item.get("name") for item in packet_doc.get("redactedEnvSecretRequirements", []) if isinstance(item, dict))
    if secret_names != REQUIRED_ENV_SECRET_NAMES:
        findings.append(finding("approvalPacketFixture.results.redactedEnvSecretRequirements", "Accepted #291 packet must preserve the name-only env/secret set."))
    if any(item.get("value") != "<redacted>" for item in packet_doc.get("redactedEnvSecretRequirements", []) if isinstance(item, dict)):
        findings.append(finding("approvalPacketFixture.results.redactedEnvSecretRequirements.value", "Accepted #291 packet must not include secret values."))
    rollback = packet_doc.get("rollbackDisablePlan", {})
    if rollback.get("disableCommand") != "local-runtime:disable --target simple-agent --dry-run":
        findings.append(finding("approvalPacketFixture.results.rollbackDisablePlan.disableCommand", "Accepted #291 packet must preserve dry-run disable command."))
    if rollback.get("rollbackCommand") != "local-runtime:rollback --target simple-agent --dry-run":
        findings.append(finding("approvalPacketFixture.results.rollbackDisablePlan.rollbackCommand", "Accepted #291 packet must preserve dry-run rollback command."))
    if rollback.get("liveRuntimeEnabledAfterRollback") is not False:
        findings.append(finding("approvalPacketFixture.results.rollbackDisablePlan.liveRuntimeEnabledAfterRollback", "Rollback evidence must leave live runtime disabled."))
    transcript = packet_doc.get("dryRunCommandTranscript", {})
    if transcript.get("command") != "python scripts/beta_runtime_service_activation_approval_packet.py --output tests/fixtures/beta-runtime-service-activation-approval-packet.json":
        findings.append(finding("approvalPacketFixture.results.dryRunCommandTranscript.command", "Accepted #291 packet must preserve the deterministic dry-run transcript."))
    if transcript.get("exitCode") != 0:
        findings.append(finding("approvalPacketFixture.results.dryRunCommandTranscript.exitCode", "Accepted #291 packet dry-run transcript must exit 0."))
    if packet_doc.get("riskVerdict") != "approval-packet-ready":
        findings.append(finding("approvalPacketFixture.results.riskVerdict", "Accepted #291 packet risk verdict must be approval-packet-ready."))
    if packet_doc.get("stopCue") != REQUIRED_PACKET_STOP_CUE:
        findings.append(finding("approvalPacketFixture.results.stopCue", "Accepted #291 packet must preserve the separate-live-run stop cue."))
    hashes = packet_doc.get("sourceEvidenceHashes", {})
    for label in ("canaryFixture", "activationEvidenceFixture", "e2eSmokeFixture"):
        binding = hashes.get(label)
        if not isinstance(binding, dict) or binding.get("hashMatches") is not True or not binding.get("sha256"):
            findings.append(finding(f"approvalPacketFixture.results.sourceEvidenceHashes.{label}", f"{label} must be present with hashMatches true."))
    if not hashes.get("acceptedCanaryResultSha256") or not hashes.get("acceptedActivationEvidenceSha256") or not hashes.get("acceptedE2eSmokeSha256"):
        findings.append(finding("approvalPacketFixture.results.sourceEvidenceHashes.upstream", "Accepted #291 packet must preserve #289/#287/#285 source evidence hashes."))
    findings.extend(smoke.sensitive_payload_findings(packet_doc, "approvalPacketFixture.results.approvalPacket"))
    findings.extend(smoke.unsafe_claim_findings(packet_doc, "approvalPacketFixture.results.approvalPacket"))
    findings.extend(false_boundary_findings(packet_doc.get("boundaries", {}), "approvalPacketFixture.results.boundaries"))
    return findings


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("runEvidenceId") != REQUIRED_RUN_ID:
        findings.append(finding("runEvidenceId", f"Run evidence id must be `{REQUIRED_RUN_ID}`."))
    if scenario.get("approvalPacketId") != REQUIRED_PACKET_ID:
        findings.append(finding("approvalPacketId", f"Approval packet id must be `{REQUIRED_PACKET_ID}`."))
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    if scenario.get("approvalPacketFixturePath", PINNED_APPROVAL_PACKET_PATH) != PINNED_APPROVAL_PACKET_PATH:
        findings.append(finding("approvalPacketFixture.path", f"Approval packet path must be pinned to `{PINNED_APPROVAL_PACKET_PATH}`."))
    if expected_hash_map(scenario).get(PINNED_APPROVAL_PACKET_PATH) != PINNED_APPROVAL_PACKET_SHA256:
        findings.append(finding("approvalPacketFixture.expectedSha256", "Approval packet expected sha256 must match the pinned #291 approval packet hash."))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in this local evidence gate."))
    approvals = scenario.get("operatorApprovalsRecorded", {})
    if not isinstance(approvals, dict):
        findings.append(finding("operatorApprovalsRecorded", "Operator approvals must be an object."))
    else:
        for name in REQUIRED_OPERATOR_APPROVALS:
            if approvals.get(name) is not True:
                findings.append(finding(f"operatorApprovalsRecorded.{name}", f"{name} must be recorded true."))
    checklist = scenario.get("preflightChecklist", [])
    if not isinstance(checklist, list) or len(checklist) < 6:
        findings.append(finding("preflightChecklist", "Preflight checklist must cover approval, rollback, trace/eval, bounds, and mainnet stop conditions."))
    else:
        joined = " ".join(item for item in checklist if isinstance(item, str)).lower()
        for marker in ("operator approval", "rollback", "trace/eval", "dry-run substitute", "mainnet"):
            if marker not in joined:
                findings.append(finding("preflightChecklist", f"Preflight checklist must mention {marker}."))
    decision = scenario.get("activationDecision", {})
    if not isinstance(decision, dict):
        findings.append(finding("activationDecision", "Activation decision must be an object."))
    else:
        if decision.get("decision") not in {"hold", "rollback"}:
            findings.append(finding("activationDecision.decision", "This deterministic local gate may only decide hold or rollback."))
        if decision.get("liveActionAuthorized") is not False:
            findings.append(finding("activationDecision.liveActionAuthorized", "Live action must not be authorized by this local gate."))
    transcript = scenario.get("boundedRunTranscript", {})
    if not isinstance(transcript, dict):
        findings.append(finding("boundedRunTranscript", "Run transcript must be an object."))
    else:
        if transcript.get("mode") != "dry-run-substitute":
            findings.append(finding("boundedRunTranscript.mode", "Transcript must be the bounded dry-run substitute."))
        if transcript.get("command") != "python scripts/beta_runtime_service_activation_evidence_gate.py --output tests/fixtures/beta-runtime-service-activation-evidence-gate.json":
            findings.append(finding("boundedRunTranscript.command", "Transcript command must be the deterministic evidence gate command."))
        if transcript.get("exitCode") != 0:
            findings.append(finding("boundedRunTranscript.exitCode", "Transcript exit code must be 0."))
    trace = scenario.get("traceEvalSummary", {})
    if not isinstance(trace, dict):
        findings.append(finding("traceEvalSummary", "Trace/eval summary must be an object."))
    else:
        if trace.get("completionStatus") != "pass" or trace.get("requiredGateStatus") != "pass" or trace.get("toolExecution") is not None:
            findings.append(finding("traceEvalSummary", "Trace/eval summary must pass without tool execution."))
    rollback = scenario.get("rollbackDisableVerification", {})
    if not isinstance(rollback, dict):
        findings.append(finding("rollbackDisableVerification", "Rollback/disable verification must be an object."))
    else:
        if rollback.get("disableCommand") != "local-runtime:disable --target simple-agent --dry-run":
            findings.append(finding("rollbackDisableVerification.disableCommand", "Disable verification must use the pinned dry-run command."))
        if rollback.get("rollbackCommand") != "local-runtime:rollback --target simple-agent --dry-run":
            findings.append(finding("rollbackDisableVerification.rollbackCommand", "Rollback verification must use the pinned dry-run command."))
        if rollback.get("liveRuntimeEnabledAfterRollback") is not False:
            findings.append(finding("rollbackDisableVerification.liveRuntimeEnabledAfterRollback", "Rollback verification must leave live runtime disabled."))
    if scenario.get("riskVerdict") != "hold-for-separate-live-run":
        findings.append(finding("riskVerdict", "Risk verdict must hold for a separate live run."))
    if scenario.get("nextStepCue") != REQUIRED_NEXT_STEP_CUE:
        findings.append(finding("nextStepCue", "Next-step cue must stop before live activation."))
    findings.extend(smoke.sensitive_payload_findings(scenario, "scenario"))
    findings.extend(smoke.unsafe_claim_findings(scenario, "scenario"))
    findings.extend(gate.command_findings(scenario.get("localCommands", []), "localCommands"))
    return findings


def verdict_for(status: str, requested: str | None) -> str:
    if status == "pass":
        return requested if requested in {"hold-for-live-run", "rollback", "reject"} else "hold-for-live-run"
    if requested == "reject":
        return "reject"
    return "hold"


def build_run_evidence(
    scenario: dict[str, Any],
    approval_doc: dict[str, Any],
    approval_binding: dict[str, Any],
    commit: str,
) -> dict[str, Any]:
    accepted = accepted_packet_result(approval_doc) or {}
    packet_doc = accepted.get("approvalPacket", {}) if isinstance(accepted.get("approvalPacket", {}), dict) else {}
    source_hashes = packet_doc.get("sourceEvidenceHashes", {}) if isinstance(packet_doc.get("sourceEvidenceHashes", {}), dict) else {}
    return {
        "runEvidenceId": scenario.get("runEvidenceId"),
        "approvalPacketId": scenario.get("approvalPacketId"),
        "releaseId": scenario.get("releaseId"),
        "releaseCandidateId": scenario.get("releaseCandidateId"),
        "sourceCommit": commit,
        "approvalPacketEvidence": {
            "fixture": approval_binding,
            "acceptedResultId": accepted.get("id"),
            "acceptedVerdict": accepted.get("verdict"),
            "acceptedApprovalPacketSha256": gate.sha256_text(dump_json(packet_doc)) if packet_doc else None,
            "sourceEvidenceHashes": source_hashes,
        },
        "selectedRuntimePath": packet_doc.get("selectedRuntimePath", {}),
        "operatorApprovalsRecorded": scenario.get("operatorApprovalsRecorded", {}),
        "preflightChecklist": scenario.get("preflightChecklist", []),
        "activationDecision": scenario.get("activationDecision", {}),
        "boundedRunTranscript": scenario.get("boundedRunTranscript", {}),
        "traceEvalSummary": scenario.get("traceEvalSummary", {}),
        "rollbackDisableVerification": scenario.get("rollbackDisableVerification", {}),
        "riskVerdict": scenario.get("riskVerdict"),
        "nextStepCue": scenario.get("nextStepCue"),
        "boundaries": {
            "deterministicLocalOnly": True,
            "dryRunSubstituteOnly": True,
            "actualServiceMutation": False,
            "serviceStarted": False,
            "networkAccess": False,
            "credentialAccess": False,
            "providerApiAccess": False,
            "hostedFetch": False,
            "liveMcpInvocation": False,
            "liveRuntimeActivation": False,
            "dockerStarted": False,
            "surfpoolStarted": False,
            "coolifyDeployment": False,
            "walletAccess": False,
            "paymentAccess": False,
            "facilitatorAccess": False,
            "settlementAccess": False,
            "devnetAccess": False,
            "mainnetAccess": False,
            "deploymentPublished": False,
            "packagePublished": False,
            "archivePublished": False,
            "publicPublished": False,
            "externalSpend": False,
        },
    }


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    hashes = expected_hash_map(scenario)
    packet_path = scenario.get("approvalPacketFixturePath", PINNED_APPROVAL_PACKET_PATH)
    expected_sha = PINNED_APPROVAL_PACKET_SHA256 if packet_path == PINNED_APPROVAL_PACKET_PATH else hashes.get(packet_path, "")
    approval_binding = gate.artifact_binding(packet_path, expected_sha, "approvalPacketFixture", findings)
    approval_doc: dict[str, Any] = {}
    path = ROOT / packet_path
    if path.exists():
        try:
            approval_doc = load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            findings.append(finding("approvalPacketFixture.json", f"Approval packet evidence must be JSON: {exc}"))
    findings.extend(approval_packet_findings(approval_doc))
    status = "pass" if not findings else "fail"
    verdict = verdict_for(status, scenario.get("requestedVerdict"))
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "status": status,
        "expectedStatus": scenario["expectedStatus"],
        "verdict": verdict,
        "expectedVerdict": scenario["expectedVerdict"],
        "findings": findings,
        "sourceCommit": commit,
        "runEvidence": build_run_evidence(scenario, approval_doc, approval_binding, commit),
    }


def build_report(doc: dict[str, Any], commit: str | None = None) -> dict[str, Any]:
    actual_commit = commit or gate.source_commit()
    defaults = doc.get("defaults", {})
    results = [build_result(merge_scenario(defaults, scenario), actual_commit) for scenario in doc.get("scenarios", [])]
    mismatches = [
        finding(f"results[{index}].status", f"{result['id']} produced {result['status']}/{result['verdict']} but expected {result['expectedStatus']}/{result['expectedVerdict']}.")
        for index, result in enumerate(results)
        if result["status"] != result["expectedStatus"] or result["verdict"] != result["expectedVerdict"]
    ]
    return {
        "mode": "beta-runtime-service-activation-evidence-gate",
        "issue": 293,
        "parentEpic": 220,
        "follows": [291, 289, 287, 285],
        "status": "pass" if not mismatches else "fail",
        "sourceCommit": actual_commit,
        "releaseId": doc.get("releaseId"),
        "findings": mismatches,
        "summary": {
            "holdForLiveRunVerdicts": sum(1 for result in results if result["verdict"] == "hold-for-live-run"),
            "holdVerdicts": sum(1 for result in results if result["verdict"] == "hold"),
            "rollbackVerdicts": sum(1 for result in results if result["verdict"] == "rollback"),
            "rejectVerdicts": sum(1 for result in results if result["verdict"] == "reject"),
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["kind"] == "negative" and result["status"] == "fail"),
        },
        "boundaries": {
            "deterministicLocalOnly": True,
            "dryRunSubstituteOnly": True,
            "actualServiceMutation": False,
            "serviceStarted": False,
            "networkAccess": False,
            "credentialAccess": False,
            "providerApiAccess": False,
            "hostedFetch": False,
            "liveMcpInvocation": False,
            "liveRuntimeActivation": False,
            "dockerStarted": False,
            "surfpoolStarted": False,
            "coolifyDeployment": False,
            "walletAccess": False,
            "paymentAccess": False,
            "facilitatorAccess": False,
            "settlementAccess": False,
            "devnetAccess": False,
            "mainnetAccess": False,
            "deploymentPublished": False,
            "packagePublished": False,
            "archivePublished": False,
            "publicPublished": False,
            "externalSpend": False,
        },
        "mainnetStatement": "This evidence gate does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Evidence gate scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated evidence gate JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(load_json(Path(args.scenarios)))
    payload = dump_json(report)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
