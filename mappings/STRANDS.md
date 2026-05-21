# Strands / AWS Production Mapping

_Loop 34. Anchor issue: #36._

## Mapping

- model provider maps to Strands model/provider configuration, often AWS-friendly.
- tools map to SDK tool definitions.
- runtime/deployment may map to AWS-hosted services, containers, or Bedrock-adjacent production paths.
- observability maps to callback/tracing hooks plus ReddiAgent summary events.

## Notes

Strands is useful as a production SDK reference, especially where AWS deployment and operational constraints matter.

## Compatibility Risks

- AWS/Bedrock defaults may make portability feel secondary.
- Deployment details should stay in runtime/deployment, not core model definition.

