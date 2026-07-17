#!/usr/bin/env python3
"""Run a bounded provider-backed sandbox prototype with budget and eval traces."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import yaml

from run_local_agent import display_path, validate


ROOT = Path(__file__).resolve().parents[1]


SCENARIOS = [
    {
        "id": "simple-agent-fake-provider-pass",
        "adl": "examples/simple-agent.yaml",
        "provider": "fake-openai",
        "model": "fake-openai/gpt-sandbox-mini",
        "task": "Explain what ReddiAgent can safely prove in this sandbox.",
        "budget": {
            "maxPromptTokens": 80,
            "maxCompletionTokens": 80,
            "maxTotalTokens": 160,
            "maxUsd": 0.001,
        },
        "response": (
            "Answer: ReddiAgent can prove prompt construction, model metadata, budget gates, "
            "eval gates, and trace capture without calling a hosted provider."
        ),
        "expectedCompletionStatus": "pass",
    },
    {
        "id": "simple-agent-fake-provider-budget-fail",
        "adl": "examples/simple-agent.yaml",
        "provider": "fake-openai",
        "model": "fake-openai/gpt-sandbox-mini",
        "task": "Explain what ReddiAgent can safely prove in this sandbox.",
        "budget": {
            "maxPromptTokens": 8,
            "maxCompletionTokens": 8,
            "maxTotalTokens": 12,
            "maxUsd": 0.00001,
        },
        "response": (
            "Answer: ReddiAgent can prove prompt construction, model metadata, budget gates, "
            "eval gates, and trace capture without calling a hosted provider."
        ),
        "expectedCompletionStatus": "fail",
    },
]


def stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())


def estimate_tokens(text: str) -> int:
    # Conservative deterministic stand-in for provider token accounting.
    return max(1, len(text.split()))


def estimate_usd(prompt_tokens: int, completion_tokens: int) -> float:
    # Fake local provider pricing: USD 0.000001 per token for bounded evidence only.
    return round((prompt_tokens + completion_tokens) * 0.000001, 6)


def build_prompt(doc: dict[str, Any], task: str) -> str:
    metadata = doc["metadata"]
    harness = doc["harness"]
    instructions = harness["instructions"]["inline"]
    policy_ids = ", ".join(policy["id"] for policy in harness.get("policies", [])) or "none"
    eval_ids = ", ".join(gate["id"] for gate in harness.get("evalGates", [])) or "none"
    return (
        f"Agent: {metadata['name']}\n"
        f"Instructions: {instructions}\n"
        f"Policies: {policy_ids}\n"
        f"Eval gates: {eval_ids}\n"
        f"Task: {task}"
    )


def check_budget(
    budget: dict[str, int | float],
    prompt_tokens: int,
    completion_tokens: int,
    estimated_cost_usd: float,
) -> dict[str, Any]:
    total_tokens = prompt_tokens + completion_tokens
    checks = [
        {
            "id": "prompt-token-budget",
            "status": "pass" if prompt_tokens <= budget["maxPromptTokens"] else "fail",
            "actual": prompt_tokens,
            "limit": budget["maxPromptTokens"],
        },
        {
            "id": "completion-token-budget",
            "status": "pass" if completion_tokens <= budget["maxCompletionTokens"] else "fail",
            "actual": completion_tokens,
            "limit": budget["maxCompletionTokens"],
        },
        {
            "id": "total-token-budget",
            "status": "pass" if total_tokens <= budget["maxTotalTokens"] else "fail",
            "actual": total_tokens,
            "limit": budget["maxTotalTokens"],
        },
        {
            "id": "estimated-cost-budget",
            "status": "pass" if estimated_cost_usd <= budget["maxUsd"] else "fail",
            "actual": estimated_cost_usd,
            "limit": budget["maxUsd"],
        },
    ]
    return {
        "status": "pass" if all(check["status"] == "pass" for check in checks) else "fail",
        "checks": checks,
    }


def check_evals(doc: dict[str, Any], response: str) -> dict[str, Any]:
    results = []
    for gate in doc["harness"].get("evalGates", []):
        if gate["id"] == "has-answer":
            passed = "answer:" in response.lower() or "uncertain" in response.lower()
            message = "response includes an answer or uncertainty marker"
        else:
            passed = False
            message = "fake provider sandbox has no evaluator for this gate"
        results.append(
            {
                "id": gate["id"],
                "type": gate["type"],
                "status": "pass" if passed else "fail",
                "message": message,
                "retryable": False,
            }
        )
    return {
        "status": "pass" if all(result["status"] == "pass" for result in results) else "fail",
        "results": results,
    }


def trace_event(trace_id: str, event: str, **fields: Any) -> dict[str, Any]:
    return {"event": event, "traceId": trace_id, **fields}


def run_scenario(config: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / config["adl"]
    doc = load_yaml(path)
    errors = validate(doc)
    if errors:
        return {
            "id": config["id"],
            "status": "fail",
            "adl": display_path(path),
            "completion": {
                "status": "fail",
                "reason": "ADL validation failed before provider sandbox execution",
            },
            "validationErrorCount": len(errors),
        }

    prompt = build_prompt(doc, config["task"])
    response = config["response"]
    prompt_tokens = estimate_tokens(prompt)
    completion_tokens = estimate_tokens(response)
    estimated_cost_usd = estimate_usd(prompt_tokens, completion_tokens)
    budget = check_budget(config["budget"], prompt_tokens, completion_tokens, estimated_cost_usd)
    evals = check_evals(doc, response)
    completion_status = "pass" if budget["status"] == "pass" and evals["status"] == "pass" else "fail"
    completion_reason = (
        "provider sandbox completed and required budget/eval gates passed"
        if completion_status == "pass"
        else "provider sandbox completed but required budget/eval gates failed"
    )
    trace_id = stable_id(doc["metadata"]["name"], config["id"], "provider-sandbox")
    trace = [
        trace_event(
            trace_id,
            "provider.sandbox_started",
            agent=doc["metadata"]["name"],
            provider=config["provider"],
            model=config["model"],
        ),
        trace_event(
            trace_id,
            "provider.prompt_prepared",
            promptHash=stable_hash(prompt),
            promptBytes=len(prompt.encode("utf-8")),
            promptPreview=prompt[:120],
        ),
        trace_event(
            trace_id,
            "provider.response_received",
            responseHash=stable_hash(response),
            promptTokens=prompt_tokens,
            completionTokens=completion_tokens,
            totalTokens=prompt_tokens + completion_tokens,
            estimatedCostUsd=estimated_cost_usd,
        ),
        trace_event(trace_id, "budget.checked", status=budget["status"], failedCount=sum(1 for check in budget["checks"] if check["status"] == "fail")),
        trace_event(trace_id, "eval.checked", status=evals["status"], failedCount=sum(1 for result in evals["results"] if result["status"] == "fail")),
        trace_event(trace_id, "provider.sandbox_completed", status=completion_status, reason=completion_reason),
    ]
    status = "pass" if completion_status == config["expectedCompletionStatus"] else "fail"
    return {
        "id": config["id"],
        "status": status,
        "adl": config["adl"],
        "provider": {
            "adapter": "local-fake-provider",
            "provider": config["provider"],
            "model": config["model"],
            "hostedProviderCall": False,
            "credentialAccess": False,
            "networkAccess": False,
        },
        "prompt": {
            "task": config["task"],
            "hash": stable_hash(prompt),
            "preview": prompt[:120],
        },
        "usage": {
            "promptTokens": prompt_tokens,
            "completionTokens": completion_tokens,
            "totalTokens": prompt_tokens + completion_tokens,
            "estimatedCostUsd": estimated_cost_usd,
        },
        "budget": {
            "limits": config["budget"],
            **budget,
        },
        "evals": evals,
        "completion": {
            "status": completion_status,
            "reason": completion_reason,
        },
        "trace": trace,
    }


def build_report() -> dict[str, Any]:
    scenarios = [run_scenario(scenario) for scenario in SCENARIOS]
    total_estimated_cost = round(sum(scenario.get("usage", {}).get("estimatedCostUsd", 0) for scenario in scenarios), 6)
    return {
        "mode": "provider-backed-sandbox-prototype",
        "status": "pass" if all(scenario["status"] == "pass" for scenario in scenarios) else "fail",
        "issue": 222,
        "providerAdapter": "local-fake-provider",
        "costEvidence": {
            "hostedProviderCalls": 0,
            "externalSpendUsd": 0,
            "simulatedEstimatedCostUsd": total_estimated_cost,
            "pricingModel": "fake local USD 0.000001 per token for deterministic budget evidence",
        },
        "boundaries": {
            "providerSandboxExecutionAllowed": True,
            "hostedProviderModelApiCalls": False,
            "networkAccess": False,
            "credentialAccess": False,
            "paymentAccess": False,
            "mcpInvocation": False,
            "devnetAccess": False,
            "mainnetAccess": False,
            "externalSpendUsd": 0,
        },
        "scenarios": scenarios,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Write the JSON evidence report to this path.")
    args = parser.parse_args()
    report = build_report()
    payload = json.dumps(report, indent=2)
    if args.output:
        output_path = args.output if args.output.is_absolute() else ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n")
    print(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
