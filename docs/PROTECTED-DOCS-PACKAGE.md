# Protected Docs Package

_Issue #210. Parent epic: #206._

This package plan prepares ReddiAgent for partner/advisor sharing without deploying or publishing anything from this repository.

## Package Intent

The protected package is a static documentation bundle that gathers:

- vision and roadmap entrypoints;
- architecture and product thesis docs;
- ADR index and initial decisions;
- specs, mappings, and research entrypoints;
- deterministic evidence reports for the static/export surfaces.

The package deliberately stays separate from runtime code. It does not start servers, install dependencies, execute providers, resolve MCP servers, access credentials, configure payment rails, select/store a password, deploy, or publish.

## Access Model

Use a simple shared password or equivalent host-level access control selected outside this repo at publish time. The password must not be generated, committed, logged, or stored in this repository.

Recommended partner/advisor flow:

1. Nissan approves the hosting location and access approach.
2. The static package is deployed behind that host-level protection.
3. The URL and password/access grant are shared out-of-band.
4. Rotation happens in the hosting/access-control layer, not in repo docs.

## Crawler Controls

The package should default to no indexing:

- `robots.txt`: `User-agent: *` with `Disallow: /`.
- HTML pages: `noindex, nofollow, noarchive` robots meta tag.
- Hosting headers: `X-Robots-Tag: noindex, nofollow, noarchive`.
- Sitemap: omit `sitemap.xml` for the protected package.

These controls reduce crawler exposure but do not replace access control.

## Local Manifest

Generate the package manifest locally:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/protected_docs_package.py
```

The manifest is guarded by `tests/test_protected_docs_package.py` and fixture `tests/fixtures/protected-docs-package.json`.

## Static Boundary

Current package work is static review only:

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

Deployment, public publishing, and password selection require a separate Nissan approval gate. Mainnet deployment or mainnet runs remain out of scope.
