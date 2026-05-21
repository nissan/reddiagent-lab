# Validation Error Demo

_Updated during loops 84-103. Anchor issues: #110-#130._

## Command

    /Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/validate_examples.py examples/invalid/missing-instructions.yaml

## Expected

Validation fails with builder-facing guidance, not raw JSON Schema jargon.

## Current Output

    FAIL examples/invalid/missing-instructions.yaml

    1. Missing required field: harness.instructions.
       Location: harness.instructions
       Why it matters: Instructions are the agent's operating contract: what it may do, what it should avoid, and how it should behave.
       Fix: Add harness.instructions with either inline text or a path to an instruction file.
       Minimal snippet:
         harness:
           instructions:
             inline: Summarize the supplied source and cite every claim.
       Reference: tutorials/simple-local-agent.md
    FAIL examples/invalid/bad-model-capability.yaml

    1. Unsupported value at model.capability. Allowed values: chat, reasoning, code, vision, audio, embedding, reranking.
       Location: model.capability
       Why it matters: Capability is how ReddiAgent matches an agent to compatible models without hard-coding one provider.
       Fix: Choose one supported capability: chat, reasoning, code, vision, audio, embedding, or reranking.
       Minimal snippet:
         model:
           capability: reasoning
       Reference: specs/PROVIDER-MAPPING-v0.1.md
    FAIL examples/invalid/bad-runtime-target.yaml

    1. Unsupported value at harness.runtime.target. Allowed values: local-python, hosted-container, serverless, platform-native, openclaw.
       Location: harness.runtime.target
       Why it matters: The runtime target tells runners where this harness can execute.
       Fix: Choose one supported target: local-python, hosted-container, serverless, platform-native, or openclaw.
       Minimal snippet:
         harness:
           runtime:
             target: local-python
       Reference: specs/RUNTIME-DEPLOYMENT-v0.1.md
    FAIL examples/invalid/bad-tool-id.yaml

    1. Value at harness.tools.0.id does not match the required format.
       Location: harness.tools.0.id
       Why it matters: Tools define which external capabilities the harness may expose to the model.
       Fix: Each tool needs id, type, and description.
       Minimal snippet:
         harness:
           tools:
             - id: search_docs
               type: function
               description: Search approved project docs.
       Reference: specs/TOOL-REGISTRY-v0.1.md
    FAIL examples/invalid/duplicate-fallbacks.yaml

    1. List at model.providers.fallbacks contains duplicate entries.
       Location: model.providers.fallbacks
       Why it matters: Fallbacks keep the agent portable when the preferred provider is unavailable.
       Fix: Use unique non-empty fallback provider identifiers.
       Minimal snippet:
         model:
           providers:
             preferred: openai:gpt-4.1-mini
             fallbacks:
               - anthropic:claude-3-5-haiku
       Reference: specs/PROVIDER-MAPPING-v0.1.md
    FAIL examples/invalid/bad-payment-intent.yaml

    1. List at extensions.x402.intents.0.rails needs at least 1 item.
       Location: extensions.x402.intents.0.rails
       Why it matters: Payment intents declare spend or charge boundaries before any x402-capable rail is used.
       Fix: Each intent needs id, direction, maxAmount, currency, and at least one rail.
       Minimal snippet:
         extensions:
           x402:
             enabled: true
             intents:
               - id: summarize-paid-source
                 direction: spend
                 maxAmount: "0.10"
                 currency: USDC
                 rails: [solana]
       Reference: specs/PAYMENT-REPUTATION-EXTENSION-v0.1.md

