#!/usr/bin/env python3
"""Emit a deterministic dry-run receipt for a payment-capable ReddiAgent."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]


def digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> int:
    path = ROOT / "examples" / "payment-agent.yaml"
    doc = yaml.safe_load(path.read_text())
    x402 = doc["extensions"]["x402"]
    intent = x402["intents"][0]
    agent = doc["metadata"]["name"]
    task_id = "dry-run-example-task"
    receipt = {
        "receiptVersion": "reddiagent.receipt/v0.1",
        "mode": "dry-run",
        "agent": agent,
        "taskId": task_id,
        "paymentIntentId": intent["id"],
        "railCandidates": intent["rails"],
        "amount": intent["maxAmount"],
        "currency": intent["currency"],
        "requestHash": digest(agent + ":" + task_id + ":request"),
        "responseHash": digest(agent + ":" + task_id + ":response"),
        "policyResults": [{"id": "task-budget", "status": "pass"}],
        "evalResults": [{"id": "receipt-required", "status": "pass"}],
        "settlementReference": None,
    }
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

