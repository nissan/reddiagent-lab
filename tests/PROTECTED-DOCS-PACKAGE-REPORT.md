# Protected Docs Package Report

_Issue #210. Parent epic: #206._

## Summary

`scripts/protected_docs_package.py` builds a deterministic manifest for a protected, noindex ReddiAgent documentation package. It packages the existing vision, roadmap, architecture, ADR register, specs, mappings, research entrypoints, and evidence reports without deploying or publishing anything.

## Access and Crawling

- Protection model: host-level shared password or equivalent access control selected outside this repo after Nissan approval.
- Password handling: no password is generated, committed, logged, or stored by this package.
- Crawler controls: `robots.txt` disallows all crawling; pages should use `noindex, nofollow, noarchive`; hosting should set `X-Robots-Tag: noindex, nofollow, noarchive`; sitemap is omitted.

## Static Boundary

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`
- `providerModelApiCalls=false`
- `credentialLookupOrStorage=false`
- `deploymentAllowed=false`
- `publishingAllowed=false`
- `universalPasswordSelected=false`
- `writesRuntimeCode=false`

## Validation

Run:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/protected_docs_package.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_protected_docs_package.py
PYTHON=/Users/loki/.pyenv/versions/3.14.3/bin/python3 bash tests/smoke-validation.sh
```
