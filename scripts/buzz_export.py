#!/usr/bin/env python3
"""Deterministic, local-only ADL v0.2 to Buzz static projection report."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone

import jsonschema
import yaml

from prosumer_builder_plan import BOUNDARY_FLAGS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "specs" / "ADL-v0.2.schema.json"
PIN_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
SIGNATURE_RE = re.compile(r"^[0-9a-f]{128}$")
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
SENSITIVE_RE = re.compile(
    r"(?i)(-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:api[_-]?key|secret|password|"
    r"private[_-]?key|seed[_-]?phrase)\s*[:=]\s*[^\s]+|sk-[a-z0-9_-]{12,})"
)
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

# Minimal verification-only Ed25519 implementation. It deliberately supports
# one reviewed algorithm instead of delegating identity proof to caller booleans
# or ambient crypto providers.
_Q = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _Q - 2, _Q)) % _Q
_I = pow(2, (_Q - 1) // 4, _Q)


def _ed_xrecover(y: int) -> int:
    xx = (y * y - 1) * pow(_D * y * y + 1, _Q - 2, _Q) % _Q
    x = pow(xx, (_Q + 3) // 8, _Q)
    if (x * x - xx) % _Q:
        x = x * _I % _Q
    if x & 1:
        x = _Q - x
    return x


_B = (_ed_xrecover(4 * pow(5, _Q - 2, _Q) % _Q), 4 * pow(5, _Q - 2, _Q) % _Q)
_IDENTITY = (0, 1)


def _ed_add(p: tuple[int, int], q: tuple[int, int]) -> tuple[int, int]:
    x1, y1 = p
    x2, y2 = q
    factor = _D * x1 * x2 * y1 * y2 % _Q
    return ((x1 * y2 + x2 * y1) * pow(1 + factor, _Q - 2, _Q) % _Q,
            (y1 * y2 + x1 * x2) * pow(1 - factor, _Q - 2, _Q) % _Q)


def _ed_scalar_mult(p: tuple[int, int], scalar: int) -> tuple[int, int]:
    result = _IDENTITY
    addend = p
    while scalar:
        if scalar & 1:
            result = _ed_add(result, addend)
        addend = _ed_add(addend, addend)
        scalar >>= 1
    return result


def _ed_decode(raw: bytes) -> tuple[int, int]:
    if len(raw) != 32:
        raise ValueError("Ed25519 point must be 32 bytes")
    encoded = int.from_bytes(raw, "little")
    y = encoded & ((1 << 255) - 1)
    if y >= _Q:
        raise ValueError("non-canonical Ed25519 point")
    x = _ed_xrecover(y)
    if (x & 1) != (encoded >> 255):
        x = _Q - x
    point = (x, y)
    if _ed_scalar_mult(point, _L) != _IDENTITY or point == _IDENTITY:
        raise ValueError("invalid Ed25519 subgroup")
    return point


def _ed_verify(public_key_hex: object, signature_hex: object, message: bytes) -> bool:
    try:
        if (not isinstance(public_key_hex, str) or not DIGEST_RE.fullmatch(public_key_hex) or
                not isinstance(signature_hex, str) or not SIGNATURE_RE.fullmatch(signature_hex)):
            return False
        public_key = bytes.fromhex(public_key_hex)
        signature = bytes.fromhex(signature_hex)
        if len(signature) != 64:
            return False
        a_point = _ed_decode(public_key)
        r_point = _ed_decode(signature[:32])
        scalar = int.from_bytes(signature[32:], "little")
        if scalar >= _L:
            return False
        challenge = int.from_bytes(
            hashlib.sha512(signature[:32] + public_key + message).digest(), "little"
        ) % _L
        return _ed_scalar_mult(_B, scalar) == _ed_add(r_point, _ed_scalar_mult(a_point, challenge))
    except (ValueError, OverflowError):
        return False


def _jcs_string(value: str) -> str:
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise ValueError("RFC 8785 forbids unpaired Unicode surrogates")
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _jcs_number(value: int | float) -> str:
    if isinstance(value, bool):
        raise TypeError("boolean is not a JSON number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("RFC 8785 forbids non-finite numbers")
    if isinstance(value, int) and abs(value) > 2**53 - 1:
        raise ValueError("integer is outside the interoperable IEEE-754 range")
    if number == 0:
        return "0"
    negative = number < 0
    rendered = repr(abs(number)).lower()
    mantissa, exponent_text = (rendered.split("e", 1) + ["0"])[:2] if "e" in rendered else (rendered, "0")
    exponent = int(exponent_text)
    before, _, after = mantissa.partition(".")
    digits = (before + after).lstrip("0")
    decimal_position = len(before) + exponent - (len(before + after) - len((before + after).lstrip("0")))
    digits = digits.rstrip("0") or "0"
    absolute = abs(number)
    if 1e-6 <= absolute < 1e21:
        if decimal_position <= 0:
            body = "0." + "0" * (-decimal_position) + digits
        elif decimal_position >= len(digits):
            body = digits + "0" * (decimal_position - len(digits))
        else:
            body = digits[:decimal_position] + "." + digits[decimal_position:]
    else:
        body = digits[0] + (("." + digits[1:]) if len(digits) > 1 else "")
        scientific_exponent = decimal_position - 1
        body += "e" + ("+" if scientific_exponent >= 0 else "") + str(scientific_exponent)
    return ("-" if negative else "") + body


def _jcs(value: object) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return _jcs_number(value)
    if isinstance(value, str):
        return _jcs_string(value)
    if isinstance(value, list):
        return "[" + ",".join(_jcs(item) for item in value) + "]"
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("RFC 8785 object keys must be strings")
        keys = sorted(value, key=lambda key: key.encode("utf-16be"))
        return "{" + ",".join(_jcs_string(key) + ":" + _jcs(value[key]) for key in keys) + "}"
    raise TypeError(f"unsupported RFC 8785 value: {type(value).__name__}")


def canonical_bytes(value: object) -> bytes:
    """Return RFC 8785/JCS canonical UTF-8 bytes."""
    return _jcs(value).encode("utf-8")


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
                       ".".join(map(str, e.path)) or "<root>",
                       "Canonical ADL v0.2 schema validation failed.",
                       "Correct the canonical ADL v0.2 source.") for e in errors]


def _parse_utc(value: object) -> datetime:
    if not isinstance(value, str) or not RFC3339_UTC_RE.fullmatch(value):
        raise ValueError("timestamp must be unambiguous RFC 3339 UTC")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _domain_preimage(domain: str, value: dict) -> bytes:
    return domain.encode("utf-8") + b"\x00" + canonical_bytes(value)


def _verify_related_binding(evidence: object) -> dict | None:
    """Recompute a related immutable binding and prove its owner activation."""
    fields = {
        "canonicalAgentId", "canonicalAdlUri", "canonicalAdlDigest",
        "canonicalAdlVersion", "buzzAgentPubkey", "ownerPubkey", "issuedAt",
        "notBefore", "expiresAt", "sequence", "previousBindingDigest",
        "emergencyRevocationAuthorities", "ownerBindingProof", "bindingDigest",
        "lifecycleEvidence",
    }
    immutable_fields = (
        "canonicalAgentId", "canonicalAdlUri", "canonicalAdlDigest",
        "canonicalAdlVersion", "buzzAgentPubkey", "ownerPubkey", "issuedAt",
        "notBefore", "expiresAt", "sequence", "previousBindingDigest",
        "emergencyRevocationAuthorities",
    )
    try:
        if not isinstance(evidence, dict) or set(evidence) != fields:
            return None
        sequence = evidence["sequence"]
        predecessor = evidence["previousBindingDigest"]
        if (not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1 or
                (sequence == 1 and predecessor is not None) or
                (sequence > 1 and not DIGEST_RE.fullmatch(str(predecessor))) or
                not DIGEST_RE.fullmatch(str(evidence["canonicalAdlDigest"])) or
                evidence["canonicalAdlVersion"] != "reddiagent.dev/v0.2" or
                not isinstance(evidence["canonicalAgentId"], str) or
                not evidence["canonicalAgentId"] or
                not isinstance(evidence["canonicalAdlUri"], str) or
                not evidence["canonicalAdlUri"] or
                not DIGEST_RE.fullmatch(str(evidence["buzzAgentPubkey"])) or
                not DIGEST_RE.fullmatch(str(evidence["ownerPubkey"])) or
                evidence["buzzAgentPubkey"] == evidence["ownerPubkey"]):
            return None
        issued = _parse_utc(evidence["issuedAt"])
        not_before = _parse_utc(evidence["notBefore"])
        expires = _parse_utc(evidence["expiresAt"])
        if not issued <= not_before < expires:
            return None
        emergency = evidence["emergencyRevocationAuthorities"]
        if not isinstance(emergency, list):
            return None
        emergency_sort = sorted(
            emergency, key=lambda item: (str(item.get("signerKeyId", "")).encode(),
                                         str(item.get("signerPubkey", "")).encode())
        )
        if emergency != emergency_sort:
            return None
        seen_emergency: set[str] = set()
        for authority in emergency:
            if (not isinstance(authority, dict) or
                    set(authority) != {"signerKeyId", "signerPubkey", "signatureAlgorithm",
                                       "bindingScope", "allowedActions", "notBefore", "expiresAt"}):
                return None
            key_id = authority["signerKeyId"]
            if (not isinstance(key_id, str) or not key_id or key_id in seen_emergency or
                    not DIGEST_RE.fullmatch(str(authority["signerPubkey"])) or
                    authority["signatureAlgorithm"] != "ed25519" or
                    authority["bindingScope"] != "this-binding-only" or
                    authority["allowedActions"] != ["revoked"]):
                return None
            if (authority["notBefore"] is not None and
                    _parse_utc(authority["notBefore"]) < not_before):
                return None
            if (authority["expiresAt"] is not None and
                    _parse_utc(authority["expiresAt"]) > expires):
                return None
            seen_emergency.add(key_id)
        immutable = {key: evidence[key] for key in immutable_fields}
        digest = sha256(_domain_preimage("reddiagent-buzz-identity-binding-v1", immutable))
        if evidence["bindingDigest"] != digest:
            return None
        proof = evidence["ownerBindingProof"]
        proof_fields = {"proofVersion", "canonicalizationVersion", "signatureAlgorithm",
                        "signerKeyId", "signatureBytes"}
        if (not isinstance(proof, dict) or set(proof) != proof_fields or
                proof["proofVersion"] != 1 or proof["canonicalizationVersion"] != "RFC8785" or
                proof["signatureAlgorithm"] != "ed25519" or
                proof["signerKeyId"] != evidence["ownerPubkey"]):
            return None
        proof_payload = {key: proof[key] for key in (
            "proofVersion", "canonicalizationVersion", "signatureAlgorithm", "signerKeyId"
        )}
        proof_payload["bindingDigest"] = digest
        if not _ed_verify(evidence["ownerPubkey"], proof["signatureBytes"],
                          _domain_preimage("reddiagent-buzz-owner-binding-proof-v1", proof_payload)):
            return None
        records = evidence["lifecycleEvidence"]
        if not isinstance(records, list) or len(records) != 1:
            return None
        record = records[0]
        record_fields = {
            "recordVersion", "recordSequence", "actorKeyId", "actorPubkey",
            "signatureAlgorithm", "action", "bindingDigest", "previousBindingDigest",
            "replacementBindingDigest", "effectiveAt", "reasonCode", "reason",
            "evidenceDigest", "signatureBytes",
        }
        if (not isinstance(record, dict) or set(record) != record_fields or
                record["recordVersion"] != 1 or
                not isinstance(record["recordSequence"], int) or
                isinstance(record["recordSequence"], bool) or record["recordSequence"] < 1 or
                record["actorKeyId"] != evidence["ownerPubkey"] or
                record["actorPubkey"] != evidence["ownerPubkey"] or
                record["signatureAlgorithm"] != "ed25519" or record["action"] != "active" or
                record["bindingDigest"] != digest or
                record["previousBindingDigest"] != predecessor or
                record["replacementBindingDigest"] is not None):
            return None
        signed = {key: record[key] for key in (
            "recordVersion", "recordSequence", "actorKeyId", "actorPubkey",
            "signatureAlgorithm", "action", "bindingDigest", "previousBindingDigest",
            "replacementBindingDigest", "effectiveAt", "reasonCode", "reason",
        )}
        preimage = _domain_preimage("reddiagent-buzz-identity-transition-v1", signed)
        if not _ed_verify(evidence["ownerPubkey"], record["signatureBytes"], preimage):
            return None
        signature = bytes.fromhex(record["signatureBytes"])
        if record["evidenceDigest"] != sha256(preimage + b"\x00" + signature):
            return None
        activated = _parse_utc(record["effectiveAt"])
        if not_before > activated or activated >= expires:
            return None
        return {"bindingDigest": digest, "sequence": sequence, "previousBindingDigest": predecessor,
                "canonicalAgentId": evidence["canonicalAgentId"],
                "ownerPubkey": evidence["ownerPubkey"], "activatedAt": activated}
    except (KeyError, TypeError, ValueError, UnicodeError):
        return None


def _identity_diagnostics(binding: dict, adl_digest: str, canonical_uri: str,
                          evaluation_time: str | None) -> list[dict]:
    """Verify the immutable #424 owner proof and signed lifecycle fold."""
    invalid = [diagnostic(
        "BUZZ_IDENTITY_BINDING_INVALID", "refused", "identityBinding",
        "Identity binding proof or lifecycle evidence is invalid, stale, expired, or revoked.",
        "Supply owner-signed #424 binding and lifecycle evidence for these exact source bytes.")]
    try:
        required = {
            "canonicalAgentId", "canonicalAdlUri", "canonicalAdlDigest",
            "canonicalAdlVersion", "buzzAgentPubkey", "ownerPubkey",
            "ownerAttestationRef", "ownerBindingProof", "issuedAt", "notBefore",
            "expiresAt", "sequence", "previousBindingDigest",
            "emergencyRevocationAuthorities", "status", "lifecycleEvidence",
            "bindingDigest", "relatedBindings",
        }
        if not isinstance(binding, dict) or set(binding) != required:
            return invalid
        if (binding["canonicalAdlDigest"] != adl_digest or
                binding["canonicalAdlUri"] != canonical_uri or
                binding["canonicalAdlVersion"] != "reddiagent.dev/v0.2" or
                not isinstance(binding["canonicalAgentId"], str) or
                not binding["canonicalAgentId"] or not binding["ownerAttestationRef"] or
                not DIGEST_RE.fullmatch(str(binding["buzzAgentPubkey"])) or
                not DIGEST_RE.fullmatch(str(binding["ownerPubkey"])) or
                binding["buzzAgentPubkey"] == binding["ownerPubkey"]):
            return invalid
        if not isinstance(binding["sequence"], int) or isinstance(binding["sequence"], bool) or binding["sequence"] < 1:
            return invalid
        if ((binding["sequence"] == 1 and binding["previousBindingDigest"] is not None) or
                (binding["sequence"] > 1 and not DIGEST_RE.fullmatch(
                    str(binding["previousBindingDigest"]))) or
                binding["previousBindingDigest"] == binding.get("bindingDigest")):
            return invalid
        issued = _parse_utc(binding["issuedAt"])
        not_before = _parse_utc(binding["notBefore"])
        expires = _parse_utc(binding["expiresAt"])
        evaluated = _parse_utc(evaluation_time)
        if not (issued <= not_before < expires) or evaluated < not_before:
            return invalid

        emergency = binding["emergencyRevocationAuthorities"]
        if not isinstance(emergency, list):
            return invalid
        emergency_sort = sorted(
            emergency, key=lambda item: (str(item.get("signerKeyId", "")).encode(),
                                         str(item.get("signerPubkey", "")).encode())
        )
        if emergency != emergency_sort:
            return invalid
        emergency_keys: dict[str, dict] = {}
        for authority in emergency:
            if set(authority) != {"signerKeyId", "signerPubkey", "signatureAlgorithm",
                                  "bindingScope", "allowedActions", "notBefore", "expiresAt"}:
                return invalid
            key_id = authority["signerKeyId"]
            if (not isinstance(key_id, str) or not key_id or key_id in emergency_keys or
                    authority["signatureAlgorithm"] != "ed25519" or
                    authority["bindingScope"] != "this-binding-only" or
                    authority["allowedActions"] != ["revoked"]):
                return invalid
            if authority["notBefore"] is not None and _parse_utc(authority["notBefore"]) < not_before:
                return invalid
            if authority["expiresAt"] is not None and _parse_utc(authority["expiresAt"]) > expires:
                return invalid
            emergency_keys[key_id] = authority

        immutable = {key: binding[key] for key in (
            "canonicalAgentId", "canonicalAdlUri", "canonicalAdlDigest",
            "canonicalAdlVersion", "buzzAgentPubkey", "ownerPubkey", "issuedAt",
            "notBefore", "expiresAt", "sequence", "previousBindingDigest",
            "emergencyRevocationAuthorities",
        )}
        binding_digest = sha256(_domain_preimage("reddiagent-buzz-identity-binding-v1", immutable))
        if binding["bindingDigest"] != binding_digest:
            return invalid

        proof = binding["ownerBindingProof"]
        proof_fields = {"proofVersion", "canonicalizationVersion", "signatureAlgorithm",
                        "signerKeyId", "signatureBytes"}
        if not isinstance(proof, dict) or set(proof) != proof_fields:
            return invalid
        if (proof["proofVersion"] != 1 or proof["canonicalizationVersion"] != "RFC8785" or
                proof["signatureAlgorithm"] != "ed25519" or
                proof["signerKeyId"] != binding["ownerPubkey"]):
            return invalid
        proof_payload = {key: proof[key] for key in (
            "proofVersion", "canonicalizationVersion", "signatureAlgorithm", "signerKeyId"
        )}
        proof_payload["bindingDigest"] = binding_digest
        if not _ed_verify(binding["ownerPubkey"], proof["signatureBytes"],
                          _domain_preimage("reddiagent-buzz-owner-binding-proof-v1", proof_payload)):
            return invalid

        related_items = binding["relatedBindings"]
        if not isinstance(related_items, list):
            return invalid
        related: dict[str, dict] = {}
        for item in related_items:
            verified = _verify_related_binding(item)
            if (verified is None or verified["bindingDigest"] in related or
                    verified["canonicalAgentId"] != binding["canonicalAgentId"] or
                    verified["ownerPubkey"] != binding["ownerPubkey"]):
                return invalid
            related[verified["bindingDigest"]] = verified
        if list(related) != sorted(related, key=lambda item: bytes.fromhex(item)):
            return invalid
        immutable_predecessor = binding["previousBindingDigest"]
        if immutable_predecessor is not None:
            predecessor_evidence = related.get(immutable_predecessor)
            if (predecessor_evidence is None or
                    predecessor_evidence["sequence"] + 1 != binding["sequence"]):
                return invalid

        records = binding["lifecycleEvidence"]
        if not isinstance(records, list):
            return invalid
        validated: list[tuple[datetime, int, int, bytes, str, str | None]] = []
        seen_sequences: set[int] = set()
        action_rank = {"revoked": 0, "superseded": 1, "rotating": 2, "active": 3}
        record_fields = {
            "recordVersion", "recordSequence", "actorKeyId", "actorPubkey",
            "signatureAlgorithm", "action", "bindingDigest", "previousBindingDigest",
            "replacementBindingDigest", "effectiveAt", "reasonCode", "reason",
            "evidenceDigest", "signatureBytes",
        }
        for record in records:
            if not isinstance(record, dict) or set(record) != record_fields:
                return invalid
            sequence = record["recordSequence"]
            action = record["action"]
            if (record["recordVersion"] != 1 or not isinstance(sequence, int) or
                    isinstance(sequence, bool) or sequence < 1 or sequence in seen_sequences or
                    action not in action_rank or record["bindingDigest"] != binding_digest or
                    record["signatureAlgorithm"] != "ed25519"):
                return invalid
            seen_sequences.add(sequence)
            actor_key = None
            if record["actorKeyId"] == binding["ownerPubkey"] and record["actorPubkey"] == binding["ownerPubkey"]:
                actor_key = binding["ownerPubkey"]
            elif record["actorKeyId"] in emergency_keys:
                authority = emergency_keys[record["actorKeyId"]]
                if action != "revoked" or record["actorPubkey"] != authority["signerPubkey"]:
                    return invalid
                actor_key = authority["signerPubkey"]
            if actor_key is None:
                return invalid
            for digest_field in ("previousBindingDigest", "replacementBindingDigest"):
                if record[digest_field] is not None and not DIGEST_RE.fullmatch(str(record[digest_field])):
                    return invalid
            predecessor = record["previousBindingDigest"]
            replacement = record["replacementBindingDigest"]
            if action == "active" and (predecessor != binding["previousBindingDigest"] or
                                       replacement is not None):
                return invalid
            if action == "revoked" and (predecessor is not None or replacement is not None):
                return invalid
            if action in {"rotating", "superseded"} and (
                    predecessor != binding_digest or replacement is None or
                    replacement == binding_digest):
                return invalid
            signed = {key: record[key] for key in (
                "recordVersion", "recordSequence", "actorKeyId", "actorPubkey",
                "signatureAlgorithm", "action", "bindingDigest", "previousBindingDigest",
                "replacementBindingDigest", "effectiveAt", "reasonCode", "reason",
            )}
            domain = ("reddiagent-buzz-identity-revocation-v1" if action == "revoked"
                      else "reddiagent-buzz-identity-transition-v1")
            preimage = _domain_preimage(domain, signed)
            if not _ed_verify(actor_key, record["signatureBytes"], preimage):
                return invalid
            signature = bytes.fromhex(record["signatureBytes"])
            evidence_digest = sha256(preimage + b"\x00" + signature)
            if record["evidenceDigest"] != evidence_digest:
                return invalid
            effective = _parse_utc(record["effectiveAt"])
            if effective < not_before:
                return invalid
            if action == "active" and predecessor is not None:
                predecessor_evidence = related.get(predecessor)
                if (predecessor_evidence is None or
                        predecessor_evidence["activatedAt"] > effective):
                    return invalid
            if action in {"rotating", "superseded"}:
                replacement_evidence = related.get(replacement)
                if (replacement_evidence is None or
                        replacement_evidence["sequence"] != binding["sequence"] + 1 or
                        replacement_evidence["previousBindingDigest"] != binding_digest or
                        (action == "rotating" and replacement_evidence["activatedAt"] < effective) or
                        (action == "superseded" and replacement_evidence["activatedAt"] > effective)):
                    return invalid
            if record["actorKeyId"] in emergency_keys:
                authority = emergency_keys[record["actorKeyId"]]
                if ((authority["notBefore"] is not None and effective < _parse_utc(authority["notBefore"])) or
                        (authority["expiresAt"] is not None and effective >= _parse_utc(authority["expiresAt"]))):
                    return invalid
            validated.append((effective, sequence, action_rank[action], bytes.fromhex(evidence_digest),
                              action, replacement))

        validated.sort(key=lambda item: item[:4])
        derived_status = "bound"
        pending_replacement = None
        for effective, _, _, _, action, replacement in validated:
            if effective <= evaluated:
                allowed = {
                    "bound": {"active", "rotating", "revoked"},
                    "active": {"rotating", "revoked"},
                    "rotating": {"superseded", "revoked"},
                    "superseded": {"revoked"},
                    "revoked": set(),
                }
                if action not in allowed[derived_status]:
                    return invalid
                if action == "rotating":
                    pending_replacement = replacement
                elif action == "superseded" and replacement != pending_replacement:
                    return invalid
                derived_status = action
        if derived_status != "revoked" and expires <= evaluated:
            derived_status = "expired"
        if binding["status"] != derived_status or derived_status != "active":
            return invalid
        return []
    except (KeyError, TypeError, ValueError, UnicodeError):
        return invalid


