# Contributing to ReddiAgent Lab

Thanks for your interest. This repository is the home of ADL (the Agent
Definition Language) and its companion open specifications. It is currently
stewarded by the project maintainer, with the explicit goal of transitioning to
community governance as a contributor base forms — the spec's future should not
be dictated by one vendor or one person.

## What kind of contribution fits here

- **Spec review and feedback** — the highest-value contribution today. Use the
  structured intake in `docs/OPEN-SPEC-REVIEW-INTAKE.md` and the
  `.github/ISSUE_TEMPLATE/open-spec-review.md` issue template. Feedback against
  the canonical spec (`specs/ADL-v0.2.md` + `specs/ADL-v0.2.schema.json`)
  is preferred; v0.1 is superseded.
- **Implementation reports** — you tried to implement ADL (a validator, an
  exporter, a runtime mapping) and hit friction, ambiguity, or a gap. Open an
  issue describing what you built and where the spec failed you. These reports
  drive spec iteration more than opinions do.
- **Examples and negative fixtures** — new agent definitions under
  `examples/v0.2/`, or invalid documents under `examples/invalid/` that a
  correct validator must reject.
- **Tooling fixes** — the validators, conformance checks, and compatibility
  reporters under `scripts/`.

Payment-protocol and Solana implementation work belongs in the companion
implementation repo (Reddi Agent Protocol), not here. This repo defines the
agent-definition layer; the protocol repo proves it against real rails.

## Ground rules

- Every artifact in this repo carries a status from the shared vocabulary
  defined in `docs/OPEN-SPECS-EXPLAINER.md`: **stable**, **experimental**,
  **report-only**, **executable prototype**, or **future work**. Don't claim a
  higher status than the evidence supports.
- Changes to `specs/ADL-v0.2.md` or the schema require: updated examples,
  updated negative fixtures where behavior is newly rejected, a
  `docs/SCHEMA-CHANGELOG.md` entry, and green validation.
- Work through pull requests from feature branches. Direct pushes to `main`
  are reserved for status/index syncs by maintainers.

## Running validation locally

Requires Python 3.12+ with `pyyaml` and `jsonschema`.

```bash
python3 scripts/validate_examples.py                                    # v0.1 example set (legacy)
python3 scripts/adl_v02_conformance.py examples/v0.2/simple-agent.yaml  # v0.2 conformance
python3 -m pytest tests/ -q                                             # full test suite
```

## Licensing of contributions

By contributing you agree that code contributions are licensed under
Apache-2.0 (see `LICENSE`) and specification/documentation contributions under
CC BY 4.0 (see `LICENSE-SPECS.md`).
