# REASONS-LITE — Deterministic report-only ADL to Buzz exporter

_Status: draft | Owner: Loki on behalf of Nissan | Project: reddiagent-lab | Issue: [#425](https://github.com/reddinft/reddiagent-lab/issues/425) | Normative contract: `specs/BUZZ-ADAPTER-CONTRACT-v0.1.md`_

SPDD-LITE is required because this exporter crosses public-content, identity,
policy, payment-authority, packaging, and future install boundaries. This file
is the implementation update plan. The implementation must update this artifact
in the same PR if its files, data contract, or safeguards materially diverge.

## R — Requirements / Definition of Done

Build a deterministic, local, report-first exporter from validated canonical
ADL v0.2 to an optional static Buzz projection. ADL remains canonical, the Buzz
output is disposable and one-way, and RAP remains the sole payment/receipt/
reputation authority described by the #424 contract.

**DoD checklist:**

- [ ] Add `buzz-static-projection` to the existing static export-target parity
  matrix; do not introduce a parallel classification vocabulary.
- [ ] Emit a machine-readable compatibility report for valid, lossy,
  unsupported, and refused inputs using only #424's five classifications and
  stable `BUZZ_*` diagnostics.
- [ ] Bind the exact canonical ADL URI, API version, source-byte SHA-256, schema
  SHA-256, repository source commit when applicable, full Buzz upstream/fork
  pins, full adapter commit, and contract version.
- [ ] Produce byte-identical JSON and package files for identical source bytes,
  pins, reviewed auxiliary files, and caller inputs. JSON uses UTF-8, RFC 8785
  canonicalization for digest preimages, lowercase hexadecimal SHA-256, sorted
  paths, and no unpinned wall-clock data.
- [ ] Project only reviewed public-safe persona instructions plus explicitly
  allowed static model/provider/tool/skill/package metadata. Preserve every
  semantic loss and metadata-only limitation in the report and package.
- [ ] Refuse invalid ADL, secrets or public-sensitive content, unsafe paths,
  unresolved policy references, executable/runtime semantics, embedded spend
  authority, misleading payment/reputation claims, invalid identity joins,
  invalid pins, and Buzz-to-ADL/round-trip requests.
- [ ] Keep every G1 boundary flag false in reports, parity rows, manifests,
  positive fixtures, negative fixtures, and rendered evidence.
- [ ] Inherit the #424 attribution/branding hold explicitly: every report,
  parity row, manifest, package metadata object, and fixture sets
  `publicDistributionAllowed=false` and `publicBrandingAllowed=false`; any
  distribution request refuses with `BUZZ_ATTRIBUTION_REVIEW_REQUIRED` until
  the required license/NOTICE/modified-file/branding review is complete.
- [ ] Prove the Buzz artifact cannot be imported or represented as reconstructing
  canonical ADL.
- [ ] Pass focused exporter/parity tests, deterministic snapshots, negative
  fixtures, `git diff --check`, full deterministic smoke, and exact-head Oli QA.

Out of scope: Buzz source changes; Buzz install, runtime, relay, or agent start;
provider/model calls; credential lookup; tool/MCP execution; wallet, RPC,
payment, settlement, or delegated spend; public distribution; deployment;
localnet, devnet, or mainnet; and work on #426 or later.

## E — Entities / Handoff Objects

| Entity / object | Purpose | Required fields / invariants |
|---|---|---|
| Canonical ADL input | Sole agent-definition authority | Exact source bytes, repository-relative or stable URI, `reddiagent.dev/v0.2`, validated schema, optional reviewed source root |
| Export request | Caller-controlled deterministic pins | Full upstream/fork/adapter commits, contract version, reviewed identity-binding evidence, optional pinned `generatedAt`; no ambient discovery |
| Compatibility report | Complete decision and loss evidence | `format`, version, canonical pins, target pins, identity result, ordered surface rows, ordered diagnostics, package eligibility, boundary flags |
| Surface row | One #424 matrix decision | ADL path, exactly one primary classification, projection rule, diagnostics, blocking state; complete coverage without inferred semantics |
| Diagnostic | Stable fail-closed reason | #424 code, classification, severity, path, message, remediation, `blocking`; sorted by path, severity rank, code |
| Projection package | Optional static non-canonical output | Public-safe persona/listing, reviewed static assets, report file/digest, provenance manifest, explicit `oneWay=true` and `canonical=false` |
| Artifact manifest | Deterministic inventory | Relative path, lowercase SHA-256, byte length, media type, source/report relationship; bytewise path ordering |
| Parity row | Existing matrix integration | Target id `buzz-static-projection`, report command, strict export command, authoritative check, readiness/loss/blockers, all existing false boundary flags, `publicDistributionAllowed=false`, `publicBrandingAllowed=false` |

The report is always the first output. A projection package may be written only
when the report is valid and contains no `refused` row, no blocking
`unsupported` row, and no invalid/stale/expired/revoked identity or pin result.
Report-only failures return a deterministic non-zero exit code after writing the
report to stdout; they must not leave a partial package directory.

## A — Approach / Key Decisions

### Command and output contract

Add a local CLI with separate report and package modes:

```text
python3 scripts/buzz_export.py --single <adl> --canonical-uri <uri> \
  --schema specs/ADL-v0.2.schema.json --upstream-commit <40-hex> \
  --fork-commit <40-hex> --adapter-commit <40-hex> \
  --identity-binding <json>

python3 scripts/buzz_export.py ... --export-package <empty-output-dir>
```

The CLI must not fetch commits, resolve network identities, inspect ambient
credentials, start a runtime, or infer pins from mutable branch names. Tests may
pass the exact checked-out adapter commit explicitly. Package mode accepts only
an absent or empty destination directory and writes through a temporary sibling
before an atomic rename, so refusals cannot leave a plausible partial artifact.

### Determinism

- Digest canonical ADL **source bytes** exactly as required by #424; do not
  parse-and-reserialize them for `canonicalAdl.digest`.
- Digest reports and manifest preimages using RFC 8785/JCS with digest fields
  excluded from their own preimages and the exclusion named in the schema/test.
- Serialize published JSON as canonical UTF-8 with a final newline. Sort file
  inventory by UTF-8 relative-path bytes and diagnostics by #424's order.
- Normalize no source content silently. Reject non-regular files, symlinks,
  root escapes, duplicate normalized paths, and unsupported encodings.
- Omit `generatedAt` unless the caller provides a valid pinned RFC 3339 UTC
  instant; the value then participates in the digest.
- Never include absolute host paths, temporary paths, usernames, environment
  values, process ids, filesystem mtimes, or unordered collection iteration.

### Safe projection allowlist

The package allowlist is intentionally narrow:

- reviewed display name and description;
- reviewed public-safe inline instructions, or bytes from one in-root regular
  instruction file with its original relative path and digest;
- model capability/provider identifiers only as advisory metadata;
- tool/function/skill identifiers, descriptions, input schemas, permissions,
  and resolved policy references only as non-executable review metadata;
- packaging/license/provenance fields required by #424.

Memory content, datasource contents, credential material, wallet/RPC/rail data,
host paths, executable hooks, dynamic imports, provider configuration, tool/MCP
endpoints, and runtime/deployment instructions are never package payloads.

### Refusal and one-way rules

Reuse every normative #424 `BUZZ_*` code and emit all applicable codes. A
secret/public-sensitive scanner is a conservative deterministic denylist plus
explicit source annotations; it is a safety gate, not a claim of exhaustive
secret detection. Fixtures must cover compound failures to prove codes are not
collapsed.

The package manifest must state:

```json
{
  "canonical": false,
  "oneWayProjection": true,
  "bidirectionalImportAllowed": false,
  "canonicalSourceRequiredForRegeneration": true
}
```

The compatibility report, parity row, artifact manifest, and package metadata
must additionally state `publicDistributionAllowed=false` and
`publicBrandingAllowed=false`. Package creation is local evidence generation,
not authorization to distribute or brand it publicly. A caller request for
distribution must be refused with `BUZZ_ATTRIBUTION_REVIEW_REQUIRED`; it cannot
be downgraded to a warning or cleared by a CLI flag.

No parser/import command for Buzz packages is added. Tests must assert the CLI
has no reverse/import mode and that package content lacks enough authority to
claim lossless ADL reconstruction.

Rejected alternatives: a new compatibility framework, silent best-effort
mapping, mutable/default target pins, automatic git/network pin discovery,
round-trip serialization, exporting memory or secrets after redaction, and
writing a package before validation finishes.

## S — Structure / Files Touched

| Surface | Planned change |
|---|---|
| `spdd/prompt/0425-buzz-exporter.md` | This accepted implementation plan and prompt/code sync log |
| `scripts/prosumer_builder_plan.py` | Add `buzz-static-projection` to canonical `EXPORT_MATRIX_TARGETS`; keep `BOUNDARY_FLAGS` authoritative and populate each agent row from deterministic exporter summary fields without adding a second target or boundary registry |
| `scripts/static_export_target_parity.py` | Add the Buzz target by consuming exporter report summaries |
| `scripts/buzz_export.py` | Deterministic report-first CLI and optional static package writer |
| `tests/test_buzz_export.py` | Focused report, package, determinism, refusal, pins, path safety, identity, and one-way tests |
| `tests/test_static_export_target_parity.py` | Assert Buzz target ordering, readiness, diagnostics, and false boundaries |
| `tests/fixtures/buzz-*.yaml` / `tests/fixtures/buzz-*.json` | Minimal valid/lossy/unsupported/refused/compound/tampered/stale cases and snapshots, including an unreviewed-attribution distribution request refused with `BUZZ_ATTRIBUTION_REVIEW_REQUIRED` |
| `tests/fixtures/static-export-target-parity-matrix.json` | Regenerated existing parity fixture with the new target |
| `tests/STATIC-EXPORT-TARGET-PARITY-MATRIX-REPORT.md` | Regenerated deterministic human-readable parity evidence if the existing generator owns it |
| `tests/smoke-validation.sh` | Add focused exporter/parity checks to the deterministic smoke suite |

No Buzz repository or source file is modified.

## O — Operations / Ordered Tasks

1. Merge and accept this #425 plan/spec PR before implementation.
2. Add fixture builders and deterministic canonical/digest helpers local to the
   exporter unless an existing helper has exactly the required contract.
3. Implement report mode with complete #424 surface-row coverage and stable
   all-applicable diagnostics before allowing any package write.
4. Add positive, lossy, unsupported, and compound-refusal fixtures; prove exact
   repeated output bytes and no partial package on failure.
5. Add the `buzz-static-projection` target to canonical
   `scripts/prosumer_builder_plan.py` `EXPORT_MATRIX_TARGETS`, preserve its
   `BOUNDARY_FLAGS` as the sole boundary registry, feed deterministic exporter
   summaries into its per-agent row construction, and let
   `scripts/static_export_target_parity.py` consume those canonical rows before
   regenerating the owned fixture/report.
6. Implement the allowlisted package only for eligible reports; bind its report
   digest and deterministic manifest.
7. Run focused validation, then full smoke. Update this plan for any material
   divergence and request exact-head Oli QA.
8. Merge only after local checks, GitHub Actions, review/request/thread
   freshness, and current-head Oli PASS are all green.

## N — Norms

- Canonical ADL is the sole source of truth; Buzz output is optional and
  disposable.
- Report every semantic loss and refusal; never infer missing authority.
- Extend the existing parity matrix and boundary flags.
- RAP keeps mandate, rail, receipt, dispute/refund, accounting-acceptance, and
  reputation authority.
- Static metadata never becomes runtime permission, provider configuration,
  tool enablement, wallet attachment, or payment authority.
- Keep G1 local/static/deterministic. Issue existence never authorizes #428 or
  any runtime action.

## S — Safeguards / Acceptance Checklist

- [ ] All reports, parity rows, fixtures, manifests, and package metadata set
  runtime/network/relay/provider/credential/tool/MCP/payment/wallet/deployment/
  bidirectional-import flags to false where the #424 contract defines them.
- [ ] All reports, parity rows, fixtures, manifests, and package metadata set
  `publicDistributionAllowed=false` and `publicBrandingAllowed=false`; a
  dedicated negative fixture/test requests distribution before attribution and
  branding review and asserts blocking `BUZZ_ATTRIBUTION_REVIEW_REQUIRED`, a
  non-zero exit, and no package or partial temporary directory.
- [ ] Invalid ADL or missing/mutable/mismatched pins emits deterministic blocking
  diagnostics and no package.
- [ ] Out-of-root, symlink, non-regular, unreadable, sensitive, duplicate, or
  unsafe package paths fail closed.
- [ ] Unresolved policies, executable semantics, ambient credential/provider
  behavior, wallet/payment authority, and false receipt/reputation claims fail
  closed with all applicable stable codes.
- [ ] Expired, revoked, stale, ambiguous, or mismatched identity bindings block
  package emission; lifecycle status is derived exactly as #424 specifies.
- [ ] Two clean runs with the same source bytes and explicit inputs produce
  identical stdout, package file bytes, manifest order, and digests.
- [ ] A changed source byte, auxiliary file byte, schema, identity evidence, or
  pin changes the bound digest or refuses the export.
- [ ] Refusal tests prove no destination or partial temporary directory remains.
- [ ] CLI help and tests expose no reverse/import/round-trip operation.
- [ ] Planned validation commands:

  ```text
  python3 tests/test_buzz_export.py
  python3 tests/test_static_export_target_parity.py
  python3 -m py_compile scripts/buzz_export.py scripts/prosumer_builder_plan.py scripts/static_export_target_parity.py tests/test_buzz_export.py tests/test_static_export_target_parity.py
  git diff --check origin/main...HEAD
  PYTHON=<pinned-python> bash tests/smoke-validation.sh
  ```

- [ ] Current-head Oli review covers #425 acceptance, the #424 contract, failure
  atomicity, deterministic outputs, and every denied G1 boundary before merge.

## Prompt/Code Sync Log

| Date | Divergence | Artifact update | Code/test update |
|---|---|---|---|
| 2026-07-31 | Initial #425 implementation plan; no exporter implementation | Created | Deferred until this plan is accepted |
| 2026-07-31 | Oli exact-head QA found omitted canonical parity ownership and an implicit attribution/branding hold | Added `scripts/prosumer_builder_plan.py` ownership/row flow plus explicit false distribution/branding invariants and refusal fixture/test | Deferred until this plan is accepted |
| 2026-07-31 | Implementation keeps RFC-8785-compatible canonical JSON local to the exporter and adds the full G1 false-boundary registry to the existing parity owner | No material scope change | Added report/package CLI, focused fixtures/tests, canonical parity target/summary, and smoke wiring |
