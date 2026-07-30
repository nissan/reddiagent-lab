# Agent Development Process

_Adopted 2026-07-26 by maintainer direction. This is the operating contract
for all agent-executed work in this repository (and mirrored for
reddi-agent-protocol). It encodes the autonomous plan → design → build →
test → deploy pipeline._

## Roles

Agent charters live in `.claude/agents/`: firefly (planning/scenarios),
archie (research), kit (implementation), oli (review gate), sara (editorial),
quinn (synthesis), becky (cost intelligence), belle (design/UX). Use the
charter matching the work; the orchestrating session routes and integrates.

## Issue lifecycle and status

Issues carry exactly one `status:*` label at a time, updated on every
transition:

`status:product-backlog` → `status:sprint-backlog` → `status:assigned` →
`status:in-progress` → `status:in-review` → done (issue closed).

Rules:

- Before `status:in-progress`: create the work branch (see naming below).
- Issues are assigned to the human user (`reddinft`) unless a dedicated AI
  account exists; every commit made by an agent on the human's behalf states
  the agent in the commit trailer (see Attribution).
- Plan work so parallel issues touch disjoint files/areas — no two
  in-progress issues should expect merge conflicts. Note the intended file
  footprint in the issue body when parallelism matters.
- Blocked work: label `status:blocked`, comment what human-in-the-loop action
  is required, and stop — do not work around a block.

## Branches and worktrees

- Branch naming: `<type>/<hyphenated-short-title>` where type ∈
  fix | feat | docs | chore | research | spike
  (e.g. `fix/signup-fails-for-google-users`).
- All local work uses git worktrees created one level above the repo root:
  `../reddiagent-lab-worktree-01`, `-02`, … — never build directly in the
  primary checkout when parallel work is possible.

## Attribution

Commits made by an agent on behalf of the maintainer end with:

```
Committed by <agent-name> on behalf of @reddinft
Co-Authored-By: <model attribution line>
```

## Build → test → PR

- Work through the issue's acceptance criteria; test locally
  (`python3 -m pytest tests/ -q` must be green; conformance checks for any
  spec/example change).
- Open the PR referencing the issue; move the issue to `status:in-review`.

## Research lanes and citation discipline

Research reports feed spec decisions and public claims, so a wrong or invented
citation propagates into implementations and into the launch narrative. Two
consecutive reports shipped defects that only the review pass caught: PR #410
carried an H-graded negative claim contradicted by the source's own
contributing guide, and PR #412 carried a **fabricated direct quotation**
attributed verbatim to a page where it does not appear, graded as
primary-source-read.

Rules for any report using the H/M/L confidence legend:

- **No quotation, field name, version string, or value ships unless it was
  fetched and grepped in-session and seen.** An unverifiable claim is
  paraphrased with a downgraded code, or recorded as an honest Unknown.
  Unknowns are a feature; invented evidence is worse than no evidence.
- **Deep-link, don't bare-domain.** Cite the exact page or file (with a read
  date, and a byte count or hit count where it settles a negative claim) so a
  reviewer can reproduce the check.
- **Scope negative claims to what was searched.** "Absent from these three
  pages, grepped on this date" is auditable; "does not exist" is not.
- **Retract in the artifact.** When a corrective round removes a bad citation,
  name the retracted string and the mechanism that produced it, rather than
  quietly patching it.
- Prefer a different agent for the corrective pass than the one that authored
  the defect.

## Intelligent review protocol

Every open PR gets a review pass (the 20-minute review loop picks up any PR
in need of one):

1. Review as an independent reviewer (oli charter): correctness, edge cases,
   security, spec conformance, test coverage. Post findings as PR comments —
   actionable, line-cited, severity-graded. For research reports, **spot-verify
   H-graded quotations by live fetch** — plausibility is not verification — and
   check claims the report makes about this repo's own artifacts against the
   files themselves.
2. If satisfied, post a comment reading **"Ready to Approve"**. Then:
   - Convert any remaining non-blocking findings into follow-up issues,
     labeled with the project and follow-up type
     (`type:feature` | `type:improvement` | `type:fix` | `type:nitpick`),
     attached to the same epic as the source issue where applicable, and
     linked to the originating issue with the relationship stated explicitly
     (depends-on / blocks / relates-to).
   - Complete the merge (squash) and cleanup: delete the branch, close the
     issue (status → done), sync STATUS.md if the change is
     direction-bearing.
3. If not satisfied, switch to developer mode: address all findings,
   test, commit, push, and comment on the PR describing how each round of
   feedback was addressed. Repeat until "Ready to Approve" or blocked.
4. Blocked (needs credentials, approval, external action, or judgment
   reserved to the maintainer): comment the block reason, label
   `status:blocked`, and leave for human action.

## Guardrails (unchanged by this process)

Mainnet remains blocked until official audit and explicit go-live approval.
Live settlement, wallet/facilitator access, credential storage, and external
publication follow the approval state in STATUS.md. The review loop merges
code; it never activates live payment paths.
