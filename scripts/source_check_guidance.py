"""Builder-facing guidance for local source-check failures."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SourceCheckGuidance:
    gate_id: str
    tool_id: str
    problem: str
    why_it_matters: str
    fix: str
    snippet: str
    reference: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def guidance_for_source_failure(
    gate_id: str,
    tool_id: str,
    title: str,
    url: str,
) -> SourceCheckGuidance:
    return SourceCheckGuidance(
        gate_id=gate_id,
        tool_id=tool_id,
        problem=(
            f"Tool output cites an unapproved source: title={title!r}, url={url!r}."
        ),
        why_it_matters=(
            "A successful fixture tool call only proves execution succeeded. "
            "Source trust must be checked separately so a local fixture cannot smuggle "
            "unsupported web, MCP, credential, or payment evidence into the answer."
        ),
        fix=(
            "Return one of the approved in-repo sources from the local fixture, or add a "
            "project-owned source to the approved list with review and tests."
        ),
        snippet=(
            "output:\n"
            "  title: Tool Registry Contract v0.1\n"
            "  url: specs/TOOL-REGISTRY-v0.1.md"
        ),
        reference="specs/DATA-SOURCE-CONTRACT-v0.1.md",
    )