def _surface_diagnostics(doc: dict) -> list[dict]:
    result: list[dict] = []
    harness = doc.get("harness", {}) or {}
    policies = {item.get("id") for item in harness.get("policies", []) or [] if isinstance(item, dict)}

    def unresolved(path: str, item: dict) -> None:
        refs = item.get("policyRefs", []) or []
        if any(ref not in policies for ref in refs):
            result.append(diagnostic(
                "BUZZ_POLICY_UNRESOLVED", "refused", path,
                "One or more policy references do not resolve in canonical ADL.",
                "Define and owner-review every referenced policy."))

    for collection in ("tools", "functions"):
        for index, item in enumerate(harness.get(collection, []) or []):
            if not isinstance(item, dict):
                continue
            path = f"harness.{collection}.{index}"
            unresolved(path, item)
            side_effects = item.get("sideEffects", {}) or {}
            permissions = set(item.get("permissions", []) or [])
            executable = (item.get("type") in {"mcp", "http", "native"} or
                          side_effects.get("mode") not in {None, "none", "read"} or
                          side_effects.get("mutatesState") is True or
                          side_effects.get("external") is True or
                          bool(permissions & {"network", "payment", "shell", "filesystem",
                                              "messaging", "mcp", "mutation"}))
            if executable:
                result.append(diagnostic(
                    "BUZZ_RUNTIME_CAPABILITY_REFUSED", "refused", path,
                    "Executable, external, mutating, or privileged tool semantics cannot enter G1.",
                    "Project only inert reviewed contract metadata."))

    for index, item in enumerate(harness.get("skills", []) or []):
        if not isinstance(item, dict):
            continue
        path = f"harness.skills.{index}"
        unresolved(path, item)
        keys = {str(key).lower() for key in item}
        if keys & {"command", "entrypoint", "hook", "install", "executable", "runtime"}:
            result.append(diagnostic(
                "BUZZ_RUNTIME_CAPABILITY_REFUSED", "refused", path,
                "Executable skill or automatic-install semantics cannot enter G1.",
                "Retain only reviewed static skill description metadata."))
        for key in ("path", "asset", "source"):
            if key in item and (Path(str(item[key])).is_absolute() or ".." in Path(str(item[key])).parts):
                result.append(diagnostic(
                    "BUZZ_PUBLIC_SENSITIVE_CONTENT", "refused", path,
                    "Skill metadata contains an unsafe asset path.",
                    "Use reviewed in-root relative static asset paths."))

    for index, item in enumerate(harness.get("dataSources", []) or []):
        if not isinstance(item, dict):
            continue
        path = f"harness.dataSources.{index}"
        if item.get("trust") != "approved" or (item.get("sourceCheck") or {}).get("expectation") != "approved-source":
            result.append(diagnostic(
                "BUZZ_POLICY_UNRESOLVED", "refused", path,
                "Data-source trust boundary is not owner-reviewed and approved.",
                "Provide approved source-check evidence without fetching data."))
        if item.get("type") != "file" or any(key in item for key in ("api", "database", "vectorIndex", "mcp")):
            result.append(diagnostic(
                "BUZZ_RUNTIME_CAPABILITY_REFUSED", "refused", path,
                "External data-source access cannot enter a static G1 package.",
                "Retain only redacted review metadata and perform no fetch."))
        if any(token in canonical_bytes(item).decode("utf-8", errors="ignore").lower()
               for token in ("authref", "connectionref", "credential", "private")):
            result.append(diagnostic(
                "BUZZ_PUBLIC_SENSITIVE_CONTENT", "refused", path,
                "Data-source metadata exposes a private or credential-bearing boundary.",
                "Remove private connection and credential metadata."))

    memory = harness.get("memory") or {}
    if memory:
        stateful = memory.get("mode") in {"persistent", "external"} or memory.get("scope") in {"workspace", "external"}
        result.append(diagnostic(
            "BUZZ_SURFACE_UNSUPPORTED", "unsupported", "harness.memory",
            "Memory is report-only and is never copied.",
            "Keep memory outside the Buzz package.", blocking=False))
        if stateful:
            result.append(diagnostic(
                "BUZZ_PUBLIC_SENSITIVE_CONTENT", "refused", "harness.memory",
                "Persistent, external, or workspace memory cannot be copied.",
                "Keep stateful memory outside the Buzz package."))
    if harness.get("deployment"):
        result.append(diagnostic(
            "BUZZ_RUNTIME_CAPABILITY_REFUSED", "refused", "harness.deployment",
            "Deployment, hosting, or release intent cannot enter G1.",
            "Keep deployment disabled and outside the static package."))

    authority_surfaces = {
        "metadata.name": (doc.get("metadata") or {}).get("name", ""),
        "metadata.description": (doc.get("metadata") or {}).get("description", ""),
        "harness.instructions.inline": (harness.get("instructions") or {}).get("inline", ""),
        "extensions": doc.get("extensions", {}),
    }
    for path, value in authority_surfaces.items():
        if re.search(r"(?i)buzz.{0,80}(authoritative|settled|accepted|receipt|reputation|payment authority|eval pass)",
                     str(value)):
            result.append(diagnostic(
                "BUZZ_AUTHORITY_CLAIM_REFUSED", "refused", path,
                "Content represents Buzz context as canonical, payment, receipt, eval, or reputation authority.",
                "Keep ADL canonical and RAP authoritative for payment/receipt/reputation."))
    return result


