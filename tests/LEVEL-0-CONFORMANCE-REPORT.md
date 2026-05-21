# Level 0 Conformance Report

_Loop 23/25. Issues: #23, #25._

## Command

    /Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/validate_examples.py

## Result

    PASS examples/simple-agent.yaml
    PASS examples/tool-agent.yaml
    PASS examples/payment-agent.yaml

## Interpretation

All current example ADL files satisfy Level 0 conformance: schema-valid ReddiAgent documents with required model and harness fields.

## Follow-Up

Level 1 conformance should prove that simple-agent and tool-agent can run or dry-run on the local-python target.

