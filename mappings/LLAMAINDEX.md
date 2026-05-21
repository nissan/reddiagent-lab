# LlamaIndex Data-Source Mapping

_Loop 33. Anchor issue: #35._

## Mapping

- dataSources map to indexes, readers, retrievers, and query engines.
- tools can wrap query engines.
- memory can remain harness-owned unless LlamaIndex memory is explicitly configured.
- eval gates can check source/citation presence and retrieval constraints.

## Notes

LlamaIndex is the strongest reference for data-aware agents. ReddiAgent should make dataSources explicit so retrieval is not hidden inside prompt code.

## Compatibility Risks

- RAG-specific concepts can dominate the agent model.
- Index persistence/versioning needs explicit metadata.

