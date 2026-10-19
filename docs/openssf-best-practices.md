# OpenSSF Best Practices: passing criteria

This is the answer sheet for the [OpenSSF Best Practices badge](https://www.bestpractices.dev/) at the **passing** level. It follows the criteria as published at <https://www.bestpractices.dev/en/criteria/0> (checked 2026-10-19: 67 criteria). Each row gives the answer to enter and the evidence to link.

Status values:

- **Met**: the evidence is in this repository today. Reviewers can see it once the repository is public.
- **N/A**: the criterion does not apply, with the reason.
- **After publishing**: needs the public repository, a release or a repository setting.
- **Maintainer must confirm**: a statement about the people on the project. Only the maintainer can answer it.

When entering URLs on bestpractices.dev, turn the relative links below into `https://github.com/DoGood-Studio/lexdays/blob/main/...`.

## Summary

| Status | Count |
|---|---|
| Met | 43 |
| N/A | 12 |
| After publishing | 10 |
| Maintainer must confirm | 2 |

All MUST criteria that can be met before publishing are met.

## Basics

| Criterion | Level | Status | Evidence |
|---|---|---|---|
| `description_good` | MUST | Met | First paragraphs of [README.md](../README.md) and the demo page. |
| `interact` | MUST | Met | README sections *Install*, *Contributing*; issue templates in [.github/ISSUE_TEMPLATE](../.github/ISSUE_TEMPLATE/). |
| `contribution` | MUST | Met | [CONTRIBUTING.md, *Commits and pull requests*](../CONTRIBUTING.md#commits-and-pull-requests): fork, branch, pull request, CI, review. |
| `contribution_requirements` | SHOULD | Met | [CONTRIBUTING.md, *Coding standards*](../CONTRIBUTING.md#coding-standards) and [*Tests are required*](../CONTRIBUTING.md#tests-are-required). |
| `floss_license` | MUST | Met | MIT License: [LICENSE](../LICENSE). |
| `floss_license_osi` | SUGGESTED | Met | MIT is OSI-approved. |
| `license_location` | MUST | Met | [LICENSE](../LICENSE) at the repository root, copied into [python/LICENSE](../python/LICENSE) and [js/LICENSE](../js/LICENSE) for the packages. |
| `documentation_basics` | MUST | Met | [README.md](../README.md), [docs/](.), [CONTRIBUTING.md](../CONTRIBUTING.md). |
| `documentation_interface` | MUST | Met | README *Quick start* (Python, TypeScript, command line); rule pack format in [docs/rulepacks.md](rulepacks.md); JSON Schemas in [spec/](../spec/); typed APIs (`py.typed`, `.d.ts`). |
| `sites_https` | MUST | After publishing | Repository on github.com, demo on github.io, packages on pypi.org and npmjs.com: all HTTPS-only. |
| `discussion` | MUST | After publishing | GitHub Issues (and Discussions, if enabled): searchable, URL-addressable, usable in a browser. |
| `english` | SHOULD | Met | All documentation is in English (plus a Turkish README); issues are accepted in English or Turkish. |
| `maintained` | MUST | Met | Actively developed; see the commit history. Must stay true. |

## Change control

| Criterion | Level | Status | Evidence |
|---|---|---|---|
| `repo_public` | MUST | After publishing | `https://github.com/DoGood-Studio/lexdays` |
| `repo_track` | MUST | Met | Git records what changed, who changed it and when. |
| `repo_interim` | MUST | Met | Work is committed to `main` between releases, not only at release time. |
| `repo_distributed` | SUGGESTED | Met | Git. |
| `version_unique` | MUST | Met | One version for both packages (0.1.0); [python/tests/test_metadata.py](../python/tests/test_metadata.py) fails if any manifest or `CITATION.cff` disagrees. |
| `version_semver` | SUGGESTED | Met | Semantic Versioning, stated in [CHANGELOG.md](../CHANGELOG.md). |
| `version_tags` | SUGGESTED | After publishing | Each release is a `vX.Y.Z` tag; the release workflow refuses a tag that does not match the package versions ([RELEASING.md](../RELEASING.md)). |
| `release_notes` | MUST | Met | [CHANGELOG.md](../CHANGELOG.md) (Keep a Changelog format), copied into each GitHub Release. |
| `release_notes_vulns` | MUST | N/A | No publicly known vulnerabilities have been fixed. Future ones go under `### Security` ([SECURITY.md](../SECURITY.md#disclosure-in-release-notes)). |

## Reporting

| Criterion | Level | Status | Evidence |
|---|---|---|---|
| `report_process` | MUST | Met | GitHub Issues with templates for bugs, rule corrections and new jurisdictions ([.github/ISSUE_TEMPLATE](../.github/ISSUE_TEMPLATE/)). |
| `report_tracker` | SHOULD | Met | GitHub Issues. |
| `report_responses` | MUST | After publishing | No reports yet. Answer "Met: no bug reports received yet" and acknowledge every report from then on. |
| `enhancement_responses` | SHOULD | After publishing | Same as above for enhancement requests. |
| `report_archive` | MUST | After publishing | GitHub Issues are public and searchable. |
| `vulnerability_report_process` | MUST | Met | [SECURITY.md](../SECURITY.md#reporting-a-vulnerability). |
| `vulnerability_report_private` | MUST | After publishing | GitHub private vulnerability reporting, described in SECURITY.md. It works only after it is enabled in the repository settings. |
| `vulnerability_report_response` | MUST | N/A | No vulnerability reports in the last 6 months. SECURITY.md commits to an acknowledgement within 3 working days. |

## Quality

| Criterion | Level | Status | Evidence |
|---|---|---|---|
| `build` | MUST | Met | `uv build` (hatchling) and `npm run build` (tsup); run in CI ([ci.yml](../.github/workflows/ci.yml)). |
| `build_common_tools` | SUGGESTED | Met | Standard Python and npm tooling. |
| `build_floss_tools` | SHOULD | Met | All build tools are FLOSS. |
| `test` | MUST | Met | pytest and vitest suites in [python/tests](../python/tests/) and [js/test](../js/test/), plus shared vectors in [vectors/](../vectors/); how to run them is in [CONTRIBUTING.md](../CONTRIBUTING.md#development-setup). |
| `test_invocation` | SHOULD | Met | `uv run pytest` and `npm test`. |
| `test_most` | SUGGESTED | Met | CI requires at least 95% line and branch coverage for Python; both implementations run the same vectors. |
| `test_continuous_integration` | SUGGESTED | Met | [ci.yml](../.github/workflows/ci.yml): every push and pull request, on Linux, Windows and macOS. |
| `test_policy` | MUST | Met | [CONTRIBUTING.md, *Tests are required*](../CONTRIBUTING.md#tests-are-required). |
| `tests_are_added` | MUST | Met | Recent feature commits include tests, e.g. `a4d8d6e` (property and differential tests) and `1e128a9` (`test_i18n.py` with the 12 languages). |
| `tests_documented_added` | SUGGESTED | Met | CONTRIBUTING.md and the checklist in [PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md). |
| `warnings` | MUST | Met | ruff, mypy in strict mode, TypeScript in strict mode. |
| `warnings_fixed` | MUST | Met | CI fails on any ruff, mypy or tsc finding; all are clean today. |
| `warnings_strict` | SUGGESTED | Met | `mypy --strict`, `tsc` with `strict` and `noImplicitOverride`, and a broad ruff rule set (`E F W I B UP SIM RUF PL C4 PT`). |

## Security

| Criterion | Level | Status | Evidence |
|---|---|---|---|
| `know_secure_design` | MUST | Maintainer must confirm | Supporting material: [SECURITY.md, *Security design*](../SECURITY.md#security-design). The answer must be true of a primary developer. |
| `know_common_errors` | MUST | Maintainer must confirm | The errors relevant to this library and their mitigations are listed in SECURITY.md: code execution from data, path traversal, resource exhaustion, ReDoS, time-zone shifts and supply-chain attacks. |
| `crypto_published` | MUST | N/A | The software uses no cryptography. |
| `crypto_call` | SHOULD | N/A | No cryptography. |
| `crypto_floss` | MUST | N/A | No cryptography. |
| `crypto_keylength` | MUST | N/A | No cryptography. |
| `crypto_working` | MUST | N/A | No cryptography. |
| `crypto_weaknesses` | SHOULD | N/A | No cryptography. |
| `crypto_pfs` | SHOULD | N/A | No cryptography. |
| `crypto_password_storage` | MUST | N/A | The software stores no passwords. |
| `crypto_random` | MUST | N/A | No cryptographic keys or nonces. |
| `delivery_mitm` | MUST | After publishing | Packages are delivered over HTTPS by PyPI and npm and published with Trusted Publishing and provenance ([release.yml](../.github/workflows/release.yml)). |
| `delivery_unsigned` | MUST | Met | Nothing retrieves a hash over HTTP; workflows download only over HTTPS. |
| `vulnerabilities_fixed_60_days` | MUST | Met | No known vulnerabilities, and no runtime dependencies. |
| `vulnerabilities_critical_fixed` | SHOULD | Met | SECURITY.md commits to a fix or mitigation plan within 14 days. |
| `no_leaked_credentials` | MUST | Met | No credentials in the repository (scanned 2026-10-19). Releases use OIDC Trusted Publishing, so no tokens are stored. |

## Analysis

| Criterion | Level | Status | Evidence |
|---|---|---|---|
| `static_analysis` | MUST | Met | CodeQL for Python, TypeScript and the workflows ([codeql.yml](../.github/workflows/codeql.yml)), plus ruff and mypy in CI. |
| `static_analysis_common_vulnerabilities` | SUGGESTED | Met | CodeQL's security queries; ruff's bugbear rules. |
| `static_analysis_fixed` | MUST | After publishing | CodeQL first runs on GitHub. Fix any medium or higher alert before the first release. |
| `static_analysis_often` | SUGGESTED | Met | Every push and pull request, and weekly. |
| `dynamic_analysis` | SUGGESTED | Met | Property-based testing with Hypothesis and fast-check, and a 1,800-case Python/TypeScript differential test. |
| `dynamic_analysis_unsafe` | SUGGESTED | N/A | Python and TypeScript are memory-safe. |
| `dynamic_analysis_enable_assertions` | SUGGESTED | Met | Tests run with assertions enabled; property tests assert invariants on every generated case. |
| `dynamic_analysis_fixed` | MUST | Met | Problems found by property tests are fixed, e.g. backward counting in `business_days_between` (`a4d8d6e`). |

## After publishing

1. Make the repository public and push `main`.
2. Enable private vulnerability reporting:
   ```bash
   gh api -X PUT repos/DoGood-Studio/lexdays/private-vulnerability-reporting
   ```
3. Let CI, CodeQL and Scorecard run once, and fix any CodeQL alert of medium or higher severity.
4. Sign in to <https://www.bestpractices.dev/> with GitHub, choose **Get Your Badge Now**, and add the repository URL.
5. Enter the answers from this file. For each **Maintainer must confirm** row, answer only if it is true.
6. Add the badge to `README.md` with the project id that bestpractices.dev assigns:
   ```markdown
   [![OpenSSF Best Practices](https://www.bestpractices.dev/projects/<id>/badge)](https://www.bestpractices.dev/projects/<id>)
   ```
7. Release 0.1.0 by creating the `v0.1.0` tag as a GitHub Release ([RELEASING.md](../RELEASING.md)). This also completes `version_tags` and `delivery_mitm`.
