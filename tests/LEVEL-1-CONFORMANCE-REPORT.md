# Level 1 Conformance Report

_Loops 44, 46, 47. Issues: #44, #47, #48._

## Commands

    /Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/validate_examples.py
    /Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_level1.py

## Expected Result

    PASS examples/simple-agent.yaml
    PASS examples/tool-agent.yaml
    PASS examples/payment-agent.yaml
    PASS Level 1 simple-agent.yaml
    PASS Level 1 tool-agent.yaml

## Interpretation

simple-agent and tool-agent satisfy Level 1 local dry-run conformance. payment-agent remains Level 0 plus payment dry-run only.

