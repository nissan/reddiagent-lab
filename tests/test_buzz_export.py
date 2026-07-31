#!/usr/bin/env python3
"""Focused deterministic Buzz static exporter checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SOURCE = ROOT / "tests" / "fixtures" / "buzz-valid-static-agent.yaml"
ATTRIBUTION = ROOT / "tests" / "fixtures" / "buzz-attribution-distribution-request.json"
COMPOUND = ROOT / "tests" / "fixtures" / "buzz-compound-refusal-agent.yaml"
STALE_DRIFT = ROOT / "tests" / "fixtures" / "buzz-upstream-drift-unreviewed.json"
MALFORMED_GOVERNANCE = ROOT / "tests" / "fixtures" / "buzz-malformed-governance-cases.json"
LIFECYCLE_RELATIONSHIPS = ROOT / "tests" / "fixtures" / "buzz-lifecycle-relationship-cases.json"
SCHEMA = ROOT / "specs" / "ADL-v0.2.schema.json"
PIN = "a" * 40
EVALUATION_TIME = "2026-07-31T01:00:00Z"
SEED = bytes.fromhex("1f" * 32)
Q = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493
D = (-121665 * pow(121666, Q - 2, Q)) % Q
I = pow(2, (Q - 1) // 4, Q)


def xrecover(y: int) -> int:
    xx = (y * y - 1) * pow(D * y * y + 1, Q - 2, Q) % Q
    x = pow(xx, (Q + 3) // 8, Q)
    if (x * x - xx) % Q:
        x = x * I % Q
    return Q - x if x & 1 else x


B = (xrecover(4 * pow(5, Q - 2, Q) % Q), 4 * pow(5, Q - 2, Q) % Q)


def add(p: tuple[int, int], q: tuple[int, int]) -> tuple[int, int]:
    x1, y1 = p
    x2, y2 = q
    factor = D * x1 * x2 * y1 * y2 % Q
    return ((x1 * y2 + x2 * y1) * pow(1 + factor, Q - 2, Q) % Q,
            (y1 * y2 + x1 * x2) * pow(1 - factor, Q - 2, Q) % Q)


def mult(p: tuple[int, int], scalar: int) -> tuple[int, int]:
    result = (0, 1)
    while scalar:
        if scalar & 1:
            result = add(result, p)
        p = add(p, p)
        scalar >>= 1
    return result


def encode(p: tuple[int, int]) -> bytes:
    x, y = p
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def key_material() -> tuple[str, int, bytes]:
    digest = hashlib.sha512(SEED).digest()
    scalar_bytes = bytearray(digest[:32])
    scalar_bytes[0] &= 248
    scalar_bytes[31] &= 63
    scalar_bytes[31] |= 64
    scalar = int.from_bytes(scalar_bytes, "little")
    public = encode(mult(B, scalar))
    return public.hex(), scalar, digest[32:]


def sign(message: bytes) -> str:
    public_hex, scalar, prefix = key_material()
    public = bytes.fromhex(public_hex)
    nonce = int.from_bytes(hashlib.sha512(prefix + message).digest(), "little") % L
    encoded_r = encode(mult(B, nonce))
    challenge = int.from_bytes(hashlib.sha512(encoded_r + public + message).digest(), "little") % L
    encoded_s = ((nonce + challenge * scalar) % L).to_bytes(32, "little")
    return (encoded_r + encoded_s).hex()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def preimage(domain: str, value: dict) -> bytes:
    return domain.encode() + b"\x00" + canonical(value)


def signed_lifecycle_record(owner: str, binding_digest: str, *, action: str,
                            sequence: int, previous: str | None,
                            replacement: str | None,
                            effective_at: str = "2026-07-31T00:00:00Z") -> dict:
    record = {"recordVersion": 1, "recordSequence": sequence, "actorKeyId": owner,
              "actorPubkey": owner, "signatureAlgorithm": "ed25519", "action": action,
              "bindingDigest": binding_digest, "previousBindingDigest": previous,
              "replacementBindingDigest": replacement, "effectiveAt": effective_at,
              "reasonCode": "OWNER_REVIEWED", "reason": "Owner-reviewed static export fixture."}
    domain = ("reddiagent-buzz-identity-revocation-v1" if action == "revoked"
              else "reddiagent-buzz-identity-transition-v1")
    record_message = preimage(domain, record)
    record["signatureBytes"] = sign(record_message)
    record["evidenceDigest"] = hashlib.sha256(
        record_message + b"\x00" + bytes.fromhex(record["signatureBytes"])
    ).hexdigest()
    return record


def canonical_uri(path: Path) -> str:
    if path.resolve() == SOURCE.resolve():
        return "repo:tests/fixtures/buzz-valid-static-agent.yaml"
    return f"urn:reddiagent:test:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def binding(path: Path, *, sequence: int = 1, previous_binding_digest: str | None = None,
            record_previous: str | None = None,
            record_replacement: str | None = None,
            related_bindings: list[dict] | None = None,
            record_effective_at: str = "2026-07-31T00:00:00Z") -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    owner, _, _ = key_material()
    value = {
        "canonicalAgentId": "reddiagent:buzz-static-review-agent",
        "canonicalAdlUri": canonical_uri(path),
        "canonicalAdlDigest": digest,
        "canonicalAdlVersion": "reddiagent.dev/v0.2",
        "buzzAgentPubkey": "c" * 64,
        "ownerPubkey": owner,
        "ownerAttestationRef": "nip-oa:reviewed-fixture",
        "issuedAt": "2026-07-30T00:00:00Z",
        "notBefore": "2026-07-30T00:00:00Z",
        "expiresAt": "2026-08-31T00:00:00Z",
        "sequence": sequence,
        "previousBindingDigest": previous_binding_digest,
        "emergencyRevocationAuthorities": [],
    }
    immutable = {key: value[key] for key in (
        "canonicalAgentId", "canonicalAdlUri", "canonicalAdlDigest",
        "canonicalAdlVersion", "buzzAgentPubkey", "ownerPubkey", "issuedAt",
        "notBefore", "expiresAt", "sequence", "previousBindingDigest",
        "emergencyRevocationAuthorities",
    )}
    binding_digest = hashlib.sha256(preimage("reddiagent-buzz-identity-binding-v1", immutable)).hexdigest()
    proof = {"proofVersion": 1, "canonicalizationVersion": "RFC8785",
             "signatureAlgorithm": "ed25519", "signerKeyId": owner}
    proof_message = preimage("reddiagent-buzz-owner-binding-proof-v1",
                             {**proof, "bindingDigest": binding_digest})
    proof["signatureBytes"] = sign(proof_message)
    record = signed_lifecycle_record(
        owner, binding_digest, action="active", sequence=1,
        previous=record_previous, replacement=record_replacement,
        effective_at=record_effective_at,
    )
    return {**value, "ownerBindingProof": proof, "status": "active",
            "lifecycleEvidence": [record], "bindingDigest": binding_digest,
            "relatedBindings": related_bindings or []}


def related_evidence(value: dict) -> dict:
    return {key: item for key, item in value.items()
            if key not in {"ownerAttestationRef", "status", "relatedBindings"}}


def drift() -> dict:
    return {
        "reviewVersion": 1, "reviewer": "fixture-owner", "reviewedAt": "2026-07-31T00:30:00Z",
        "pins": {"mergeBase": PIN, "upstreamCommit": PIN, "forkCommit": PIN, "adapterCommit": PIN},
        "upstreamDrift": {"commitsChanged": [], "relevantPaths": [], "linkedUpstreamIssues": [],
                          "classificationChanges": [], "negativeClaimsReverified": True,
                          "relevantDrift": False, "decision": "hold-no-drift"},
        "adapterDecision": {"chosenLayer": "external-adapter", "rejectedHigherLayers": [],
                            "affectedPaths": ["scripts/buzz_export.py"], "apiSurfaces": ["static-json"],
                            "forkDeltaCount": 0, "upstreamCandidate": None,
                            "maintenanceOwner": "reddinft", "removalTrigger": "adapter-contract-retired"},
        "reviewedExtensions": [],
        "attribution": {
            "upstreamRepository": {"url": "https://github.com/block/buzz", "commit": PIN},
            "downstreamRepository": {"url": "https://github.com/reddinft/buzz", "commit": PIN},
            "license": {"spdx": "Apache-2.0", "textIncluded": False, "status": "reviewed-hold"},
            "notice": {"present": False, "digest": None, "status": "reviewed-absent-at-pin"},
            "copyrightNotices": {"status": "reviewed-hold"},
            "modifiedFiles": {"files": [], "notices": [], "status": "not-applicable"},
            "distributionForms": {"source": "hold", "object": "hold"},
            "thirdPartyInventory": {"status": "pending-review"},
            "downstreamName": "pending-review", "publicDisclaimer": "pending-review",
            "trademarkReview": {"reviewer": None, "date": None, "scope": "downstream-name",
                                "decision": "pending-review"},
            "publicDistributionAllowed": False, "publicBrandingAllowed": False,
        },
    }


def command(source: Path, binding_path: Path, drift_path: Path, *extra: str) -> list[str]:
    return [PYTHON, "scripts/buzz_export.py", "--single", str(source),
            "--canonical-uri", canonical_uri(source),
            "--schema", str(SCHEMA), "--source-commit", PIN,
            "--upstream-commit", PIN, "--fork-commit", PIN,
            "--adapter-commit", PIN, "--identity-binding", str(binding_path),
            "--drift-review", str(drift_path), "--evaluation-time", EVALUATION_TIME, *extra]


def assert_boundaries(item: dict) -> None:
    for key in ("runtimeExecutionAllowed", "networkAccess", "relayAccess",
                "providerAccess", "credentialAccess", "toolExecutionAllowed",
                "mcpInvocation", "walletAccess", "paymentAccess",
                "deploymentAllowed", "bidirectionalImportAllowed",
                "publicDistributionAllowed", "publicBrandingAllowed"):
        assert item[key] is False, key


def main() -> int:
    sys.path.insert(0, str(ROOT / "scripts"))
    from buzz_export import BOUNDARY_FLAGS as EXPORTER_BOUNDARIES, _ed_verify, build_report, canonical_bytes
    from prosumer_builder_plan import BOUNDARY_FLAGS as CANONICAL_BOUNDARIES

    assert EXPORTER_BOUNDARIES is CANONICAL_BOUNDARIES
    jcs_vector = canonical_bytes({"z": 1e30, "a": 1e-7, "b": 1e-6, "c": 1e20, "d": -0.0,
                                  "\ue000": "bmp", "\U0001f600": "astral"})
    assert jcs_vector == (
        '{"a":1e-7,"b":0.000001,"c":100000000000000000000,"d":0,"z":1e+30,'
        '"\U0001f600":"astral","\ue000":"bmp"}'.encode()
    )
    assert canonical_bytes([333333333.33333329, 1e30, 4.5, 2e-3, 1e-27]) == (
        b"[333333333.3333333,1e+30,4.5,0.002,1e-27]"
    )
    if shutil.which("node"):
        node_vector = subprocess.run(
            ["node", "-e", "process.stdout.write(JSON.stringify({a:1e-7,b:1e-6,c:1e20,d:-0,z:1e30,'😀':'astral','':'bmp'}))"],
            capture_output=True, check=True,
        ).stdout
        assert jcs_vector == node_vector
    for invalid in (float("nan"), float("inf"), float("-inf")):
        try:
            canonical_bytes({"invalid": invalid})
            raise AssertionError("non-finite RFC 8785 input was accepted")
        except ValueError:
            pass

    assert _ed_verify(
        "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
        "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b",
        b"",
    )
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        binding_path = temp / "binding.json"
        drift_path = temp / "drift.json"
        binding_path.write_text(json.dumps(binding(SOURCE)))
        drift_path.write_text(json.dumps(drift()))
        first = subprocess.run(command(SOURCE, binding_path, drift_path), cwd=ROOT, capture_output=True, check=True)
        second = subprocess.run(command(SOURCE, binding_path, drift_path), cwd=ROOT, capture_output=True, check=True)
        assert first.stdout == second.stdout
        report = json.loads(first.stdout)
        assert report["packageEligible"] is True
        assert report["canonicalAdl"]["digest"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        assert report["canonical"] is False and report["oneWayProjection"] is True
        assert report["paymentMode"] == "none"
        assert report["target"]["evaluationTime"] == EVALUATION_TIME
        assert "generatedAt" not in report["target"]
        assert set(report["identityBinding"]) == {
            "bindingDigest", "status", "sequence", "expiresAt", "proofAlgorithm", "verified"
        }
        assert set(report["target"]["governanceReview"]) == {
            "reviewVersion", "reviewedAt", "pins", "upstreamDrift",
            "adapterDecision", "reviewedExtensions", "attributionManifest",
            "publicDistributionAllowed", "publicBrandingAllowed"
        }
        assert report["target"]["governanceReview"]["pins"] == drift()["pins"]
        assert report["target"]["governanceReview"]["upstreamDrift"] == drift()["upstreamDrift"]
        assert report["target"]["governanceReview"]["adapterDecision"] == drift()["adapterDecision"]
        attribution_evidence = report["target"]["governanceReview"]["attributionManifest"]
        assert attribution_evidence == drift()["attribution"]
        assert_boundaries(report)
        diagnostic_by_path = {
            (item["path"], item["code"]): item for item in report["diagnostics"]
        }
        expected_non_blocking = {
            "lossy": "BUZZ_SEMANTIC_LOSS",
            "metadata-only": "BUZZ_METADATA_NOT_ENFORCED",
        }
        for row in report["surfaceRows"]:
            code = expected_non_blocking.get(row["classification"])
            if code is None:
                continue
            assert code in row["diagnostics"], row["path"]
            item = diagnostic_by_path[(row["path"], code)]
            assert item["classification"] == row["classification"]
            assert item["severity"] == "warning"
            assert item["blocking"] is False
        assert {
            (item["path"], item["code"])
            for item in report["diagnostics"]
            if item["code"] in expected_non_blocking.values()
        } == {
            (row["path"], expected_non_blocking[row["classification"]])
            for row in report["surfaceRows"]
            if row["classification"] in expected_non_blocking
        }
        assert {
            (item["path"], item["code"])
            for item in report["diagnostics"]
            if item["code"] in expected_non_blocking.values()
        } == {
            ("harness.instructions.inline", "BUZZ_SEMANTIC_LOSS"),
            ("model.capability", "BUZZ_SEMANTIC_LOSS"),
            ("model.providers", "BUZZ_METADATA_NOT_ENFORCED"),
            ("model.requirements", "BUZZ_METADATA_NOT_ENFORCED"),
        }

        predecessor = binding(SOURCE)
        rotated = binding(
            SOURCE, sequence=2, previous_binding_digest=predecessor["bindingDigest"],
            record_previous=predecessor["bindingDigest"],
            related_bindings=[related_evidence(predecessor)],
        )
        binding_path.write_text(json.dumps(rotated))
        rotated_proc = subprocess.run(command(SOURCE, binding_path, drift_path), cwd=ROOT,
                                      capture_output=True, check=True)
        assert json.loads(rotated_proc.stdout)["packageEligible"] is True

        def assert_related_refused(candidate: dict, name: str) -> None:
            binding_path.write_text(json.dumps(candidate))
            proc = subprocess.run(command(SOURCE, binding_path, drift_path), cwd=ROOT,
                                  text=True, capture_output=True)
            assert proc.returncode == 3, name
            assert "BUZZ_IDENTITY_BINDING_INVALID" in {
                item["code"] for item in json.loads(proc.stdout)["diagnostics"]
            }, name

        missing_activation = related_evidence(predecessor)
        missing_activation["lifecycleEvidence"] = []
        assert_related_refused(binding(
            SOURCE, sequence=2, previous_binding_digest=predecessor["bindingDigest"],
            record_previous=predecessor["bindingDigest"],
            related_bindings=[missing_activation],
        ), "related-predecessor-missing-activation")
        assert_related_refused(binding(
            SOURCE, sequence=3, previous_binding_digest=predecessor["bindingDigest"],
            record_previous=predecessor["bindingDigest"],
            related_bindings=[related_evidence(predecessor)],
        ), "related-predecessor-non-adjacent-sequence")

        current = binding(SOURCE)
        broken_replacement = binding(
            SOURCE, sequence=2, previous_binding_digest="b" * 64,
            record_previous="b" * 64, record_effective_at="2026-08-02T00:00:00Z",
        )
        current["lifecycleEvidence"].append(signed_lifecycle_record(
            current["ownerPubkey"], current["bindingDigest"], action="rotating", sequence=2,
            previous=current["bindingDigest"], replacement=broken_replacement["bindingDigest"],
            effective_at="2026-08-01T00:00:00Z",
        ))
        current["relatedBindings"] = [related_evidence(broken_replacement)]
        assert_related_refused(current, "related-replacement-broken-link")

        current = binding(SOURCE)
        early_replacement = binding(
            SOURCE, sequence=2, previous_binding_digest=current["bindingDigest"],
            record_previous=current["bindingDigest"], record_effective_at="2026-07-31T00:00:00Z",
        )
        current["lifecycleEvidence"].append(signed_lifecycle_record(
            current["ownerPubkey"], current["bindingDigest"], action="rotating", sequence=2,
            previous=current["bindingDigest"], replacement=early_replacement["bindingDigest"],
            effective_at="2026-08-01T00:00:00Z",
        ))
        current["relatedBindings"] = [related_evidence(early_replacement)]
        assert_related_refused(current, "related-replacement-activation-before-rotation")

        current = binding(SOURCE)
        future_replacement = binding(
            SOURCE, sequence=2, previous_binding_digest=current["bindingDigest"],
            record_previous=current["bindingDigest"], record_effective_at="2026-08-02T00:00:00Z",
        )
        current["lifecycleEvidence"].append(signed_lifecycle_record(
            current["ownerPubkey"], current["bindingDigest"], action="rotating", sequence=2,
            previous=current["bindingDigest"], replacement=future_replacement["bindingDigest"],
            effective_at="2026-08-01T00:00:00Z",
        ))
        current["relatedBindings"] = [related_evidence(future_replacement)]
        binding_path.write_text(json.dumps(current))
        future_rotation = subprocess.run(command(SOURCE, binding_path, drift_path), cwd=ROOT,
                                         capture_output=True, check=True)
        assert json.loads(future_rotation.stdout)["packageEligible"] is True
        binding_path.write_text(json.dumps(binding(SOURCE)))

        secret = "sk-supersecretmaterial123456"
        sensitive_evidence = binding(SOURCE)
        sensitive_evidence["ownerAttestationRef"] = secret
        sensitive_governance = drift()
        sensitive_governance["reviewer"] = secret
        binding_path.write_text(json.dumps(sensitive_evidence))
        drift_path.write_text(json.dumps(sensitive_governance))
        non_echo = subprocess.run(command(SOURCE, binding_path, drift_path), cwd=ROOT,
                                  capture_output=True, check=True)
        assert secret.encode() not in non_echo.stdout
        binding_path.write_text(json.dumps(binding(SOURCE)))
        drift_path.write_text(json.dumps(drift()))

        unsafe_report, unsafe_projection = build_report(
            SOURCE, canonical_uri(SOURCE), SCHEMA,
            {"sourceCommit": PIN, "upstreamCommit": PIN, "forkCommit": PIN,
             "adapterCommit": secret},
            binding(SOURCE), drift(), EVALUATION_TIME,
        )
        assert unsafe_projection is None and unsafe_report["packageEligible"] is False
        assert secret not in canonical_bytes(unsafe_report).decode()
        assert "BUZZ_PUBLIC_SENSITIVE_CONTENT" in {
            item["code"] for item in unsafe_report["diagnostics"]
        }

        unknown = temp / "unknown-extension.yaml"
        unknown.write_text(SOURCE.read_text().replace(
            "extensions: {}", "extensions:\n  x-unreviewed:\n    nested:\n      command: run-now\n"
            "      wallet: delegated\n      credential: private-value\n"
            "      claim: Buzz is authoritative for accepted payment reputation\n"
        ))
        binding_path.write_text(json.dumps(binding(unknown)))
        unknown_proc = subprocess.run(command(unknown, binding_path, drift_path), cwd=ROOT,
                                      text=True, capture_output=True)
        assert unknown_proc.returncode == 3
        unknown_codes = {item["code"] for item in json.loads(unknown_proc.stdout)["diagnostics"]}
        assert {"BUZZ_SURFACE_UNSUPPORTED", "BUZZ_RUNTIME_CAPABILITY_REFUSED",
                "BUZZ_PAYMENT_AUTHORITY_REFUSED", "BUZZ_PUBLIC_SENSITIVE_CONTENT",
                "BUZZ_AUTHORITY_CLAIM_REFUSED"} <= unknown_codes
        binding_path.write_text(json.dumps(binding(SOURCE)))

        round_trip_report, round_trip_projection = build_report(
            SOURCE, canonical_uri(SOURCE), SCHEMA,
            {"sourceCommit": PIN, "upstreamCommit": PIN, "forkCommit": PIN,
             "adapterCommit": PIN},
            binding(SOURCE), drift(), EVALUATION_TIME, request_round_trip=True,
        )
        assert round_trip_projection is None
        assert "BUZZ_ONE_WAY_ONLY" in [d["code"] for d in round_trip_report["diagnostics"]]

        one = temp / "package-one"
        two = temp / "package-two"
        for dest in (one, two):
            proc = subprocess.run(command(SOURCE, binding_path, drift_path, "--export-package", str(dest)), cwd=ROOT,
                                  capture_output=True, check=True)
            assert proc.stdout == first.stdout
            assert sorted(p.name for p in dest.iterdir()) == ["compatibility-report.json", "manifest.json", "persona.json"]
            manifest = json.loads((dest / "manifest.json").read_text())
            assert_boundaries(manifest)
            assert manifest["governanceEvidence"] == report["target"]["governanceReview"]
            assert manifest["governanceEvidence"]["attributionManifest"] == drift()["attribution"]
            assert_boundaries(json.loads((dest / "persona.json").read_text()))
        assert {p.name: p.read_bytes() for p in one.iterdir()} == {p.name: p.read_bytes() for p in two.iterdir()}

        refused = temp / "distribution-refused"
        attribution_request = json.loads(ATTRIBUTION.read_text())
        assert attribution_request["requestDistribution"] is True
        assert attribution_request["publicDistributionAllowed"] is False
        assert attribution_request["publicBrandingAllowed"] is False
        proc = subprocess.run(command(SOURCE, binding_path, drift_path, "--request-distribution", "--export-package", str(refused)),
                              cwd=ROOT, text=True, capture_output=True)
        assert proc.returncode == 3
        refusal = json.loads(proc.stdout)
        assert "BUZZ_ATTRIBUTION_REVIEW_REQUIRED" in [d["code"] for d in refusal["diagnostics"]]
        assert not refused.exists()
        assert not list(temp.glob(".*.buzz-export-tmp"))

        tampered_binding = binding(SOURCE)
        tampered_binding["canonicalAdlDigest"] = "0" * 64
        binding_path.write_text(json.dumps(tampered_binding))
        proc = subprocess.run(command(SOURCE, binding_path, drift_path), cwd=ROOT, text=True, capture_output=True)
        assert proc.returncode == 3
        assert "BUZZ_IDENTITY_BINDING_INVALID" in [d["code"] for d in json.loads(proc.stdout)["diagnostics"]]

        for case in json.loads(LIFECYCLE_RELATIONSHIPS.read_text()):
            relationship_binding = binding(
                SOURCE,
                sequence=case["bindingSequence"],
                previous_binding_digest=case["bindingPredecessor"],
                record_previous=(case["recordPredecessor"] if case["action"] == "active" else
                                 case["bindingPredecessor"]),
            )
            if case["action"] != "active":
                owner = relationship_binding["ownerPubkey"]
                current_digest = relationship_binding["bindingDigest"]
                previous = (current_digest if case["recordPredecessor"] == "CURRENT_BINDING" else
                            case["recordPredecessor"])
                replacement = (current_digest if case["recordReplacement"] == "CURRENT_BINDING" else
                               case["recordReplacement"])
                relationship_binding["lifecycleEvidence"].append(signed_lifecycle_record(
                    owner, current_digest, action=case["action"], sequence=2,
                    previous=previous, replacement=replacement,
                    effective_at="2026-08-01T00:00:00Z",
                ))
            else:
                relationship_binding = binding(
                    SOURCE,
                    sequence=case["bindingSequence"],
                    previous_binding_digest=case["bindingPredecessor"],
                    record_previous=case["recordPredecessor"],
                    record_replacement=case["recordReplacement"],
                )
            binding_path.write_text(json.dumps(relationship_binding))
            proc = subprocess.run(command(SOURCE, binding_path, drift_path), cwd=ROOT,
                                  text=True, capture_output=True)
            assert proc.returncode == 3, case["name"]
            assert "BUZZ_IDENTITY_BINDING_INVALID" in {
                item["code"] for item in json.loads(proc.stdout)["diagnostics"]
            }, case["name"]

        binding_path.write_text(json.dumps(binding(SOURCE)))
        for case in json.loads(MALFORMED_GOVERNANCE.read_text()):
            malformed = json.loads(json.dumps(drift()))
            target = malformed
            for key in case["path"][:-1]:
                target = target[key]
            target[case["path"][-1]] = case["value"]
            drift_path.write_text(json.dumps(malformed))
            proc = subprocess.run(command(SOURCE, binding_path, drift_path,
                                          "--export-package", str(temp / "malformed-governance")),
                                  cwd=ROOT, text=True, capture_output=True)
            assert proc.returncode == 3, case["path"]
            assert "BUZZ_UPSTREAM_DRIFT_UNREVIEWED" in {
                item["code"] for item in json.loads(proc.stdout)["diagnostics"]
            }, case["path"]
            assert not (temp / "malformed-governance").exists()
        drift_path.write_text(json.dumps(drift()))

        tampered_proof = binding(SOURCE)
        signature = tampered_proof["ownerBindingProof"]["signatureBytes"]
        tampered_proof["ownerBindingProof"]["signatureBytes"] = (
            ("00" if signature[:2] != "00" else "01") + signature[2:]
        )
        binding_path.write_text(json.dumps(tampered_proof))
        proc = subprocess.run(command(SOURCE, binding_path, drift_path), cwd=ROOT,
                              text=True, capture_output=True)
        assert proc.returncode == 3
        assert "BUZZ_IDENTITY_BINDING_INVALID" in [d["code"] for d in json.loads(proc.stdout)["diagnostics"]]

        sensitive = temp / "sensitive.yaml"
        sensitive.write_bytes(SOURCE.read_bytes().replace(b"reviewed public input", b"api_key=sk-secretsecretsecret"))
        binding_path.write_text(json.dumps(binding(sensitive)))
        proc = subprocess.run(command(sensitive, binding_path, drift_path), cwd=ROOT, text=True, capture_output=True)
        assert proc.returncode == 3
        assert "BUZZ_PUBLIC_SENSITIVE_CONTENT" in [d["code"] for d in json.loads(proc.stdout)["diagnostics"]]

        binding_path.write_text(json.dumps(binding(COMPOUND)))
        drift_path.write_text(STALE_DRIFT.read_text())
        proc = subprocess.run(command(COMPOUND, binding_path, drift_path,
                                      "--export-package", str(temp / "compound-refused")),
                              cwd=ROOT, text=True, capture_output=True)
        assert proc.returncode == 3
        compound_report = json.loads(proc.stdout)
        codes = {item["code"] for item in compound_report["diagnostics"]}
        assert {"BUZZ_AUTHORITY_CLAIM_REFUSED", "BUZZ_PAYMENT_AUTHORITY_REFUSED",
                "BUZZ_POLICY_UNRESOLVED",
                "BUZZ_PUBLIC_SENSITIVE_CONTENT", "BUZZ_RUNTIME_CAPABILITY_REFUSED",
                "BUZZ_SURFACE_UNSUPPORTED", "BUZZ_UPSTREAM_DRIFT_UNREVIEWED"} <= codes
        assert not (temp / "compound-refused").exists()
        for row in compound_report["surfaceRows"]:
            if row["path"] in {"harness.tools", "harness.skills", "harness.dataSources",
                               "harness.memory", "harness.deployment", "metadata.description"}:
                assert row["diagnostics"], row["path"]

        drift_path.write_text(json.dumps(drift()))
        revoked = binding(SOURCE)
        revoked["status"] = "revoked"
        binding_path.write_text(json.dumps(revoked))
        proc = subprocess.run(command(SOURCE, binding_path, drift_path), cwd=ROOT,
                              text=True, capture_output=True)
        assert proc.returncode == 3
        assert "BUZZ_IDENTITY_BINDING_INVALID" in [d["code"] for d in json.loads(proc.stdout)["diagnostics"]]

        source_link = temp / "source-link.yaml"
        source_link.symlink_to(SOURCE)
        binding_path.write_text(json.dumps(binding(source_link)))
        proc = subprocess.run(command(source_link, binding_path, drift_path), cwd=ROOT,
                              text=True, capture_output=True)
        assert proc.returncode == 3
        assert "BUZZ_PUBLIC_SENSITIVE_CONTENT" in [d["code"] for d in json.loads(proc.stdout)["diagnostics"]]

        binding_path.write_text(json.dumps(binding(SOURCE)))
        destination_target = temp / "destination-target"
        destination_target.mkdir()
        destination_link = temp / "destination-link"
        destination_link.symlink_to(destination_target, target_is_directory=True)
        proc = subprocess.run(command(SOURCE, binding_path, drift_path, "--export-package", str(destination_link)),
                              cwd=ROOT, text=True, capture_output=True)
        assert proc.returncode == 4
        assert not list(destination_target.iterdir())

        help_text = subprocess.run([PYTHON, "scripts/buzz_export.py", "--help"], cwd=ROOT,
                                   text=True, capture_output=True, check=True).stdout.lower()
        assert "--import" not in help_text and "round-trip" not in help_text and "reverse" not in help_text

    print("PASS deterministic Buzz static exporter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
