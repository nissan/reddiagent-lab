# Runtime and Deployment v0.1

_Loop 15. Anchor issue: #16._

## Runtime Targets

| Target | Use case | Notes |
|---|---|---|
| local-python | learning, local prototypes | Best first target for prosumers |
| hosted-container | production preview | Portable and inspectable |
| serverless | short bounded tasks | Good for paid specialist tasks |
| platform-native | OpenAI/Bedrock/Gemini/etc | Useful when hosted tools are required |
| openclaw | advanced orchestration | Useful for skills, memory, subagents, channels |

## Deployment Descriptor

Deployment should describe:

- target
- resource limits
- secret references
- network permissions
- storage/memory persistence
- scheduler/event trigger
- observability sink
- rollback strategy

## Compatibility Rule

Runtime adapters must report unsupported features before execution.

