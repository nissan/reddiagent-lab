# Gemini Target Mapping

_Loop 31. Anchor issue: #33._

## Mapping

- model.capability maps to Gemini model and modality support.
- harness.tools map to function declarations.
- dataSources may map to grounding, Google APIs, or Vertex integrations.
- runtime may map to local SDK usage or Google Cloud deployment.

## Notes

Gemini is important for multimodal and Google ecosystem workflows. Keep the ADL function contract provider-neutral, then map to Gemini declarations.

## Compatibility Risks

- Product surfaces differ between Gemini API and Vertex AI.
- Grounding/code-execution features may not port cleanly.

