# Security policy

## Supported versions

Security fixes are released for the latest minor version of the `lexdays` packages on PyPI and npm.

## Reporting a vulnerability

Please **do not** open a public issue for a security vulnerability.

Report it privately with GitHub's private vulnerability reporting: go to the repository's **Security** tab, choose **Report a vulnerability**, and describe the issue, the affected versions and, if possible, steps to reproduce.

What to expect:

- an acknowledgement within **3 working days**;
- an assessment and, for a confirmed vulnerability, a fix or mitigation plan within **14 days**;
- coordinated disclosure: we publish a GitHub Security Advisory and a patched release, and credit the reporter unless they prefer otherwise.

## Scope

lexdays has no runtime dependencies and makes no network calls. The most relevant risks are:

- loading untrusted calendar or rule pack definitions (they are validated strictly; ids are restricted to block path traversal);
- supply-chain issues in the release process (releases use PyPI and npm Trusted Publishing with provenance; all GitHub Actions are pinned by commit SHA).

A **wrong deadline** is a correctness bug, not a security vulnerability. Please report it as a *Rule correction* issue.