def _extension_diagnostics(extensions: dict, reviewed: set[str]) -> list[dict]:
    result: list[dict] = []
    known = {"identity", "x402", "receipts", "reputation"}
    runtime_keys = {"command", "entrypoint", "hook", "install", "executable", "runtime",
                    "provider", "network", "endpoint", "tool", "function", "skill", "mcp", "deploy"}
    payment_keys = {"wallet", "payment", "spend", "refund", "settlement", "rpc"}
    sensitive_keys = {"secret", "credential", "password", "privatekey", "seedphrase", "token"}

    def walk(value: object, path: str) -> None:
        if isinstance(value, dict):
            for key in sorted(value, key=lambda item: str(item).encode()):
                normalized = re.sub(r"[^a-z]", "", str(key).lower())
                child = f"{path}.{key}"
                active = value[key] not in (None, False, "", [], {})
                if active and any(token in normalized for token in runtime_keys):
                    result.append(diagnostic("BUZZ_RUNTIME_CAPABILITY_REFUSED", "refused", child,
                                             "Extension contains executable or runtime semantics.",
                                             "Remove executable semantics from the static extension."))
                if active and any(token in normalized for token in payment_keys):
                    result.append(diagnostic("BUZZ_PAYMENT_AUTHORITY_REFUSED", "refused", child,
                                             "Extension contains wallet, payment, RPC, or settlement semantics.",
                                             "Keep all payment authority in RAP."))
                if active and any(token in normalized for token in sensitive_keys | {"apikey", "authref"}):
                    result.append(diagnostic("BUZZ_PUBLIC_SENSITIVE_CONTENT", "refused", child,
                                             "Extension contains credential-bearing or private semantics.",
                                             "Remove private material from public metadata."))
                walk(value[key], child)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}.{index}")
        elif isinstance(value, str):
            if SENSITIVE_RE.search(value):
                result.append(diagnostic("BUZZ_PUBLIC_SENSITIVE_CONTENT", "refused", path,
                                         "Extension contains secret-like content.",
                                         "Remove private material from public metadata."))
            if re.search(r"(?i)buzz.{0,80}(authoritative|settled|accepted|receipt|reputation|payment authority|eval pass)", value):
                result.append(diagnostic("BUZZ_AUTHORITY_CLAIM_REFUSED", "refused", path,
                                         "Extension makes an authority claim Buzz cannot prove.",
                                         "Keep ADL canonical and RAP authoritative."))

    for key in sorted(extensions, key=lambda item: str(item).encode()):
        if key in known:
            continue
        path = f"extensions.{key}"
        if key not in reviewed:
            result.append(diagnostic("BUZZ_SURFACE_UNSUPPORTED", "unsupported", path,
                                     "Extension semantics have not been owner-reviewed.",
                                     "Add the exact namespaced extension to reviewed governance evidence."))
        walk(extensions[key], path)
    return result


