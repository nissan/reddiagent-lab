# Tutorial: Simple Local Agent

_Loop 38. Anchor issue: #40._

## Goal

Run the smallest ReddiAgent definition as a local dry-run.

## File

    examples/simple-agent.yaml

## Validate

    /Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/validate_examples.py

Expected:

    PASS examples/simple-agent.yaml

## Dry-Run

    /Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/run_local_agent.py examples/simple-agent.yaml

What to notice:

- model capability is chat.
- preferred provider is openai.
- no tools are registered.
- one policy prevents external actions.
- one eval gate requires a clear answer or uncertainty statement.

## Builder Lesson

An agent does not start with tools. It starts with a job, a model profile, a harness instruction, a policy, and a completion check.

