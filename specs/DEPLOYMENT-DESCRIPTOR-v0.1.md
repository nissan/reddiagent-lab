# Deployment Descriptor v0.1

_Loop 78. Anchor issue: #93._

## Purpose

Deployment describes where the harness runs and what constraints it must obey.

## Fields

- target
- region
- resources
- environment
- secretRefs
- networkPolicy
- storage
- observability
- rollback

## Rule

If deployment cannot enforce declared policies, compatibility must fail before execution.

