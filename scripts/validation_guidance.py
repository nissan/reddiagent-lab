"""Builder-facing guidance for ReddiAgent ADL validation errors."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Iterable

from jsonschema.exceptions import ValidationError


@dataclass(frozen=True)
class Guidance:
    """A normalized validation message intended for agent builders."""

    location: str
    problem: str
    why_it_matters: str
    fix: str
    snippet: str
    reference: str
    raw_message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


FALLBACK_SNIPPET = """apiVersion: reddiagent.dev/v0.1
kind: Agent
metadata:
  name: example-agent
  description: Describe what this agent does.
model:
  capability: chat
  providers:
    preferred: openai:gpt-4.1-mini
  requirements: {}
harness:
  instructions:
    inline: Describe the agent's job and boundaries.
  runtime:
    target: local-python"""


GUIDANCE_BY_LOCATION: dict[str, dict[str, str]] = {
    "apiVersion": {
        "why": "The API version tells validators which ADL contract to apply.",
        "fix": "Set apiVersion to the supported v0.1 value.",
        "snippet": "apiVersion: reddiagent.dev/v0.1",
        "reference": "specs/ADL-v0.1.md",
    },
    "kind": {
        "why": "The kind lets tooling distinguish agent definitions from future harness, skill, or deployment documents.",
        "fix": "Set kind to Agent.",
        "snippet": "kind: Agent",
        "reference": "specs/ADL-v0.1.md",
    },
    "metadata.name": {
        "why": "The name becomes the stable local identifier used by traces, snapshots, registries, and deployment descriptors.",
        "fix": "Use lowercase letters, numbers, and hyphens, starting with a letter or number.",
        "snippet": "metadata:\n  name: research-assistant",
        "reference": "docs/GLOSSARY.md",
    },
    "metadata.description": {
        "why": "The description is the first human-readable explanation of what the agent is for.",
        "fix": "Add a short non-empty description.",
        "snippet": "metadata:\n  description: Summarizes trusted research sources for a builder.",
        "reference": "docs/BUILDER-JOURNEY.md",
    },
    "model.capability": {
        "why": "Capability is how ReddiAgent matches an agent to compatible models without hard-coding one provider.",
        "fix": "Choose one supported capability: chat, reasoning, code, vision, audio, embedding, or reranking.",
        "snippet": "model:\n  capability: reasoning",
        "reference": "specs/PROVIDER-MAPPING-v0.1.md",
    },
    "model.providers.preferred": {
        "why": "The preferred provider is the first model route attempted by a runner or compatibility report.",
        "fix": "Set a non-empty provider identifier.",
        "snippet": "model:\n  providers:\n    preferred: openai:gpt-4.1-mini",
        "reference": "specs/PROVIDER-COMPATIBILITY-REPORT-v0.1.md",
    },
    "model.providers.fallbacks": {
        "why": "Fallbacks keep the agent portable when the preferred provider is unavailable.",
        "fix": "Use unique non-empty fallback provider identifiers.",
        "snippet": "model:\n  providers:\n    preferred: openai:gpt-4.1-mini\n    fallbacks:\n      - anthropic:claude-3-5-haiku",
        "reference": "specs/PROVIDER-MAPPING-v0.1.md",
    },
    "harness.instructions": {
        "why": "Instructions are the agent's operating contract: what it may do, what it should avoid, and how it should behave.",
        "fix": "Add harness.instructions with either inline text or a path to an instruction file.",
        "snippet": "harness:\n  instructions:\n    inline: Summarize the supplied source and cite every claim.",
        "reference": "tutorials/simple-local-agent.md",
    },
    "harness.instructions.inline": {
        "why": "Inline instructions must contain the actual operating guidance for the agent.",
        "fix": "Provide non-empty instruction text.",
        "snippet": "harness:\n  instructions:\n    inline: Answer only from the supplied source text.",
        "reference": "tutorials/simple-local-agent.md",
    },
    "harness.instructions.path": {
        "why": "Instruction paths let larger agents keep policy and behavior text outside the ADL file.",
        "fix": "Provide a non-empty path to an instruction file.",
        "snippet": "harness:\n  instructions:\n    path: ./instructions/research-assistant.md",
        "reference": "specs/HARNESS-LIFECYCLE-v0.1.md",
    },
    "harness.runtime.target": {
        "why": "The runtime target tells runners where this harness can execute.",
        "fix": "Choose one supported target: local-python, hosted-container, serverless, platform-native, or openclaw.",
        "snippet": "harness:\n  runtime:\n    target: local-python",
        "reference": "specs/RUNTIME-DEPLOYMENT-v0.1.md",
    },
    "harness.tools": {
        "why": "Tools define which external capabilities the harness may expose to the model.",
        "fix": "Each tool needs id, type, and description.",
        "snippet": "harness:\n  tools:\n    - id: search_docs\n      type: function\n      description: Search approved project docs.",
        "reference": "specs/TOOL-REGISTRY-v0.1.md",
    },
    "harness.policies": {
        "why": "Policies are the guardrails that make the harness safe to run repeatedly.",
        "fix": "Each policy needs id, type, and rule.",
        "snippet": "harness:\n  policies:\n    - id: no-network\n      type: network\n      rule: Block external network access unless explicitly approved.",
        "reference": "specs/SECURITY-PERMISSIONS-v0.1.md",
    },
    "harness.evalGates": {
        "why": "Eval gates define the checks an output must pass before it is considered acceptable.",
        "fix": "Each eval gate needs id, type, and rule.",
        "snippet": "harness:\n  evalGates:\n    - id: cites-sources\n      type: source-check\n      rule: Every factual claim must cite a source.",
        "reference": "specs/EVAL-GATES-v0.1.md",
    },
    "extensions.x402.intents": {
        "why": "Payment intents declare spend or charge boundaries before any x402-capable rail is used.",
        "fix": "Each intent needs id, direction, maxAmount, currency, and at least one rail.",
        "snippet": "extensions:\n  x402:\n    enabled: true\n    intents:\n      - id: summarize-paid-source\n        direction: spend\n        maxAmount: \"0.10\"\n        currency: USDC\n        rails: [solana]",
        "reference": "specs/PAYMENT-REPUTATION-EXTENSION-v0.1.md",
    },
}


def path_to_string(path: Iterable[Any]) -> str:
    parts = [str(part) for part in path]
    return ".".join(parts) if parts else "<root>"


def _missing_required_location(error: ValidationError) -> str | None:
    if error.validator != "required":
        return None
    match = re.match(r"'([^']+)' is a required property", error.message)
    if not match:
        return None
    parent = path_to_string(error.path)
    child = match.group(1)
    return child if parent == "<root>" else f"{parent}.{child}"


def _normalize_location(error: ValidationError) -> str:
    missing = _missing_required_location(error)
    if missing:
        return missing

    path = path_to_string(error.path)
    if path != "<root>":
        return path

    if error.validator == "oneOf" and list(error.schema_path)[-2:] == ["instructions", "oneOf"]:
        return "harness.instructions"

    return "<root>"


def _guidance_template(location: str) -> dict[str, str]:
    candidates = [location]
    if "." in location:
        parts = location.split(".")
        candidates.extend(".".join(parts[:index]) for index in range(len(parts) - 1, 0, -1))

    for candidate in candidates:
        if candidate in GUIDANCE_BY_LOCATION:
            return GUIDANCE_BY_LOCATION[candidate]

    return {
        "why": "The ADL file must match the v0.1 contract before a runner can execute it safely.",
        "fix": "Compare this section with the minimal valid ADL structure and adjust the field.",
        "snippet": FALLBACK_SNIPPET,
        "reference": "specs/ADL-v0.1.md",
    }


def _problem(error: ValidationError, location: str) -> str:
    if error.validator == "required":
        return f"Missing required field: {location}."
    if error.validator == "enum":
        allowed = ", ".join(str(value) for value in error.validator_value)
        return f"Unsupported value at {location}. Allowed values: {allowed}."
    if error.validator == "const":
        return f"Unsupported value at {location}. Expected {error.validator_value!r}."
    if error.validator == "pattern":
        return f"Value at {location} does not match the required format."
    if error.validator == "minLength":
        return f"Value at {location} cannot be empty."
    if error.validator == "uniqueItems":
        return f"List at {location} contains duplicate entries."
    if error.validator == "minItems":
        return f"List at {location} needs at least {error.validator_value} item."
    if error.validator == "oneOf":
        return f"Section {location} must match exactly one supported shape."
    if error.validator == "additionalProperties":
        return f"Section {location} contains an unsupported field."
    return f"Invalid value at {location}: {error.message}"


def format_error(error: ValidationError) -> Guidance:
    location = _normalize_location(error)
    template = _guidance_template(location)
    return Guidance(
        location=location,
        problem=_problem(error, location),
        why_it_matters=template["why"],
        fix=template["fix"],
        snippet=template["snippet"],
        reference=template["reference"],
        raw_message=error.message,
    )


def format_errors(errors: Iterable[ValidationError]) -> list[Guidance]:
    return [format_error(error) for error in errors]


def render_text(path_label: str, guidance_items: list[Guidance]) -> str:
    lines = [f"FAIL {path_label}"]
    for index, item in enumerate(guidance_items, start=1):
        lines.extend(
            [
                f"",
                f"{index}. {item.problem}",
                f"   Location: {item.location}",
                f"   Why it matters: {item.why_it_matters}",
                f"   Fix: {item.fix}",
                "   Minimal snippet:",
            ]
        )
        lines.extend(f"     {line}" if line else "" for line in item.snippet.splitlines())
        lines.append(f"   Reference: {item.reference}")
    return "\n".join(lines)
