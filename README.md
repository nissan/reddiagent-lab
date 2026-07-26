# ReddiAgent Lab

ReddiAgent Lab is the home of **ADL — the Agent Definition Language** — and its
companion open specifications for defining AI agents portably: one definition
that describes the model envelope, the operating harness, and (optionally) the
payment/reputation extension, independent of any single provider or framework.

## Core Thesis

An agent can be modeled as:

    Agent = model definition + harness definition + settlement/reputation extension

The model definition makes OpenAI, Anthropic, Gemini, Ollama, hosted open
models, and future providers interchangeable at the capability and constraint
layer. The harness definition describes the operating system around the model:
tools, skills, memory, data sources, policies, eval gates, deployment,
observability, and recovery behavior. The extension layer carries payment
intent, delegated authority, receipts, and reputation metadata — kept separate
so the protocol layers stay distinct: x402 records payment proof, AP2/FIDO
records delegated authority, MCP records protected-resource access, Solana
records settlement proof, and RAP binds receipts/accounting/reputation above
the rail.

## What ADL looks like

```yaml
apiVersion: reddiagent.dev/v0.2
kind: Agent
metadata:
  name: simple-research-helper
  description: Answers a user question using only model reasoning and a session log.
model:
  capability: chat
  providers:
    preferred: openai
    fallbacks: [anthropic, gemini, ollama]
  requirements:
    toolCalling: false
    structuredOutput: true
harness:
  instructions:
    inline: "Answer clearly. Say when you are uncertain. Do not use external tools."
  memory:
    mode: session
  policies:
    - id: no-external-actions
      capability: network
      subject: agent
      resource: external-network
      action: connect
      effect: deny
      scope: { type: task }
      enforcement: { target: static-validator, phase: compatibility }
  evalGates:
    - id: has-answer
      type: output-check
      rule: "Response must include an answer or a clear uncertainty statement."
      required: true
      # ... evidence contract elided; see examples/v0.2/simple-agent.yaml
  runtime:
    target: local-python
extensions: {}
```

## Canonical spec

- **[specs/ADL-v0.2.md](specs/ADL-v0.2.md)** — the canonical specification
- **[specs/ADL-v0.2.schema.json](specs/ADL-v0.2.schema.json)** — the machine-checked schema
- [examples/v0.2/](examples/v0.2/) — validated examples; [examples/invalid/](examples/invalid/) — negative fixtures a correct validator must reject
- ADL v0.1 is superseded; see [docs/ADL-v0.1-to-v0.2-MIGRATION.md](docs/ADL-v0.1-to-v0.2-MIGRATION.md)

## Reading path

1. [docs/OPEN-SPECS-EXPLAINER.md](docs/OPEN-SPECS-EXPLAINER.md) — map of every spec, with a shared status vocabulary (stable / experimental / report-only / executable prototype / future work)
2. [docs/REDDIAGENT-ARCHITECTURE.md](docs/REDDIAGENT-ARCHITECTURE.md) — the system view
3. [docs/REDDIAGENT-VISION-ROADMAP.md](docs/REDDIAGENT-VISION-ROADMAP.md) and [docs/ROADMAP.md](docs/ROADMAP.md) — where this is going
4. [docs/adr/0000-adr-index.md](docs/adr/0000-adr-index.md) — durable architectural decisions
5. Draft announcement: docs/blog/2026-07-18-reddiagent-open-specs-call-for-review.md

## Giving feedback

Structured review intake lives at `docs/OPEN-SPEC-REVIEW-INTAKE.md`, with the
issue template at `.github/ISSUE_TEMPLATE/open-spec-review.md`. Implementation
reports — you tried to build against ADL and hit friction — are the most
valuable feedback of all. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Two repos, two roles

- **ReddiAgent Lab (this repo)** — the open spec home: ADL, companion specs,
  deterministic validation tooling, and compatibility reports. Audience: agent
  framework and platform builders. Stewarded by the maintainer today, with the
  explicit goal of community governance as the contributor base forms.
- **Reddi Agent Protocol** — the implementation and proof repo: payment,
  reputation, settlement, and protocol-level economic coordination on Solana
  (x402 escrow, receipts, reputation). Audience: Solana and payments builders.
  It consumes ADL; the spec is validated by what that repo proves against real
  rails.

The current posture is substance-first: proof implementations validate the
spec before we ask the community to invest in reviewing it. Live settlement
and mainnet remain blocked behind external audit and explicit go-live
approval.

## Local Validation

Requires Python 3.12+ with `pyyaml` and `jsonschema`:

    python3 scripts/validate_examples.py                                  # v0.1 example set (legacy)
    python3 scripts/adl_v02_conformance.py examples/v0.2/simple-agent.yaml  # v0.2 conformance
    python3 -m pytest tests/ -q                                           # full suite

Validation failures default to builder-facing guidance. Use `--format raw` for
schema-debug output or `--format json` for UI/CI integration.

## Repo Operating Model

- GitHub issues are the source of truth for planned work.
- STATUS.md is an internal operations resume log, not a documentation entrypoint.
- Research notes live in research/; spec artifacts in specs/ and docs/.
- RAP-specific implementation stays in the Reddi Agent Protocol repo unless the
  work belongs to the agent definition/harness abstraction.

## License

Code is licensed under [Apache-2.0](LICENSE); specifications and documentation
under [CC BY 4.0](LICENSE-SPECS.md).
