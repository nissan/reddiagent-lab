"""Builder-facing guidance for runtime-denied local tool fixture calls."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ToolDenialGuidance:
    tool_id: str
    problem: str
    why_it_matters: str
    fix: str
    snippet: str
    reference: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def guidance_for_denial(tool_id: str, reason: str) -> ToolDenialGuidance:
    if "undeclared tool" in reason:
        return ToolDenialGuidance(
            tool_id=tool_id,
            problem=f"Tool fixture references undeclared tool: {tool_id}.",
            why_it_matters=(
                "ReddiAgent only executes fixture calls that are declared in harness.tools, "
                "so a prompt or fixture cannot smuggle in a new capability."
            ),
            fix="Declare the tool in harness.tools if it is a safe local fixture, or remove the fixture call.",
            snippet=(
                "harness:\n"
                "  tools:\n"
                f"    - id: {tool_id}\n"
                "      type: function\n"
                "      description: Describe the safe local fixture.\n"
                "  toolFixtures:\n"
                f"    - toolId: {tool_id}\n"
                "      args: {}"
            ),
            reference="specs/TOOL-REGISTRY-v0.1.md",
        )

    if "unsupported local fixture tool" in reason:
        return ToolDenialGuidance(
            tool_id=tool_id,
            problem=f"Tool is declared but not implemented in the local fixture registry: {tool_id}.",
            why_it_matters=(
                "Declared tools still need a project-owned local implementation before the runner may execute them. "
                "This blocks shell, network, credential, and payment behavior from masquerading as fixtures."
            ),
            fix="Use an implemented local fixture tool such as search_docs, or add a deterministic registry implementation with tests.",
            snippet=(
                "harness:\n"
                "  tools:\n"
                "    - id: search_docs\n"
                "      type: function\n"
                "      description: Search approved documentation sources.\n"
                "  toolFixtures:\n"
                "    - toolId: search_docs\n"
                "      args:\n"
                "        query: tool registry"
            ),
            reference="specs/TOOL-REGISTRY-v0.1.md",
        )

    return ToolDenialGuidance(
        tool_id=tool_id,
        problem=reason,
        why_it_matters="Runtime-denied tool calls must be explainable before a builder can safely repair them.",
        fix="Review the tool fixture, registry implementation, and safety policy before retrying.",
        snippet="harness:\n  toolFixtures: []",
        reference="specs/TOOL-REGISTRY-v0.1.md",
    )


def render_tool_denial(path_label: str, guidance: ToolDenialGuidance) -> str:
    lines = [
        f"DENIED {path_label}",
        "",
        f"1. {guidance.problem}",
        f"   Tool: {guidance.tool_id}",
        f"   Why it matters: {guidance.why_it_matters}",
        f"   Fix: {guidance.fix}",
        "   Minimal snippet:",
    ]
    lines.extend(f"     {line}" if line else "" for line in guidance.snippet.splitlines())
    lines.append(f"   Reference: {guidance.reference}")
    return "\n".join(lines)
