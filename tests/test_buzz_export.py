#!/usr/bin/env python3
"""Focused deterministic Buzz static exporter checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SOURCE = ROOT / "tests" / "fixtures" / "buzz-valid-static-agent.yaml"
ATTRIBUTION = ROOT / "tests" / "fixtures" / "buzz-attribution-distribution-request.json"
COMPOUND = ROOT / "tests" / "fixtures" / "buzz-compound-refusal-agent.yaml"
STALE_DRIFT = ROOT / "tests" / "fixtures" / "buzz-upstream-drift-unreviewed.json"
SCHEMA = ROOT / "specs" / "ADL-v0.2.schema.json"
PIN = "a" * 40
GENERATED_AT = "2026-07-31T01:00:00Z"
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


def canonical_uri(path: Path) -> str:
    if path.resolve() == SOURCE.resolve():
        return "repo:tests/fixtures/buzz-valid-static-agent.yaml"
    return f"urn:reddiagent:test:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def binding(path: Path) -> dict:
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
        "sequence": 1,
        "previousBindingDigest": None,
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
    record = {"recordVersion": 1, "recordSequence": 1, "actorKeyId": owner,
              "actorPubkey": owner, "signatureAlgorithm": "ed25519", "action": "active",
              "bindingDigest": binding_digest, "previousBindingDigest": None,
              "replacementBindingDigest": None, "effectiveAt": "2026-07-31T00:00:00Z",
              "reasonCode": "OWNER_REVIEWED", "reason": "Owner-reviewed static export fixture."}
    record_message = preimage("reddiagent-buzz-identity-transition-v1", record)
    record["signatureBytes"] = sign(record_message)
    record["evidenceDigest"] = hashlib.sha256(
        record_message + b"\x00" + bytes.fromhex(record["signatureBytes"])
    ).hexdigest()
    return {**value, "ownerBindingProof": proof, "status": "active",
            "lifecycleEvidence": [record], "bindingDigest": binding_digest}


def drift() -> dict:
    return {"reviewed": True, "relevantDrift": False, "mergeBase": PIN,
            "upstreamCommit": PIN, "forkCommit": PIN, "adapterCommit": PIN,
            "reviewedAt": "2026-07-31T00:30:00Z", "reviewer": "fixture-owner"}


def command(source: Path, binding_path: Path, drift_path: Path, *extra: str) -> list[str]:
    return [PYTHON, "scripts/buzz_export.py", "--single", str(source),
            "--canonical-uri", canonical_uri(source),
            "--schema", str(SCHEMA), "--source-commit", PIN,
            "--upstream-commit", PIN, "--fork-commit", PIN,
            "--adapter-commit", PIN, "--identity-binding", str(binding_path),
            "--drift-review", str(drift_path), "--generated-at", GENERATED_AT, *extra]


def assert_boundaries(item: dict) -> None:
    for key in ("runtimeExecutionAllowed", "networkAccess", "relayAccess",
                "providerAccess", "credentialAccess", "toolExecutionAllowed",
                "mcpInvocation", "walletAccess", "paymentAccess",
                "deploymentAllowed", "bidirectionalImportAllowed",
                "publicDistributionAllowed", "publicBrandingAllowed"):
        assert item[key] is False, key


def main() -> int:
    sys.path.insert(0, str(ROOT / "scripts"))
    from buzz_export import _ed_verify, build_report

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
        assert_boundaries(report)

        round_trip_report, round_trip_projection = build_report(
            SOURCE, canonical_uri(SOURCE), SCHEMA,
            {"sourceCommit": PIN, "upstreamCommit": PIN, "forkCommit": PIN,
             "adapterCommit": PIN},
            binding(SOURCE), drift(), GENERATED_AT, request_round_trip=True,
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
            assert_boundaries(json.loads((dest / "manifest.json").read_text()))
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