def _governance_diagnostics(governance: dict, pins: dict,
                            evaluation_time: str | None) -> list[dict]:
    """Validate the complete #424 drift, adapter, extension, and attribution record."""
    valid = False
    try:
        required = {"reviewVersion", "reviewer", "reviewedAt", "pins", "upstreamDrift",
                    "adapterDecision", "reviewedExtensions", "attribution"}
        if not isinstance(governance, dict) or set(governance) != required:
            raise ValueError
        reviewed_at = _parse_utc(governance["reviewedAt"])
        evaluated_at = _parse_utc(evaluation_time)
        if reviewed_at > evaluated_at or evaluated_at - reviewed_at > timedelta(days=7):
            raise ValueError
        if (governance["reviewVersion"] != 1 or
                not isinstance(governance["reviewer"], str) or not governance["reviewer"]):
            raise ValueError
        def string_list(value: object, *, allow_empty: bool = True) -> bool:
            return (isinstance(value, list) and (allow_empty or bool(value)) and
                    all(isinstance(item, str) and bool(item) for item in value) and
                    value == sorted(set(value), key=lambda item: item.encode("utf-8")))

        pin_record = governance["pins"]
        if (not isinstance(pin_record, dict) or
                set(pin_record) != {"mergeBase", "upstreamCommit", "forkCommit", "adapterCommit"} or
                not PIN_RE.fullmatch(str(pin_record["mergeBase"])) or
                not all(PIN_RE.fullmatch(str(pin_record[key])) for key in
                        ("upstreamCommit", "forkCommit", "adapterCommit")) or
                any(pin_record[key] != pins.get(key) for key in
                    ("upstreamCommit", "forkCommit", "adapterCommit"))):
            raise ValueError
        upstream = governance["upstreamDrift"]
        if (not isinstance(upstream, dict) or
                set(upstream) != {"commitsChanged", "relevantPaths", "linkedUpstreamIssues",
                             "classificationChanges", "negativeClaimsReverified",
                             "relevantDrift", "decision"} or
                upstream["commitsChanged"] != [] or upstream["relevantPaths"] != [] or
                upstream["linkedUpstreamIssues"] != [] or
                upstream["classificationChanges"] != [] or
                upstream["negativeClaimsReverified"] is not True or
                upstream["relevantDrift"] is not False or upstream["decision"] != "hold-no-drift"):
            raise ValueError
        adapter = governance["adapterDecision"]
        if (not isinstance(adapter, dict) or
                set(adapter) != {"chosenLayer", "rejectedHigherLayers", "affectedPaths",
                            "apiSurfaces", "forkDeltaCount", "upstreamCandidate",
                            "maintenanceOwner", "removalTrigger"} or
                adapter["chosenLayer"] != "external-adapter" or adapter["rejectedHigherLayers"] != [] or
                adapter["affectedPaths"] != ["scripts/buzz_export.py"] or
                adapter["apiSurfaces"] != ["static-json"] or
                not isinstance(adapter["forkDeltaCount"], int) or isinstance(adapter["forkDeltaCount"], bool) or
                adapter["forkDeltaCount"] != 0 or adapter["upstreamCandidate"] is not None or
                adapter["maintenanceOwner"] != "reddinft" or
                adapter["removalTrigger"] != "adapter-contract-retired"):
            raise ValueError
        reviewed = governance["reviewedExtensions"]
        if (not string_list(reviewed) or
                not all(item.startswith("x-") or item.startswith("http") for item in reviewed)):
            raise ValueError
        attribution = governance["attribution"]
        attribution_fields = {"upstreamRepository", "downstreamRepository", "license",
                              "notice", "copyrightNotices", "modifiedFiles",
                              "distributionForms", "thirdPartyInventory", "downstreamName",
                              "publicDisclaimer", "trademarkReview", "publicDistributionAllowed",
                              "publicBrandingAllowed"}
        if (not isinstance(attribution, dict) or set(attribution) != attribution_fields or
                attribution["upstreamRepository"] != {"url": "https://github.com/block/buzz", "commit": pins["upstreamCommit"]} or
                attribution["downstreamRepository"] != {"url": "https://github.com/reddinft/buzz", "commit": pins["forkCommit"]} or
                attribution["publicDistributionAllowed"] is not False or
                attribution["publicBrandingAllowed"] is not False or
                attribution["downstreamName"] != "pending-review" or
                attribution["publicDisclaimer"] != "pending-review" or
                attribution["license"] != {"spdx": "Apache-2.0", "textIncluded": False,
                                           "status": "reviewed-hold"} or
                attribution["notice"] != {"present": False, "digest": None,
                                          "status": "reviewed-absent-at-pin"} or
                attribution["copyrightNotices"] != {"status": "reviewed-hold"} or
                not isinstance(attribution["modifiedFiles"], dict) or
                set(attribution["modifiedFiles"]) != {"files", "notices", "status"} or
                not string_list(attribution["modifiedFiles"]["files"]) or
                not string_list(attribution["modifiedFiles"]["notices"]) or
                attribution["modifiedFiles"]["status"] != "not-applicable" or
                attribution["distributionForms"] != {"source": "hold", "object": "hold"} or
                attribution["thirdPartyInventory"] != {"status": "pending-review"} or
                attribution["trademarkReview"] != {"reviewer": None, "date": None,
                                                    "scope": "downstream-name",
                                                    "decision": "pending-review"}):
            raise ValueError
        valid = True
    except (KeyError, TypeError, ValueError, AttributeError):
        valid = False
    if valid:
        return []
    return [diagnostic(
        "BUZZ_UPSTREAM_DRIFT_UNREVIEWED", "refused", "target.driftReview",
        "Exact pins lack complete owner-reviewed drift, adapter, extension, or attribution governance.",
        "Supply the complete #424 governance record for the exact pins.")]


