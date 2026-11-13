# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| 1.2.x | Yes |
| < 1.2 | No |

## Reporting a vulnerability

Please report security issues privately:

- Email: security@gamai.io
- Or use the repository's private security advisory feature.

Include:

- affected version and component,
- a minimal reproduction,
- impact assessment (what an attacker could do),
- any suggested fix.

We aim to acknowledge reports within 3 business days and to provide a remediation plan within 10 business days.

## Scope

In scope:

- bypass of Gate 1 / Gate 2 decisions (e.g. a destructive action classified as `READ`),
- forged or replayable evidence receipts,
- denial of service caused by crafted input to the decision engine,
- dependency or supply-chain issues in the core package.

Out of scope:

- issues that require a compromised host or stolen credentials,
- vulnerabilities in third-party services invoked by an integrator.

## Design notes

- The core performs **no network I/O** unless `BH_SPECULATIVE_URL` is explicitly set.
- The core requires **no secrets** to run.
- Evidence receipts are hashes over canonical JSON; they are not a substitute for a signed audit log in the enterprise edition.
