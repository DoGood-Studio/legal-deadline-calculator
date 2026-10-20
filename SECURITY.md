# Security policy

## Supported versions

Security fixes are released for the latest minor version of the `lexdays` packages on PyPI and npm.

## Reporting a vulnerability

Please **do not** open a public issue for a security vulnerability.

Report it privately with GitHub's private vulnerability reporting: [open a private report](https://github.com/DoGood-Studio/legal-deadline-calculator/security/advisories/new) (or go to the repository's **Security** tab and choose **Report a vulnerability**), and describe the issue, the affected versions and, if possible, steps to reproduce.

If you cannot use GitHub, email **dogoodstudio.dev@gmail.com** with the same details.

What to expect:

- an acknowledgement within **3 working days**;
- an assessment and, for a confirmed vulnerability, a fix or mitigation plan within **14 days**;
- coordinated disclosure: we publish a GitHub Security Advisory and a patched release, and credit the reporter unless they prefer otherwise.

## Scope

lexdays has no runtime dependencies and makes no network calls. The most relevant risks are:

- loading untrusted calendar or rule pack definitions (they are validated strictly; ids are restricted to block path traversal);
- supply-chain issues in the release process (releases use PyPI and npm Trusted Publishing with provenance, the built packages are signed with Sigstore and attached to the GitHub release, and all GitHub Actions are pinned by commit SHA).

A **wrong deadline** is a correctness bug, not a security vulnerability. Please report it as a *Rule correction* issue.

## Security design

The libraries are built so that untrusted input cannot do more than raise an error:

- **No code from data.** Rule packs and calendars are JSON data, never code. A rule pack can only use a closed set of step types, and its conditions are evaluated by a small interpreter over a closed set of keys. Nothing is passed to `eval`, `exec`, `new Function` or a template engine, and nothing is deserialised except with the standard JSON parsers.
- **Strict validation.** Every definition is checked when loaded: unknown fields, unknown step types, unknown options and option values, bad dates and times all raise `DataError` or `OptionError`. The same rules are published as JSON Schemas in [`spec/`](spec/) and every bundled file is tested against them.
- **No path traversal.** In Python, calendar and rule pack ids must match `^[a-z0-9]+(?:[-_/][a-z0-9]+)*$` before any file is opened. The TypeScript package looks ids up only among its bundled definitions, by own property. Either way `..`, absolute paths, backslashes and names such as `__proto__` are rejected.
- **Bounded work.** Period amounts are limited to 100,000 units, a search for the next working day gives up after 1,000 days, calendar inheritance cycles are detected, and dates outside a calendar's verified years raise `CoverageError` instead of looping or guessing. Input patterns are anchored regular expressions without nested quantifiers.
- **No ambient state.** No network access, no environment variables, no clock or time zone: the library does civil-date arithmetic on `YYYY-MM-DD` strings, and the TypeScript API rejects JavaScript `Date` objects so that a local time zone can never shift a deadline.
- **Small supply chain.** No runtime dependencies. Development dependencies are locked (`uv.lock`, `package-lock.json`) and updated by Dependabot. GitHub Actions are pinned by commit SHA, CodeQL scans Python, TypeScript and the workflows on every push and weekly, and OpenSSF Scorecard runs weekly.

## Disclosure in release notes

When a release fixes a publicly known vulnerability, the release notes in [`CHANGELOG.md`](CHANGELOG.md) list it under a `### Security` heading with its GitHub Security Advisory or CVE id.
