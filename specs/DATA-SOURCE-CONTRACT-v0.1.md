# Data Source Contract v0.1

_Loop 75. Anchor issues: #88/#89._

## Purpose

Data sources describe what the harness can read or retrieve.

## Fields

- id
- type: file, url, api, database, vector-index, mcp
- description
- accessPolicy
- freshness
- citationRequired
- persistence

## Rule

Data sources are harness resources. They should not be hidden inside prompt text.

