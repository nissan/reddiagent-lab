# Conformance Checklist v0.1

_Loop 18. Anchor issue: #19._

## Goal

Before implementation, define what a ReddiAgent validator or adapter must prove.

## Checklist

- [ ] Required ADL fields exist.
- [ ] Model requirements are valid.
- [ ] Provider mapping is possible or incompatibility is reported.
- [ ] Tool schemas are typed.
- [ ] Secret values are not embedded.
- [ ] Policies cover every risky capability.
- [ ] Payment extension has a budget policy when enabled.
- [ ] Required eval gates are known.
- [ ] Runtime target is known.
- [ ] Unsupported runtime features are reported before execution.
- [ ] Receipt requirements are enforceable if enabled.
- [ ] Observability minimum events are configured.

## Conformance Levels

- Level 0: schema-valid.
- Level 1: local-python runnable.
- Level 2: provider-adapter compatible.
- Level 3: payment/reputation extension compatible.
- Level 4: production deployment compatible.

