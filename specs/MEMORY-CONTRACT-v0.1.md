# Memory Contract v0.1

_Loop 76. Anchor issues: #90/#92._

## Modes

- none
- session
- persistent
- external

## Fields

- mode
- retention
- scope
- storageRef
- privacyPolicy

Supported `scope` values:

- task
- session
- project
- user
- workspace
- external

## Rule

Persistent or external memory must declare retention and privacy policy before runtime execution.