def _governance_summary(governance: dict) -> dict:
    """Allowlist non-sensitive, decision-bearing evidence for public output."""
    try:
        return {
            "reviewVersion": governance["reviewVersion"],
            "reviewedAt": governance["reviewedAt"],
            "pins": dict(governance["pins"]),
            "upstreamDrift": {
                "commitsChanged": [], "relevantPaths": [], "linkedUpstreamIssues": [],
                "classificationChanges": [], "negativeClaimsReverified": True,
                "relevantDrift": False, "decision": "hold-no-drift",
            },
            "adapterDecision": {
                "chosenLayer": "external-adapter", "rejectedHigherLayers": [],
                "affectedPaths": ["scripts/buzz_export.py"], "apiSurfaces": ["static-json"],
                "forkDeltaCount": 0, "upstreamCandidate": None,
                "maintenanceOwner": "reddinft", "removalTrigger": "adapter-contract-retired",
            },
            "reviewedExtensions": governance["reviewedExtensions"],
            "attributionManifest": {
                "upstreamRepository": dict(governance["attribution"]["upstreamRepository"]),
                "downstreamRepository": dict(governance["attribution"]["downstreamRepository"]),
                "license": dict(governance["attribution"]["license"]),
                "notice": dict(governance["attribution"]["notice"]),
                "copyrightNotices": dict(governance["attribution"]["copyrightNotices"]),
                "modifiedFiles": {
                    "files": list(governance["attribution"]["modifiedFiles"]["files"]),
                    "notices": list(governance["attribution"]["modifiedFiles"]["notices"]),
                    "status": governance["attribution"]["modifiedFiles"]["status"],
                },
                "distributionForms": dict(governance["attribution"]["distributionForms"]),
                "thirdPartyInventory": dict(governance["attribution"]["thirdPartyInventory"]),
                "downstreamName": governance["attribution"]["downstreamName"],
                "publicDisclaimer": governance["attribution"]["publicDisclaimer"],
                "trademarkReview": dict(governance["attribution"]["trademarkReview"]),
                "publicDistributionAllowed": False,
                "publicBrandingAllowed": False,
            },
            "publicDistributionAllowed": False,
            "publicBrandingAllowed": False,
        }
    except (KeyError, TypeError):
        return {"valid": False, "publicDistributionAllowed": False, "publicBrandingAllowed": False}


