# Retrospective: Loops 229-253 - Source-Check Guidance

Date: 2026-05-23  
Anchor issue: #131

## Shipped

- Added `source_check_guidance.py` for builder-facing source-policy repair guidance.
- Failed source checks now include `guidance` with problem, safety rationale, fix, minimal snippet, and data-source contract reference.
- Kept passing source checks compact, with no guidance payload.
- Kept `source.checked` trace events compact; guidance belongs in `sourceChecks`, not trace events.
- Updated tests and specs for the guidance contract.

## Validation

- `python3 tests/test_tool_execution.py`

Full suite was run after STATUS and memory updates for this batch.

## Decision

Source-check failures should be repairable without weakening the safety boundary. The runner now tells builders how to return approved in-repo evidence or add a reviewed source, while still avoiding real external tools, network retrieval, MCP, HTTP, shell, credentials, messaging, and live payments.

## Next

Add explicit source-check failure counting and completion semantics, so a failed required source gate can be distinguished from a successful dry-run transport.
