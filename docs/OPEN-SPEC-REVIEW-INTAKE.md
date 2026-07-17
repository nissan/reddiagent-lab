# ReddiAgent Open-Spec Review Intake

_Issue #227. Parent epic: #206. Repo-local intake notes; not externally published._

Use this guide when turning public-review feedback into ReddiAgent issues and PRs. The matching GitHub template is `.github/ISSUE_TEMPLATE/open-spec-review.md`.

The intake goal is to preserve useful reviewer context without collecting secrets, private production payloads, wallet keys, credentials, customer data, or live incident details.

## Submission Template

Every review record should include:

- reviewer role;
- target file, section, example, mapping, fixture, or evidence report;
- state classification: stable, experimental, report-only, executable prototype, or future work;
- concrete problem or improvement;
- suggested acceptance criteria;
- prototype/beta separation notes;
- sanitized evidence or reproduction steps;
- proposed backlog shape.

Use one primary target per issue whenever possible. If feedback spans several surfaces, open a parent issue and split follow-up issues by target.

## State Classification

Use the status vocabulary from `docs/OPEN-SPECS-EXPLAINER.md`:

| Classification | Intake meaning | Typical route |
|---|---|---|
| Stable | A canonical spec, schema, example, or validation behavior needs correction or clarification. | Small docs/spec/schema PR with focused validation. |
| Experimental | A documented but still-fluid surface needs design feedback before it hardens. | Design issue or spec PR with explicit tradeoffs. |
| Report-only | A compatibility, export, handoff, protected-docs, or readiness artifact needs correction without activating the target. | Report/test/fixture PR that keeps live access disabled. |
| Executable prototype | Feedback asks for runnable local/devnet/provider/MCP behavior or beta evidence. | Route under the #220 prototype/beta track, starting with #224 or #222 when appropriate. |
| Future work | Feedback depends on mainnet, production runtime operations, unrestricted spend, silent lossy exports, or unclear external actions. | Park with owner and approval gate; do not implement without fresh approval where required. |

Mainnet deployment and mainnet runs remain future work unless Nissan gives fresh explicit approval.

## Intake Flow

1. Confirm the issue uses the open-spec review template or has equivalent fields.
2. Check that the target file or section exists and that evidence is sanitized.
3. Classify the feedback using the state vocabulary above.
4. Decide whether the feedback is a docs-only correction or prototype/beta feedback.
5. Link the review issue to the relevant parent: #206 for docs/spec review, #220 for executable prototype or beta runtime feedback.
6. Convert accepted feedback into a focused implementation issue or PR with acceptance criteria copied from the review record.
7. Preserve the reviewer role and target surface in the PR body or issue comment so the rationale survives the handoff.
8. Close the review issue only after the follow-up issue/PR is linked, merged, or explicitly parked.

## Docs-Only Corrections

Treat feedback as docs-only when it changes wording, examples, links, status labels, schema explanation, mapping notes, or evidence report clarity without asking the repo to run a new live capability.

Docs-only corrections should:

- reference the exact file and section;
- include a before/after expectation;
- keep publication local unless Nissan approves external publishing;
- avoid introducing live runtime, provider, MCP, credential, payment, devnet, mainnet, deployment, npm, or destructive behavior;
- update tests when a navigation link, protected package, or public-review contract depends on the text.

## Prototype and Beta Feedback

Route feedback into the #220 prototype/beta track when it asks for:

- local executable ADL runtime behavior;
- provider-backed sandbox calls, budgets, or eval traces;
- live MCP server resolution or invocation;
- devnet payment handoff or settlement evidence;
- credential, wallet, facilitator, gateway, deployment, or operator runbook behavior;
- beta readiness, observability, incident response, or operator controls.

Do not mix prototype/beta feedback into a docs-only PR. Create or link a child issue under #220, and make the required approval, budget, audit evidence, and guardrails explicit before implementation.

## Safety and Privacy Boundary

Reviewers should not paste secrets, credentials, API keys, wallet keys, private prompts, customer payloads, private production logs, or live incident payloads into GitHub issues. Ask for sanitized fixtures, local reproduction steps, or redacted evidence paths instead.

This intake process does not publish docs, deploy a site, call provider APIs, invoke MCP servers, access credentials, touch wallets, run devnet/mainnet transactions, mutate production infrastructure, publish npm packages, or activate runtime services.