def build_report(source: Path, canonical_uri: str, schema_path: Path, pins: dict,
                 binding: dict, drift: dict, evaluation_time: str,
                 request_distribution: bool = False,
                 request_round_trip: bool = False) -> tuple[dict, dict | None]:
    original_source = source
    original_schema = schema_path
    source_unsafe = original_source.is_symlink() or not original_source.is_file()
    schema_unsafe = (original_schema.is_symlink() or not original_schema.is_file() or
                     original_schema.resolve() != DEFAULT_SCHEMA.resolve())
    source = source.resolve()
    schema_path = schema_path.resolve()
    try:
        source_bytes = source.read_bytes()
    except OSError:
        source_bytes = b""
    schema_bytes = DEFAULT_SCHEMA.read_bytes() if schema_unsafe else schema_path.read_bytes()
    diagnostics: list[dict] = []
    if source_unsafe:
        diagnostics.append(diagnostic("BUZZ_PUBLIC_SENSITIVE_CONTENT", "refused", "canonicalAdl.source",
                                      "Canonical source must be a regular non-symlink file.",
                                      "Use exact reviewed source bytes from a regular file."))
    if schema_unsafe:
        diagnostics.append(diagnostic("BUZZ_TARGET_PIN_INVALID", "refused", "canonicalAdl.schema",
                                      "Schema must be the repository-pinned ADL v0.2 schema file.",
                                      "Use specs/ADL-v0.2.schema.json without symlink indirection."))
    try:
        doc = yaml.safe_load(source_bytes)
    except (UnicodeDecodeError, yaml.YAMLError):
        doc = {}
        diagnostics.append(diagnostic("BUZZ_ADL_INVALID", "refused", "<root>",
                                      "Canonical ADL is not valid UTF-8 YAML.",
                                      "Provide UTF-8 YAML matching ADL v0.2."))
    schema = json.loads(schema_bytes)
    diagnostics.extend(_schema_diagnostics(doc, schema))
    adl_digest = sha256(source_bytes)
    if not canonical_uri or (canonical_uri.startswith("repo:") and not pins.get("sourceCommit")):
        diagnostics.append(diagnostic("BUZZ_CANONICAL_REF_MISSING", "refused", "canonicalAdl.uri",
                                      "Canonical URI or repository source commit is missing.",
                                      "Supply the immutable canonical reference."))
    if canonical_uri.startswith("repo:"):
        try:
            relative = Path(canonical_uri.removeprefix("repo:"))
            repo_path = ROOT / relative
            if (relative.is_absolute() or ".." in relative.parts or repo_path.is_symlink() or
                    ROOT.resolve() not in repo_path.resolve().parents or repo_path.resolve() != source or
                    not PIN_RE.fullmatch(str(pins.get("sourceCommit", "")))):
                raise ValueError
        except (OSError, ValueError):
            diagnostics.append(diagnostic("BUZZ_CANONICAL_REF_MISSING", "refused", "canonicalAdl.uri",
                                          "Repository URI, source path, and source commit do not bind exactly.",
                                          "Use the exact repository-relative path and full source commit."))
    elif pins.get("sourceCommit") and not PIN_RE.fullmatch(str(pins.get("sourceCommit"))):
        diagnostics.append(diagnostic("BUZZ_TARGET_PIN_INVALID", "refused", "canonicalAdl.sourceCommit",
                                      "Optional source commit must be full lowercase 40-hex.",
                                      "Supply an immutable source commit or omit it for a stable non-repository URI."))
    for name in ("upstreamCommit", "forkCommit", "adapterCommit"):
        if not PIN_RE.fullmatch(str(pins.get(name, ""))):
            diagnostics.append(diagnostic("BUZZ_TARGET_PIN_INVALID", "refused", f"target.{name}",
                                          "Target commit must be full lowercase 40-hex.",
                                          "Supply an owner-reviewed immutable commit."))
    governance_diagnostics = _governance_diagnostics(drift, pins, evaluation_time)
    identity_diagnostics = _identity_diagnostics(
        binding, adl_digest, canonical_uri, evaluation_time
    )
    diagnostics.extend(governance_diagnostics)
    diagnostics.extend(identity_diagnostics)
    if request_distribution:
        diagnostics.append(diagnostic("BUZZ_ATTRIBUTION_REVIEW_REQUIRED", "refused", "distribution",
                                      "Public distribution and branding review is incomplete.",
                                      "Complete LICENSE/NOTICE/modified-file and downstream branding review."))
    if request_round_trip:
        diagnostics.append(diagnostic("BUZZ_ONE_WAY_ONLY", "refused", "roundTrip",
                                      "Buzz-to-ADL import or round-trip reconstruction is forbidden.",
                                      "Regenerate only from canonical ADL source bytes."))
    if SENSITIVE_RE.search(source_bytes.decode("utf-8", errors="ignore")):
        diagnostics.append(diagnostic("BUZZ_PUBLIC_SENSITIVE_CONTENT", "refused", "<source>",
                                      "Source contains public-sensitive or secret-like content.",
                                      "Remove private material; redaction is not performed by this exporter."))
    harness = doc.get("harness", {}) if isinstance(doc, dict) else {}
    instructions = harness.get("instructions", {}) or {}
    instruction_text = instructions.get("inline")
    instruction_asset = None
    if "path" in instructions:
        raw_path = instructions.get("path")
        rel = Path(raw_path or "")
        candidate = source.parent / rel
        if not isinstance(raw_path, str) or not raw_path:
            diagnostics.append(diagnostic(
                "BUZZ_ADL_INVALID", "refused", "harness.instructions.path",
                "Instruction path is missing or empty.",
                "Provide a non-empty reviewed relative path."))
        else:
            try:
                resolved = candidate.resolve(strict=True)
                if (rel.is_absolute() or source.parent.resolve() not in resolved.parents or
                        candidate.is_symlink() or not resolved.is_file()):
                    raise OSError("unsafe instruction path")
                asset_bytes = resolved.read_bytes()
                instruction_text = asset_bytes.decode("utf-8")
                instruction_asset = {
                    "path": rel.as_posix(), "sha256": sha256(asset_bytes), "bytes": len(asset_bytes)
                }
                if SENSITIVE_RE.search(instruction_text):
                    raise ValueError("sensitive instruction content")
            except FileNotFoundError:
                diagnostics.append(diagnostic(
                    "BUZZ_INSTRUCTION_FILE_UNAVAILABLE", "refused", "harness.instructions.path",
                    "Instruction file is unavailable.", "Provide a reviewed in-root regular file."))
            except (OSError, UnicodeDecodeError, ValueError):
                diagnostics.append(diagnostic(
                    "BUZZ_PUBLIC_SENSITIVE_CONTENT", "refused", "harness.instructions.path",
                    "Instruction path or content is unsafe for public projection.",
                    "Use a reviewed UTF-8 in-root regular file."))
    diagnostics.extend(_surface_diagnostics(doc if isinstance(doc, dict) else {}))
    runtime = harness.get("runtime", {}) or {}
    if (runtime.get("activation") or {}).get("mode") not in {None, "blocked"} or (runtime.get("network") or {}).get("access") not in {None, "none"}:
        diagnostics.append(diagnostic("BUZZ_RUNTIME_CAPABILITY_REFUSED", "refused", "harness.runtime",
                                      "Runtime activation or network authority was requested.",
                                      "Use blocked activation and network access none."))
    extensions = doc.get("extensions", {}) if isinstance(doc, dict) else {}
    reviewed_extensions = set(drift.get("reviewedExtensions", [])) if isinstance(drift, dict) else set()
    diagnostics.extend(_extension_diagnostics(extensions or {}, reviewed_extensions))
    if (extensions.get("x402") or {}).get("enabled") is not False and extensions.get("x402"):
        diagnostics.append(diagnostic("BUZZ_PAYMENT_AUTHORITY_REFUSED", "refused", "extensions.x402",
                                      "Payment semantics cannot enter a static Buzz package.",
                                      "Keep payment authority in RAP; Buzz payment mode is none."))
    surfaces = []
    for path, classification in CLASSIFICATIONS.items():
        if _present(doc, path):
            blocking = classification == "unsupported" and path not in {
                "harness.memory", "harness.runtime", "harness.deployment"
            }
            surfaces.append({"path": path, "classification": classification,
                             "projectionRule": "review-metadata" if classification == "metadata-only" else "static-projection",
                             "diagnostics": [], "blocking": blocking})
    for key in sorted((extensions or {}), key=lambda x: x.encode()):
        path = f"extensions.{key}"
        if path not in CLASSIFICATIONS:
            reviewed = key in reviewed_extensions
            surfaces.append({"path": path,
                             "classification": "metadata-only" if reviewed else "unsupported",
                             "projectionRule": "namespaced-review-metadata" if reviewed else "no-projection",
                             "diagnostics": [], "blocking": not reviewed})
    diagnostics = _sort_diagnostics(diagnostics)
    for row in surfaces:
        row_diagnostics = [item["code"] for item in diagnostics
                           if item["path"] == row["path"] or item["path"].startswith(row["path"] + ".")]
        row["diagnostics"] = sorted(set(row_diagnostics))
        row["blocking"] = row["blocking"] or any(
            item["blocking"] for item in diagnostics
            if item["path"] == row["path"] or item["path"].startswith(row["path"] + ".")
        )
    eligible = not any(d["blocking"] for d in diagnostics) and not any(r["blocking"] for r in surfaces)
    safe_uri = canonical_uri
    if SENSITIVE_RE.search(canonical_uri):
        safe_uri = "urn:reddiagent:refused-sensitive-reference"
        diagnostics.append(diagnostic("BUZZ_PUBLIC_SENSITIVE_CONTENT", "refused", "canonicalAdl.uri",
                                      "Canonical reference contains secret-like content.",
                                      "Use a non-sensitive immutable canonical reference."))
        diagnostics = _sort_diagnostics(diagnostics)
        eligible = False
    identity_summary = {"verified": False}
    if not identity_diagnostics:
        identity_summary = {
            "bindingDigest": binding["bindingDigest"],
            "status": binding["status"],
            "sequence": binding["sequence"],
            "expiresAt": binding["expiresAt"],
            "proofAlgorithm": binding["ownerBindingProof"]["signatureAlgorithm"],
            "verified": True,
        }
    report = {
        "format": "reddiagent-buzz-compatibility-report", "version": "0.1",
        "canonicalAdl": {"uri": safe_uri, "apiVersion": doc.get("apiVersion") if isinstance(doc, dict) else None,
                         "digest": adl_digest, "schemaDigest": sha256(schema_bytes),
                         **({"sourceCommit": pins["sourceCommit"]} if pins.get("sourceCommit") else {})},
        "target": {"kind": "buzz-static-projection", "upstreamCommit": pins.get("upstreamCommit"),
                   "forkCommit": pins.get("forkCommit"), "adapterCommit": pins.get("adapterCommit"),
                   "contractVersion": "0.1", "evaluationTime": evaluation_time,
                   "governanceReview": (_governance_summary(drift) if not governance_diagnostics else
                                        {"valid": False, "publicDistributionAllowed": False,
                                         "publicBrandingAllowed": False})},
        "identityBinding": identity_summary, "surfaceRows": surfaces, "diagnostics": diagnostics,
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
    emitted = canonical_bytes(report) + (canonical_bytes(projection) if projection else b"")
    if SENSITIVE_RE.search(emitted.decode("utf-8")):
        projection = None
        safe_diagnostics = _sort_diagnostics(report["diagnostics"] + [diagnostic(
            "BUZZ_PUBLIC_SENSITIVE_CONTENT", "refused", "<final-output>",
            "Final public output failed the non-echo safety scan.",
            "Remove sensitive auxiliary evidence before export.")])
        # Do not return the unsafe object that triggered this last-resort scan.
        # Emit only fixed contract fields, digests, boundary flags, and already
        # value-free diagnostics so the refusal itself cannot echo the secret.
        report = {
            "format": "reddiagent-buzz-compatibility-report", "version": "0.1",
            "canonicalAdl": {"digest": adl_digest, "schemaDigest": sha256(schema_bytes)},
            "target": {"kind": "buzz-static-projection", "contractVersion": "0.1"},
            "identityBinding": {"verified": False}, "surfaceRows": [],
            "diagnostics": safe_diagnostics, "packageEligible": False,
            "canonical": False, "oneWayProjection": True,
            "canonicalSourceRequiredForRegeneration": True, "paymentMode": "none",
            **BOUNDARY_FLAGS,
        }
    return report, projection


def write_package(destination: Path, report: dict, projection: dict) -> None:
    if destination.is_symlink() or (destination.exists() and
                                    (not destination.is_dir() or any(destination.iterdir()))):
        raise ValueError("export destination must be absent or empty")
    parent = destination.parent.resolve()
    tmp = parent / f".{destination.name}.buzz-export-tmp"
    if tmp.is_symlink() or tmp.exists():
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
                    "governanceEvidence": report["target"]["governanceReview"],
                    "paymentMode": "none", **BOUNDARY_FLAGS}
        (tmp / "manifest.json").write_bytes(canonical_bytes(manifest) + b"\n")
        os.replace(tmp, destination)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        if destination_existed and not destination.exists():
            destination.mkdir()
        raise


