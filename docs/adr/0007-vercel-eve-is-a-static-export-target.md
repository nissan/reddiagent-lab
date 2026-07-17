# ADR 0007: Vercel Eve Is a Static Export Target

## Status

Accepted.

## Context

Vercel eve can influence how builders think about app generation and static output, but ReddiAgent's source of truth remains ADL and its harness semantics. Recent eve compatibility work treats eve as a static/export and UI-safe compatibility surface, not a runtime replacement for ADL.

Relevant references:

- `research/2026-07-17-vercel-eve-impact.md`
- `tests/EVE-COMPATIBILITY-REPORT.md`
- `tests/STATIC-EXPORT-TARGET-PARITY-MATRIX-REPORT.md`
- `docs/PROSUMER-MVP.md`
- `docs/prosumer-builder-static-export.html`
- `scripts/eve_compatibility.py`
- `scripts/static_export_target_parity.py`

## Decision

Vercel eve is a static/export target, not an ADL replacement.

ReddiAgent may use eve-oriented compatibility summaries, static export parity reports, and builder-facing guidance to explain what could be represented for eve-like targets. ADL remains canonical.

## Consequences

- Eve compatibility summaries should be derived from ADL and deterministic reports.
- Generated project writes, dependency installs, dev servers, and eve runtime execution are out of scope unless a future issue explicitly approves them.
- UI-safe summaries should separate supported, warning, and blocked semantics without hiding loss.
- Vercel eve work should improve builder understanding of export targets without weakening ReddiAgent's harness-first model.
