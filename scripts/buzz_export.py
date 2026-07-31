#!/usr/bin/env python3
"""Deterministic, local-only ADL v0.2 to Buzz static projection report."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from datetime import datetime, timezone

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "specs" / "ADL-v0.2.schema.json"
PIN_RE = re.compile(r"^[0-9a-f]{40}$")
SENSITIVE_RE = re.compile(
    r"(?i)(-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:api[_-]?key|secret|password|"
    r"private[_-]?key|seed[_-]?phrase)\s*[:=]\s*[^\s]+|sk-[a-z0-9_-]{12,})"
)
BOUNDARY_FLAGS = {
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "relayAccess": False,
    "providerAccess": False,
    "credentialAccess": False,
    "toolExecutionAllowed": False,
    "mcpInvocation": False,
    "walletAccess": False,
    "paymentAccess": False,
    "deploymentAllowed": False,
    "bidirectionalImportAllowed": False,
    "publicDistributionAllowed": False,
    "publicBrandingAllowed": False,
}
CLASSIFICATIONS = {
    "apiVersion": "direct", "kind": "direct", "metadata.name": "direct",
    "metadata.description": "direct", "conformance": "metadata-only",
    "model.capability": "lossy", "model.providers": "metadata-only",
    "model.requirements": "metadata-only", "model.cost": "metadata-only",
    "harness.instructions.inline": "lossy", "harness.instructions.path": "lossy",
    "harness.tools": "metadata-only", "harness.functions": "metadata-only",
    "harness.skills": "lossy", "harness.dataSources": "metadata-only",
    "harness.memory": "unsupported", "harness.policies": "metadata-only",
    "harness.evalGates": "metadata-only", "harness.runtime": "unsupported",
    "harness.deployment": "unsupported", "harness.observability": "metadata-only",
    "harness.recovery": "metadata-only", "extensions.identity": "direct",
    "extensions.x402": "metadata-only", "extensions.receipts": "metadata-only",
    "extensions.reputation": "metadata-only",
}
SEVERITY_RANK = {"error": 0, "warning": 1, "info": 2}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def diagnostic(code: str, classification: str, path: str, message: str,
               remediation: str, blocking: bool = True) -> dict:
    severity = "error" if blocking else "warning"
    return {"code": code, "classification": classification, "severity": severity,
            "path": path, "message": message, "remediation": remediation,
            "blocking": blocking}


def _sort_diagnostics(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda x: (x["path"].encode(), SEVERITY_RANK[x["severity"]], x["code"]))


def _present(doc: dict, path: str) -> bool:
    value: object = doc
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return False
        value = value[part]
    return value is not None


def _schema_diagnostics(doc: object, schema: dict) -> list[dict]:
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.path))
    return [diagnostic("BUZZ_ADL_INVALID", "refused",
                       ".".join(map(str, e.path)) or "<root>", e.message,
                       "Correct the canonical ADL v0.2 source.") for e in errors]


def _identity_diagnostics(binding: dict, adl_digest: str, evaluation_time: str | None) -> list[dict]:
    required = {"canonicalAgentId", "adlDigest", "buzzAgentKey", "ownerKey",
                "bindingDigest", "status", "verified"}
    valid = required <= set(binding) and binding.get("adlDigest") == adl_digest
    valid = valid and binding.get("verified") is True and binding.get("status") in {"bound", "active"}
    if binding.get("expiresAt"):
        try:
            expires = datetime.fromisoformat(binding["expiresAt"].replace("Z", "+00:00"))
            if evaluation_time is None:
                valid = False
            else:
                evaluated = datetime.fromisoformat(evaluation_time.replace("Z", "+00:00"))
                valid = valid and expires > evaluated
        except (TypeError, ValueError):
            valid = False
    if valid:
        return []
    return [diagnostic("BUZZ_IDENTITY_BINDING_INVALID", "refused", "identityBinding",
                       "Identity binding is incomplete, unverified, mismatched, stale, expired, or revoked.",
                       "Supply reviewed binding evidence for these exact source bytes.")]


def build_report(source: Path, canonical_uri: str, schema_path: Path, pins: dict,
                 binding: dict, generated_at: str | None = None,
                 request_distribution: bool = False) -> tuple[dict, dict | None]:
    source = source.resolve()
    schema_path = schema_path.resolve()
    source_bytes = source.read_bytes()
    schema_bytes = schema_path.read_bytes()
    diagnostics: list[dict] = []
    try:
        doc = yaml.safe_load(source_bytes)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        doc = {}
        diagnostics.append(diagnostic("BUZZ_ADL_INVALID", "refused", "<root>", str(exc),
                                      "Provide UTF-8 YAML matching ADL v0.2."))
    schema = json.loads(schema_bytes)
    diagnostics.extend(_schema_diagnostics(doc, schema))
    adl_digest = sha256(source_bytes)
    if not canonical_uri or (canonical_uri.startswith("repo:") and not pins.get("sourceCommit")):
        diagnostics.append(diagnostic("BUZZ_CANONICAL_REF_MISSING", "refused", "canonicalAdl.uri",
                                      "Canonical URI or repository source commit is missing.",
                                      "Supply the immutable canonical reference."))
    for name in ("upstreamCommit", "forkCommit", "adapterCommit"):
        if not PIN_RE.fullmatch(str(pins.get(name, ""))):
            diagnostics.append(diagnostic("BUZZ_TARGET_PIN_INVALID", "refused", f"target.{name}",
                                          "Target commit must be full lowercase 40-hex.",
                                          "Supply an owner-reviewed immutable commit."))
    diagnostics.extend(_identity_diagnostics(binding, adl_digest, generated_at))
    if request_distribution:
        diagnostics.append(diagnostic("BUZZ_ATTRIBUTION_REVIEW_REQUIRED", "refused", "distribution",
                                      "Public distribution and branding review is incomplete.",
                                      "Complete LICENSE/NOTICE/modified-file and downstream branding review."))
    if SENSITIVE_RE.search(source_bytes.decode("utf-8", errors="ignore")):
        diagnostics.append(diagnostic("BUZZ_PUBLIC_SENSITIVE_CONTENT", "refused", "<source>",
                                      "Source contains public-sensitive or secret-like content.",
                                      "Remove private material; redaction is not performed by this exporter."))
    harness = doc.get("harness", {}) if isinstance(doc, dict) else {}
    instructions = harness.get("instructions", {}) or {}
    instruction_text = instructions.get("inline")
    instruction_asset = None
    if "path" in instructions:
        rel = Path(instructions.get("path") or "")
        candidate = source.parent / rel
        try:
            resolved = candidate.resolve(strict=True)
            if rel.is_absolute() or source.parent.resolve() not in resolved.parents or candidate.is_symlink() or not resolved.is_file():
                raise OSError("unsafe instruction path")
            asset_bytes = resolved.read_bytes()
            instruction_text = asset_bytes.decode("utf-8")
            instruction_asset = {"path": rel.as_posix(), "sha256": sha256(asset_bytes), "bytes": len(asset_bytes)}
            if SENSITIVE_RE.search(instruction_text):
                raise ValueError("sensitive instruction content")
        except FileNotFoundError:
            diagnostics.append(diagnostic("BUZZ_INSTRUCTION_FILE_UNAVAILABLE", "refused", "harness.instructions.path",
                                          "Instruction file is unavailable.", "Provide a reviewed in-root regular file."))
        except (OSError, UnicodeDecodeError, ValueError):
            diagnostics.append(diagnostic("BUZZ_PUBLIC_SENSITIVE_CONTENT", "refused", "harness.instructions.path",
                                          "Instruction path or content is unsafe for public projection.",
                                          "Use a reviewed UTF-8 in-root regular file."))
    if harness.get("memory"):
        diagnostics.append(diagnostic("BUZZ_SURFACE_UNSUPPORTED", "unsupported", "harness.memory",
                                      "Memory contents and retention cannot be projected.",
                                      "Keep memory outside the Buzz package."))
    runtime = harness.get("runtime", {}) or {}
    if (runtime.get("activation") or {}).get("mode") not in {None, "blocked"} or (runtime.get("network") or {}).get("access") not in {None, "none"}:
        diagnostics.append(diagnostic("BUZZ_RUNTIME_CAPABILITY_REFUSED", "refused", "harness.runtime",
                                      "Runtime activation or network authority was requested.",
                                      "Use blocked activation and network access none."))
    extensions = doc.get("extensions", {}) if isinstance(doc, dict) else {}
    if extensions.get("x402"):
        diagnostics.append(diagnostic("BUZZ_PAYMENT_AUTHORITY_REFUSED", "refused", "extensions.x402",
                                      "Payment semantics cannot enter a static Buzz package.",
                                      "Keep payment authority in RAP; Buzz payment mode is none."))
    surfaces = []
    for path, classification in CLASSIFICATIONS.items():
        if _present(doc, path):
            blocking = classification == "unsupported" and path != "harness.runtime"
            surfaces.append({"path": path, "classification": classification,
                             "projectionRule": "review-metadata" if classification == "metadata-only" else "static-projection",
                             "diagnostics": [], "blocking": blocking})
    for key in sorted((extensions or {}), key=lambda x: x.encode()):
        path = f"extensions.{key}"
        if path not in CLASSIFICATIONS:
            surfaces.append({"path": path, "classification": "metadata-only",
                             "projectionRule": "namespaced-review-metadata", "diagnostics": [], "blocking": False})
    diagnostics = _sort_diagnostics(diagnostics)
    eligible = not any(d["blocking"] for d in diagnostics) and not any(r["blocking"] for r in surfaces)
    report = {
        "format": "reddiagent-buzz-compatibility-report", "version": "0.1",
        "canonicalAdl": {"uri": canonical_uri, "apiVersion": doc.get("apiVersion") if isinstance(doc, dict) else None,
                         "digest": adl_digest, "schemaDigest": sha256(schema_bytes),
                         **({"sourceCommit": pins["sourceCommit"]} if pins.get("sourceCommit") else {})},
        "target": {"kind": "buzz-static-projection", "upstreamCommit": pins.get("upstreamCommit"),
                   "forkCommit": pins.get("forkCommit"), "adapterCommit": pins.get("adapterCommit"),
                   "contractVersion": "0.1", **({"generatedAt": generated_at} if generated_at else {})},
        "identityBinding": binding, "surfaceRows": surfaces, "diagnostics": diagnostics,
        "packageEligible": eligible, "canonical": False, "oneWayProjection": True,
        "canonicalSourceRequiredForRegeneration": True, "paymentMode": "none", **BOUNDARY_FLAGS,
    }
    projection = None
    if eligible:
        projection = {"format": "reddiagent-buzz-static-persona", "version": "0.1",
                      "name": doc["metadata"]["name"], "description": doc["metadata"]["description"],
                      "instructions": instruction_text, "instructionAsset": instruction_asset,
                      "model": {"capability": doc["model"]["capability"], "providers": doc["model"]["providers"]},
                      "source": report["canonicalAdl"], "lossReport": surfaces,
                      "canonical": False, "oneWayProjection": True, "paymentMode": "none", **BOUNDARY_FLAGS}
    return report, projection


def write_package(destination: Path, report: dict, projection: dict) -> None:
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError("export destination must be absent or empty")
    parent = destination.parent.resolve()
    tmp = parent / f".{destination.name}.buzz-export-tmp"
    if tmp.exists():
        raise ValueError("temporary export path already exists")
    destination_existed = destination.exists()
    if destination_existed:
        destination.rmdir()
    try:
        tmp.mkdir(parents=False)
        report_bytes = canonical_bytes(report) + b"\n"
        persona_bytes = canonical_bytes(projection) + b"\n"
        (tmp / "compatibility-report.json").write_bytes(report_bytes)
        (tmp / "persona.json").write_bytes(persona_bytes)
        files = [{"path": "compatibility-report.json", "sha256": sha256(report_bytes), "bytes": len(report_bytes), "mediaType": "application/json"},
                 {"path": "persona.json", "sha256": sha256(persona_bytes), "bytes": len(persona_bytes), "mediaType": "application/json"}]
        manifest = {"format": "reddiagent-buzz-artifact-manifest", "version": "0.1",
                    "files": files, "reportDigest": sha256(report_bytes), "canonical": False,
                    "oneWayProjection": True, "canonicalSourceRequiredForRegeneration": True,
                    "paymentMode": "none", **BOUNDARY_FLAGS}
        (tmp / "manifest.json").write_bytes(canonical_bytes(manifest) + b"\n")
        os.replace(tmp, destination)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        if destination_existed and not destination.exists():
            destination.mkdir()
        raise


def parity_summary(doc: dict, errors: list[str]) -> dict:
    blockers = ["BUZZ_ADL_INVALID"] if errors else []
    harness = doc.get("harness", {}) or {}
    if harness.get("memory"):
        blockers.append("BUZZ_SURFACE_UNSUPPORTED")
    if (doc.get("extensions") or {}).get("x402"):
        blockers.append("BUZZ_PAYMENT_AUTHORITY_REFUSED")
    return {"status": "blocked" if blockers else "report-ready",
            "readiness": "blocked-by-validation" if errors else ("refused" if blockers else "report-ready"),
            "blockedBy": sorted(set(blockers)), "metadataOnlySections": [],
            "metadataOnlyExtensions": [], "packageEligible": not blockers,
            "diagnostics": sorted(set(blockers)), **BOUNDARY_FLAGS}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--single", required=True, type=Path)
    p.add_argument("--canonical-uri", required=True)
    p.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    p.add_argument("--source-commit")
    p.add_argument("--upstream-commit", required=True)
    p.add_argument("--fork-commit", required=True)
    p.add_argument("--adapter-commit", required=True)
    p.add_argument("--identity-binding", required=True, type=Path)
    p.add_argument("--generated-at")
    p.add_argument("--export-package", type=Path)
    p.add_argument("--request-distribution", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.generated_at:
        try:
            parsed = datetime.fromisoformat(args.generated_at.replace("Z", "+00:00"))
            if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
                raise ValueError
        except ValueError:
            print("error: generated-at must be pinned RFC 3339 UTC", file=sys.stderr)
            return 2
    binding = json.loads(args.identity_binding.read_text())
    pins = {"sourceCommit": args.source_commit, "upstreamCommit": args.upstream_commit,
            "forkCommit": args.fork_commit, "adapterCommit": args.adapter_commit}
    report, projection = build_report(args.single, args.canonical_uri, args.schema, pins,
                                      binding, args.generated_at, args.request_distribution)
    sys.stdout.buffer.write(canonical_bytes(report) + b"\n")
    if not report["packageEligible"]:
        return 3
    if args.export_package:
        try:
            write_package(args.export_package, report, projection)
        except (OSError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
