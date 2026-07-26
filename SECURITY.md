# Security Policy

## Reporting a vulnerability

Please report security issues privately via
[GitHub Security Advisories](https://github.com/reddinft/reddiagent-lab/security/advisories/new)
rather than public issues. You should receive an acknowledgment within a few
days.

## Scope

This repository contains specifications, schemas, deterministic validation
tooling, and fixtures. It runs no services, holds no credentials, and performs
no network, wallet, or payment operations. Reports we care about here include:

- **Spec-level security flaws** — anything in `specs/ADL-v0.2.md` (permission
  policy model, payment authority contract, source boundaries, eval gates)
  that would let a conforming implementation authorize an action its author
  did not intend: policy-binding bypasses, authority-scope ambiguity, replay
  or receipt-substitution weaknesses in the x402/RAP evidence model.
- **Validator soundness** — inputs that the schema or conformance tooling
  accepts but the spec text forbids (or vice versa), especially where the gap
  weakens a fail-closed guarantee.
- **Fixture/report integrity** — ways the deterministic evidence chain could
  be made to assert something untrue.

Vulnerabilities in live payment execution, smart contracts, or the Solana
programs belong to the companion implementation repository (Reddi Agent
Protocol); if you report one here we will route it there.

## Supported versions

Only the current canonical spec line (ADL v0.2) receives security-relevant
revisions. ADL v0.1 is superseded and will not be patched.
