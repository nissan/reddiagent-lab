#!/usr/bin/env python3
"""Build deterministic local beta runtime service activation approval packet evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-runtime-service-activation-approval-packet-scenarios.json"
PINNED_CANARY_PATH = "tests/fixtures/beta-runtime-activation-canary-runner.json"
REQUIRED_PACKET_ID = "reddiagent-beta-0-runtime-service-activation-approval-packet"
REQUIRED_CANARY_ID = "reddiagent-beta-0-local-runtime-activation-canary"
REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_STOP_CUE = (
    "STOP: this packet is approval evidence only; run a separate explicit live activation gate "
    "before any service, runtime, Docker, Coolify, devnet, payment, package, or mainnet action."
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
)

sys.path.insert(0, str(ROOT / "scripts"))
import beta_e2e_acceptance_smoke_runner as smoke  # noqa: E402
import beta_runtime_activation_canary_runner as canary  # noqa: E402
import beta_runtime_activation_evidence_gate as gate  # noqa: E402


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


def load_canary(path_text: str, findings: list[dict[str, str]]) -> dict[str, Any]:
    path = ROOT / path_text
    if not path.exists():
        return {}
    try:
        return load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(finding("canaryEvidenceFixture.json", f"Canary evidence must be JSON: {exc}"))
        return {}


def accepted_canary_result(doc: dict[str, Any]) -> dict[str, Any] | None:
    for result in doc.get("results", []):
        if result.get("id") == "runtime-activation-canary-accept-pass":
            return result
    for result in doc.get("results", []):
        if result.get("status") == "pass" and result.get("verdict") == "accept-canary":
            return result
    return None


def boundary_findings(boundaries: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    required_false = (
        "serviceStarted",
        "networkAccess",
        "credentialAccess",
        "providerApiAccess",
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
    )
    for field in required_false:
        if boundaries.get(field) is not False:
            findings.append(finding(f"{prefix}.{field}", f"{field} must remain false."))
    return findings


def canary_findings(doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if doc.get("mode") != "beta-local-runtime-activation-canary-runner":
        findings.append(finding("canaryEvidenceFixture.mode", "Pinned #289 fixture must be the activation canary runner."))
    if doc.get("issue") != 289 or doc.get("parentEpic") != 220:
        findings.append(finding("canaryEvidenceFixture.issue", "Pinned fixture must belong to issue #289 and parent #220."))
    if doc.get("status") != "pass":
        findings.append(finding("canaryEvidenceFixture.status", "Pinned #289 fixture must pass."))
    if doc.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("canaryEvidenceFixture.releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    findings.extend(boundary_findings(doc.get("boundaries", {}), "canaryEvidenceFixture.boundaries"))
    accepted = accepted_canary_result(doc)
    if not accepted:
        findings.append(finding("canaryEvidenceFixture.results", "Pinned #289 fixture must include accepted canary evidence."))
        return findings
    if accepted.get("canaryId") != REQUIRED_CANARY_ID:
        findings.append(finding("canaryEvidenceFixture.results.canaryId", f"Canary id must be `{REQUIRED_CANARY_ID}`."))
    if accepted.get("status") != "pass" or accepted.get("verdict") != "accept-canary":
        findings.append(finding("canaryEvidenceFixture.results.verdict", "Accepted #289 result must pass with accept-canary verdict."))
    selected = accepted.get("selectedRuntimePath", {})
    if selected.get("adlPath") != gate.REQUIRED_ADL_PATH or selected.get("reviewedCommand") != gate.LOCAL_COMMAND_PREFIX:
        findings.append(finding("canaryEvidenceFixture.results.selectedRuntimePath", "Accepted #289 canary may select only the reviewed simple local ADL runtime path."))
    transcript = accepted.get("canaryCommandTranscript", {})
    if transcript.get("command") != gate.LOCAL_COMMAND_PREFIX or transcript.get("exitCode") != 0:
        findings.append(finding("canaryEvidenceFixture.results.canaryCommandTranscript", "Accepted #289 transcript must be the simple local ADL command with exit code 0."))
    if transcript.get("traceEvents") != gate.REQUIRED_TRACE_EVENTS:
        findings.append(finding("canaryEvidenceFixture.results.canaryCommandTranscript.traceEvents", "Accepted #289 trace sequence must match reviewed events."))
    summary = accepted.get("traceEvalSummary", {})
    if summary.get("completionStatus") != "pass" or summary.get("requiredGateStatus") != "pass" or summary.get("toolExecution") is not None:
        findings.append(finding("canaryEvidenceFixture.results.traceEvalSummary", "Accepted #289 trace/eval summary must pass without tool execution."))
    before = accepted.get("operatorControlStateBefore", {})
    after = accepted.get("operatorControlStateAfter", {})
    if before.get("runtimeEnabled") is not False or before.get("disableSwitchAvailable") is not True:
        findings.append(finding("canaryEvidenceFixture.results.operatorControlStateBefore", "Accepted #289 before-state must keep runtime disabled with disable switch available."))
    if after.get("runtimeEnabled") is not False or after.get("disableSwitchAvailable") is not True:
        findings.append(finding("canaryEvidenceFixture.results.operatorControlStateAfter", "Accepted #289 after-state must keep runtime disabled with disable switch available."))
    rollback = accepted.get("rollbackDisableDryRunProof", {})
    if rollback.get("liveRuntimeEnabledAfterRollback") is not False:
        findings.append(finding("canaryEvidenceFixture.results.rollbackDisableDryRunProof", "Accepted #289 rollback proof must leave live runtime disabled."))
    activation = accepted.get("activationEvidence", {})
    if not activation.get("acceptedSourceSmoke") or not activation.get("acceptedActivationEvidenceSha256"):
        findings.append(finding("canaryEvidenceFixture.results.activationEvidence.upstreamHashes", "Accepted #289 evidence must preserve upstream #287/#285 source hashes."))
    findings.extend(smoke.sensitive_payload_findings(accepted, "canaryEvidenceFixture.results"))
    findings.extend(smoke.unsafe_claim_findings(accepted, "canaryEvidenceFixture.results"))
    findings.extend(gate.command_findings(accepted.get("localCommands", []), "canaryEvidenceFixture.results.localCommands"))
    findings.extend(boundary_findings(accepted.get("boundaries", {}), "canaryEvidenceFixture.results.boundaries"))
    return findings


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("approvalPacketId") != REQUIRED_PACKET_ID:
        findings.append(finding("approvalPacketId", f"Approval packet id must be `{REQUIRED_PACKET_ID}`."))
    if scenario.get("canaryId") != REQUIRED_CANARY_ID:
        findings.append(finding("canaryId", f"Canary id must be `{REQUIRED_CANARY_ID}`."))
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    if scenario.get("canaryEvidenceFixturePath", PINNED_CANARY_PATH) != PINNED_CANARY_PATH:
        findings.append(finding("canaryEvidenceFixture.path", f"Canary evidence fixture path must be pinned to `{PINNED_CANARY_PATH}`."))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in this local approval packet."))
    approvals = scenario.get("requiredOperatorApprovals", [])
    if tuple(approvals) != REQUIRED_OPERATOR_APPROVALS:
        findings.append(finding("requiredOperatorApprovals", "Required operator approvals must be complete and pinned."))
    env_names = scenario.get("redactedEnvSecretNames", [])
    if tuple(env_names) != REQUIRED_ENV_SECRET_NAMES:
        findings.append(finding("redactedEnvSecretNames", "Env/secret requirements must be the approved name-only set."))
    if any("=" in item or " " in item for item in env_names if isinstance(item, str)):
        findings.append(finding("redactedEnvSecretNames", "Env/secret requirements must be names only, with no values."))
    checklist = scenario.get("liveActionChecklist", [])
    if not isinstance(checklist, list) or len(checklist) < 5:
        findings.append(finding("liveActionChecklist", "Live-action checklist must include the separate activation prerequisites."))
    elif not any("separate explicit live activation" in item for item in checklist if isinstance(item, str)):
        findings.append(finding("liveActionChecklist", "Checklist must require a separate explicit live activation run."))
    rollback = scenario.get("rollbackDisablePlan", {})
    if rollback.get("disableCommand") != "local-runtime:disable --target simple-agent --dry-run":
        findings.append(finding("rollbackDisablePlan.disableCommand", "Disable plan must use the pinned dry-run command."))
    if rollback.get("rollbackCommand") != "local-runtime:rollback --target simple-agent --dry-run":
        findings.append(finding("rollbackDisablePlan.rollbackCommand", "Rollback plan must use the pinned dry-run command."))
    if rollback.get("liveRuntimeEnabledAfterRollback") is not False:
        findings.append(finding("rollbackDisablePlan.liveRuntimeEnabledAfterRollback", "Rollback plan must leave live runtime disabled."))
    transcript = scenario.get("dryRunCommandTranscript", {})
    if transcript.get("command") != "python scripts/beta_runtime_service_activation_approval_packet.py --output tests/fixtures/beta-runtime-service-activation-approval-packet.json":
        findings.append(finding("dryRunCommandTranscript.command", "Dry-run transcript must be the deterministic packet generation command."))
    if transcript.get("exitCode") != 0:
        findings.append(finding("dryRunCommandTranscript.exitCode", "Dry-run command transcript must exit 0."))
    if scenario.get("riskVerdict") != "approval-packet-ready":
        findings.append(finding("riskVerdict", "Passing packet risk verdict must be approval-packet-ready."))
    if scenario.get("stopCue") != REQUIRED_STOP_CUE:
        findings.append(finding("stopCue", "Packet must include the explicit separate-live-run stop cue."))
    findings.extend(smoke.sensitive_payload_findings(scenario, "scenario"))
    findings.extend(smoke.unsafe_claim_findings(scenario, "scenario"))
    findings.extend(gate.command_findings(scenario.get("localCommands", []), "localCommands"))
    return findings


def verdict_for(status: str, requested: str | None) -> str:
    if status == "pass":
        return requested if requested in {"approval-packet-ready", "hold", "reject"} else "approval-packet-ready"
    if requested == "reject":
        return "reject"
    return "hold"


def build_approval_packet(scenario: dict[str, Any], canary_doc: dict[str, Any], canary_binding: dict[str, Any], commit: str) -> dict[str, Any]:
    accepted = accepted_canary_result(canary_doc) or {}
    activation = accepted.get("activationEvidence", {})
    if not isinstance(activation, dict):
        activation = {}
    source_smoke = activation.get("acceptedSourceSmoke", {})
    if not isinstance(source_smoke, dict):
        source_smoke = {}
    return {
        "approvalPacketId": scenario.get("approvalPacketId"),
        "releaseId": scenario.get("releaseId"),
        "releaseCandidateId": scenario.get("releaseCandidateId"),
        "sourceCommit": commit,
        "sourceEvidenceHashes": {
            "canaryFixture": canary_binding,
            "acceptedCanaryResultSha256": gate.sha256_text(dump_json(accepted)) if accepted else None,
            "activationEvidenceFixture": activation.get("fixture"),
            "acceptedActivationEvidenceSha256": activation.get("acceptedActivationEvidenceSha256"),
            "e2eSmokeFixture": source_smoke.get("fixture"),
            "acceptedE2eSmokeSha256": source_smoke.get("acceptedEvidenceSha256"),
        },
        "selectedRuntimePath": {
            "adlPath": gate.REQUIRED_ADL_PATH,
            "reviewedCommand": gate.LOCAL_COMMAND_PREFIX,
            "toolExecution": None,
        },
        "requiredOperatorApprovals": scenario.get("requiredOperatorApprovals", []),
        "liveActionChecklist": scenario.get("liveActionChecklist", []),
        "redactedEnvSecretRequirements": [{"name": name, "value": "<redacted>"} for name in scenario.get("redactedEnvSecretNames", [])],
        "rollbackDisablePlan": scenario.get("rollbackDisablePlan", {}),
        "dryRunCommandTranscript": scenario.get("dryRunCommandTranscript", {}),
        "traceEvalSummary": accepted.get("traceEvalSummary", {}),
        "operatorControlStateBefore": accepted.get("operatorControlStateBefore", {}),
        "operatorControlStateAfter": accepted.get("operatorControlStateAfter", {}),
        "riskVerdict": scenario.get("riskVerdict"),
        "stopCue": scenario.get("stopCue"),
        "boundaries": {
            "deterministicLocalOnly": True,
            "approvalPacketOnly": True,
            "requiresSeparateLiveActivationRun": True,
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
    canary_path = scenario.get("canaryEvidenceFixturePath", PINNED_CANARY_PATH)
    canary_binding = gate.artifact_binding(canary_path, hashes.get(canary_path, ""), "canaryEvidenceFixture", findings)
    canary_doc = load_canary(canary_path, findings)
    findings.extend(canary_findings(canary_doc))
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
        "approvalPacket": build_approval_packet(scenario, canary_doc, canary_binding, commit),
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
        "mode": "beta-runtime-service-activation-approval-packet",
        "issue": 291,
        "parentEpic": 220,
        "follows": [289, 287, 285],
        "status": "pass" if not mismatches else "fail",
        "sourceCommit": actual_commit,
        "releaseId": doc.get("releaseId"),
        "findings": mismatches,
        "summary": {
            "approvalPacketReadyVerdicts": sum(1 for result in results if result["verdict"] == "approval-packet-ready"),
            "holdVerdicts": sum(1 for result in results if result["verdict"] == "hold"),
            "rejectVerdicts": sum(1 for result in results if result["verdict"] == "reject"),
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["kind"] == "negative" and result["status"] == "fail"),
        },
        "boundaries": {
            "deterministicLocalOnly": True,
            "approvalPacketOnly": True,
            "requiresSeparateLiveActivationRun": True,
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
        "mainnetStatement": "This approval packet does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def write_packet(result: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / f"{result['approvalPacket']['approvalPacketId']}.json"
    payload = dump_json(result["approvalPacket"])
    manifest_path.write_text(payload)
    return {"manifestPath": str(manifest_path), "manifestSha256": gate.sha256_text(payload)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Approval packet scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated approval packet report JSON.")
    parser.add_argument("--packet-output-dir", type=Path, help="Explicit local directory for the accepted approval packet artifact.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(load_json(Path(args.scenarios)))
    if args.packet_output_dir:
        output_dir = args.packet_output_dir if args.packet_output_dir.is_absolute() else ROOT / args.packet_output_dir
        positive = next(result for result in report["results"] if result["id"] == "runtime-service-approval-packet-ready-pass")
        report["localApprovalPacketWrite"] = write_packet(positive, output_dir)
    payload = dump_json(report)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