def parity_summary(doc: dict, errors: list[str]) -> dict:
    adl_invalid = bool(errors) or doc.get("apiVersion") != "reddiagent.dev/v0.2"
    blockers = ["BUZZ_ADL_INVALID"] if adl_invalid else []
    harness = doc.get("harness", {}) or {}
    blockers.extend(item["code"] for item in _surface_diagnostics(doc) if item["blocking"])
    runtime = harness.get("runtime", {}) or {}
    if ((runtime.get("activation") or {}).get("mode") not in {None, "blocked"} or
            (runtime.get("network") or {}).get("access") not in {None, "none"}):
        blockers.append("BUZZ_RUNTIME_CAPABILITY_REFUSED")
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
    p.add_argument("--drift-review", required=True, type=Path)
    p.add_argument("--evaluation-time", required=True)
    p.add_argument("--export-package", type=Path)
    p.add_argument("--request-distribution", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        parsed = _parse_utc(args.evaluation_time)
        if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
            raise ValueError
    except ValueError:
        print("error: evaluation-time must be pinned RFC 3339 UTC", file=sys.stderr)
        return 2
    try:
        if args.identity_binding.is_symlink() or not args.identity_binding.is_file():
            raise ValueError("identity binding must be a regular non-symlink file")
        if args.drift_review.is_symlink() or not args.drift_review.is_file():
            raise ValueError("drift review must be a regular non-symlink file")
        binding = json.loads(args.identity_binding.read_text())
        drift = json.loads(args.drift_review.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: invalid deterministic evidence input: {exc}", file=sys.stderr)
        return 2
    pins = {"sourceCommit": args.source_commit, "upstreamCommit": args.upstream_commit,
            "forkCommit": args.fork_commit, "adapterCommit": args.adapter_commit}
    report, projection = build_report(
        args.single, args.canonical_uri, args.schema, pins, binding, drift,
        args.evaluation_time, args.request_distribution
    )
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
