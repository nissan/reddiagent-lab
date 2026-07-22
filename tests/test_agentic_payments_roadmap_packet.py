from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "research" / "2026-07-23-agentic-payments-roadmap-recalibration.md"


def test_agentic_payments_roadmap_packet_has_required_sections() -> None:
    text = PACKET.read_text(encoding="utf-8")

    required_headings = [
        "## Boundary",
        "## Executive Verdict",
        "## Sources",
        "## Layer Map",
        "## Practical Release Ladder",
        "## External Tester MVP Candidates",
        "## Audit Prep Deltas",
        "## Recommendations",
        "## Follow-Up Child Issues To Create Under #220",
    ]
    for heading in required_headings:
        assert heading in text


def test_agentic_payments_roadmap_packet_keeps_guardrails_and_release_ladder() -> None:
    text = PACKET.read_text(encoding="utf-8")
    lowered = text.lower()

    required_terms = [
        "x402",
        "AP2",
        "FIDO",
        "Verifiable Intent",
        "MCP",
        "Solana devnet",
        "Surfpool/localnet",
        "mainnet",
        "official audit",
        "replay",
        "atomicity",
        "delegated authority",
        "spend limits",
        "privacy/PII",
        "receipt/settlement proof",
        "kill-switch",
    ]
    for term in required_terms:
        assert term.lower() in lowered

    forbidden_live_claims = [
        "mainnet is approved",
        "paymentAccess=true",
        "runtimeExecutionAllowed=true",
        "mcpInvocation=true",
    ]
    for claim in forbidden_live_claims:
        assert claim.lower() not in lowered


if __name__ == "__main__":
    test_agentic_payments_roadmap_packet_has_required_sections()
    test_agentic_payments_roadmap_packet_keeps_guardrails_and_release_ladder()
    print("PASS agentic payments roadmap packet")
