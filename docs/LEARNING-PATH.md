# Learning Path Outline

_Loop 61. Anchor issue: #62._

## Sequence

1. What is an agent?
2. Model versus harness.
3. Simple local ADL.
4. Tool contracts.
5. Policies and eval gates.
6. Dry-run traces.
7. Provider compatibility.
8. Payment intent and dry-run receipt.
9. Reputation signals.
10. Deployment and adapters.
11. Capstone: the Vault Duel (Reddi Arena).

## Teaching Rule

Every lesson should end with a visible artifact the builder can run or inspect.

## Capstone (Lesson 11)

Hosted by the Arena proof use case rather than this repo: two ADL documents
fight a deterministic Vault match, and weight class is computed from the
declaration — the lesson is that an ADL document is a contract, not
documentation, because a bot cannot do what its ADL did not declare. It honors
the teaching rule: the builder ends with runnable artifacts (a replayable
seeded match, a leaderboard, a hireable specialist), all on the `x402-dry-run`
rail with no wallet, live rail, or provider calls.

- Tutorial: https://github.com/nissan/reddi-arena/blob/main/tutorials/vault-duel.md
- Live preview: https://reddi-arena-production.up.railway.app

