# Migrating an ADL document from v0.2 to v0.3

v0.3 replaces v0.2. A v0.2 document is not valid v0.3 and there is no
compatibility mode: nothing had launched on v0.2, so the payment vocabulary
was changed outright to match what Reddi Agent Protocol V1 does on Solana.

Documents without `extensions.x402` only need the version line changed.

| v0.2 | v0.3 |
| --- | --- |
| `apiVersion: reddiagent.dev/v0.2` | `apiVersion: reddiagent.dev/v0.3` |
| `currency: USDC` on an intent or authority | `asset: { symbol, network, mint }`; `mint` is omitted only for `SOL` |
| `currency: USD`, `EUR`, `GBP` | removed; use one of `SOL`, `USDC`, `PYUSD`, `USDG`, `AUDD` |
| `rails: [x402-dry-run]` | `rail: solana` and `extensions.x402.mode: dry-run` |
| `rails: [solana, ...]` | one `rail` per intent |
| no mode | `extensions.x402.mode: dry-run` or `live` (required) |
| policy `limits.currency` / `limits.maxUsd` | `limits.asset` (the symbol) and `limits.maxAmount` |
| charge intent with only `maxAmount` | add `price: { amount, per: call }`, `payTo`, `settlement`, `requireReceipt: true`, `receiptRef`, `policyRefs`, and a matching payment policy |
| receipt ref without a format | add `format: reddi.receipt.v2` |
| no fee | `extensions.x402.protocolFee: { bps: 5, rounding: down, paidBy: provider }`, required for a live charge |

Check a migrated document with:

```bash
python3 scripts/adl_v03_conformance.py path/to/agent.yaml
```

The v0.2 spec, schema, examples and checker stay in the repository as
superseded history, as v0.1 does.
