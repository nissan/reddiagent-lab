# Live MCP/Devnet Handoff Prototype Report

_Issue: #221._

## Scope

This report covers the first executable ReddiAgent MCP/devnet payment handoff prototype.

The prototype is intentionally bounded. It exercises reviewed MCP server/tool references, devnet-only payment handoff policy, receipt shape, rollback planning, and trace semantics without touching credentials, wallets, networks, payment rails, settlement, production infrastructure, or mainnet.

## Evidence

- Script: `scripts/live_mcp_devnet_handoff_prototype.py`
- Pinned fixture: `tests/fixtures/live-mcp-devnet-handoff-prototype.json`
- Test: `tests/test_live_mcp_devnet_handoff_prototype.py`
- Smoke gate: `tests/smoke-validation.sh`

## Scenarios

| Scenario | Expected result | Evidence |
|---|---:|---|
| `approved-mcp-devnet-handoff` | pass | Reviewed MCP serverRef/toolRef plus bounded simulated Solana devnet handoff emit receipt and rollback evidence. |
| `mainnet-payment-denied` | fail closed | Mainnet handoff is denied before side effects and emits no receipt. |
| `unreviewed-mcp-server-denied` | fail closed | Unallowlisted MCP serverRef is denied before invocation and emits no receipt. |

## Boundary

- Live MCP resolution/invocation is approved by policy for #221, but this validation run uses deterministic local evidence only.
- Devnet payment handoff is approved by policy for #221, but this validation run uses a simulated devnet handoff and spends zero lamports.
- Mainnet remains blocked.
- No secret, wallet, credential, raw payment proof, or raw prompt material is logged.
- Rollback/cleanup evidence is required before completion.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_live_mcp_devnet_handoff_prototype.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/live_mcp_devnet_handoff_prototype.py --output tests/fixtures/live-mcp-devnet-handoff-prototype.json
PYTHON=/Users/loki/.pyenv/versions/3.14.3/bin/python3 bash tests/smoke-validation.sh
```
