#!/usr/bin/env python3
"""Build Coolify public devnet demo readiness evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "coolify-devnet-public-demo-scenarios.json"
SENSITIVE_KEY = re.compile(r"(token|secret|password|private|credential|mnemonic|seed|wallet)", re.I)
SHA40 = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_PUBLIC_ROUTES = [
    "/",
    "/adl-validation-ui.html",
    "/beta-review-ui.html",
    "/prosumer-builder-static-export.html",
    "/public-demo-pitch.html",
    "/healthz.html",
]
PUBLIC_ARTIFACT_DENYLIST = [
    (re.compile(r"/Users/loki"), "Public deploy artifact must not contain local workspace paths."),
    (re.compile(r"op://"), "Public deploy artifact must not contain 1Password references."),
    (re.compile(r"\btoken\s*=", re.I), "Public deploy artifact must not contain token assignments."),
    (re.compile(r"\bsecret\s*=", re.I), "Public deploy artifact must not contain secret assignments."),
    (re.compile(r"\bpassword\s*=", re.I), "Public deploy artifact must not contain password assignments."),
    (re.compile(r"\bapi[_-]?key\s*=", re.I), "Public deploy artifact must not contain API key assignments."),
    (re.compile(r"sk-[A-Za-z0-9_-]{8,}"), "Public deploy artifact must not contain provider secret key markers."),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "Public deploy artifact must not contain private key material."),
    (re.compile(r"\bmainnet\s+(ready|enabled|active|live)\b", re.I), "Public deploy artifact must not claim mainnet readiness."),
]


def load_json(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text())
    if not isinstance(doc, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return doc


def merge_scenario(defaults: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(defaults))
    for key, value in scenario.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_commit() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout.strip()


def finding(path: str, reason: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


def collect_findings(scenario: dict[str, Any], commit: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    public_url = str(scenario.get("publicUrl", ""))
    repo = str(scenario.get("repo", ""))
    branch = str(scenario.get("branch", ""))
    resource_type = str(scenario.get("coolifyResourceType", ""))
    build_pack = str(scenario.get("buildPack", ""))
    dockerfile_path = str(scenario.get("dockerfilePath", ""))
    image_name = str(scenario.get("imageName", ""))
    image_tag_policy = str(scenario.get("imageTagPolicy", ""))
    health_path = str(scenario.get("healthPath", ""))
    publish_directory = str(scenario.get("publishDirectory", ""))
    routes = scenario.get("verifiedRoutes", [])
    claims = scenario.get("claims", {})
    boundaries = scenario.get("boundaries", {})
    env_contract = scenario.get("environmentContract", [])
    rollback = scenario.get("rollback", {})

    require(bool(SHA40.fullmatch(commit)), "sourceCommit", "Source commit must be a full git SHA.")
    require(public_url.startswith("https://") and public_url.endswith("/"), "publicUrl", "Public URL must be a full HTTPS URL ending in slash.")
    require(public_url.endswith(".preview.reddi.tech/"), "publicUrl", "Coolify demo must use the preview.reddi.tech preview domain.")
    require(repo == "git@github.com:reddinft/reddiagent-lab.git", "repo", "Repo must use the least-privilege private SSH URL.")
    require(branch.startswith("feat/public-coolify-devnet-demo-"), "branch", "Demo must deploy from an issue-scoped feature branch.")
    require(resource_type == "dockerimage", "coolifyResourceType", "Coolify demo must use the Docker Image resource path.")
    require(build_pack == "dockerimage", "buildPack", "Coolify demo must use a prebuilt image to avoid source-build regressions.")
    require(dockerfile_path == "/Dockerfile", "dockerfilePath", "Dockerfile path must be explicit as the image source.")
    require(image_name == "localhost:5000/reddiagent-devnet-demo", "imageName", "Image must use the VPS-local loopback registry.")
    require(image_tag_policy == "source-commit-short", "imageTagPolicy", "Image tag must be derived from the source commit short SHA.")
    require(publish_directory == "/usr/share/nginx/html", "publishDirectory", "Nginx static root must be explicit.")
    require(health_path == "/", "healthPath", "Health path must be the static root page.")
    for required_route in REQUIRED_PUBLIC_ROUTES:
        require(required_route in routes, "verifiedRoutes", f"Missing required public route: {required_route}")

    for path in scenario.get("requiredLocalFiles", []):
        local = ROOT / path
        require(local.exists(), f"requiredLocalFiles.{path}.exists", "Required deploy artifact is missing.")
        if local.exists():
            text = local.read_text(errors="ignore")
            for pattern, reason in PUBLIC_ARTIFACT_DENYLIST:
                require(not pattern.search(text), f"requiredLocalFiles.{path}.content", reason)

    require(claims.get("publicDemo") is True, "claims.publicDemo", "Public demo claim must be explicit.")
    require(claims.get("devnetDemo") is True, "claims.devnetDemo", "Devnet demo claim must be explicit.")
    require(claims.get("mainnetReady") is False, "claims.mainnetReady", "Mainnet readiness must stay false.")
    require(claims.get("productionReady") is False, "claims.productionReady", "Production readiness must stay false.")
    require(claims.get("settlementEnabled") is False, "claims.settlementEnabled", "Settlement must stay disabled.")
    require(claims.get("paymentEnabled") is False, "claims.paymentEnabled", "Payment access must stay disabled.")
    require(claims.get("liveMcpEnabled") is False, "claims.liveMcpEnabled", "Live MCP invocation must stay disabled.")
    require(claims.get("providerProductCallsEnabled") is False, "claims.providerProductCallsEnabled", "Provider product calls must stay disabled.")

    require(boundaries.get("coolifyPublicUrlAllowed") is True, "boundaries.coolifyPublicUrlAllowed", "Coolify public URL must be allowed for this lane.")
    require(boundaries.get("devnetAllowed") is True, "boundaries.devnetAllowed", "Devnet must be allowed for this demo lane.")
    for field in [
        "mainnetAccess",
        "walletAccess",
        "paymentRailAccess",
        "facilitatorAccess",
        "settlementAccess",
        "credentialValuesEmbedded",
        "liveMcpInvocation",
        "providerProductCall",
        "packagePublished",
        "productionGatewayMutation",
    ]:
        require(boundaries.get(field) is False, f"boundaries.{field}", f"{field} must be false.")

    require(bool(env_contract), "environmentContract", "Environment contract is required.")
    for index, item in enumerate(env_contract):
        require("value" not in item, f"environmentContract[{index}].value", "Public metadata must not store env values.")
        require(not SENSITIVE_KEY.search(str(item.get("name", ""))), f"environmentContract[{index}].name", "Secret-like env names are not allowed in public metadata.")

    require(rollback.get("available") is True, "rollback.available", "Rollback must be available.")
    require(bool(rollback.get("teardownCommand")), "rollback.teardownCommand", "Teardown command metadata is required.")
    return findings


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings = collect_findings(scenario, commit)
    status = "pass" if not findings else "fail"
    inventory = []
    for path in scenario.get("requiredLocalFiles", []):
        local = ROOT / path
        inventory.append(
            {
                "path": path,
                "exists": local.exists(),
                "sha256": sha256_file(local) if local.exists() else None,
            }
        )
    return {
        "id": scenario.get("id"),
        "kind": scenario.get("kind"),
        "status": status,
        "expectedStatus": scenario.get("expectedStatus"),
        "findings": findings,
        "deployment": {
            "projectName": scenario.get("projectName"),
            "appName": scenario.get("appName"),
            "publicUrl": scenario.get("publicUrl"),
            "repo": scenario.get("repo"),
            "branch": scenario.get("branch"),
            "coolifyResourceType": scenario.get("coolifyResourceType"),
            "buildPack": scenario.get("buildPack"),
            "dockerfilePath": scenario.get("dockerfilePath"),
            "imageName": scenario.get("imageName"),
            "imageTagPolicy": scenario.get("imageTagPolicy"),
            "publishDirectory": scenario.get("publishDirectory"),
            "healthPath": scenario.get("healthPath"),
            "devnetCluster": scenario.get("devnetCluster"),
            "verifiedRoutes": scenario.get("verifiedRoutes"),
        },
        "claims": scenario.get("claims"),
        "boundaries": scenario.get("boundaries"),
        "environmentContract": scenario.get("environmentContract"),
        "rollback": scenario.get("rollback"),
        "requiredLocalFileInventory": inventory,
    }


def build_report(doc: dict[str, Any], commit: str) -> dict[str, Any]:
    results = [
        build_result(merge_scenario(doc.get("defaults", {}), scenario), commit)
        for scenario in doc.get("scenarios", [])
    ]
    mismatches = [
        finding(f"results[{index}].status", f"{result['id']} produced {result['status']} but expected {result['expectedStatus']}")
        for index, result in enumerate(results)
        if result["status"] != result["expectedStatus"]
    ]
    return {
        "mode": "coolify-devnet-public-demo-readiness",
        "issue": 280,
        "parentEpic": 220,
        "relatedEpics": [247],
        "sourceCommit": commit,
        "status": "pass" if not mismatches else "fail",
        "findings": mismatches,
        "mainnetStatement": "Mainnet remains blocked and is not enabled by this public devnet demo.",
        "summary": {
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["status"] == "fail"),
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(load_json(args.scenarios), source_commit())
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = args.output if args.output.is_absolute() else ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload)
    print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
