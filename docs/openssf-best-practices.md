# OpenSSF Best Practices: passing criteria

This is the answer sheet for the [OpenSSF Best Practices badge](https://www.bestpractices.dev/) at the **passing** level. It follows the criteria as published at <https://www.bestpractices.dev/en/criteria/0> (checked 2026-10-19: 67 criteria) and was brought up to date on 2026-10-20, after the repository was published and 0.2.0 was released. Each row gives the answer to enter and the evidence to link.

Status values:

- **Met**: the evidence is in this repository or its GitHub settings today.
- **N/A**: the criterion does not apply, with the reason.
- **Maintainer must confirm**: a statement about the people on the project. Only the maintainer can answer it.

When entering URLs on bestpractices.dev, turn the relative links below into `https://github.com/DoGood-Studio/legal-deadline-calculator/blob/main/...`.

## Summary

| Status | Count |
|---|---|
| Met | 53 |
| N/A | 12 |
| Maintainer must confirm | 2 |

Every MUST criterion is met or does not apply, except the two statements only the maintainer can make.

## Basics

| Criterion | Level | Status | Evidence |
|---|---|---|---|
| `description_good` | MUST | Met | First paragraphs of [README.md](../README.md) and the demo page. |
| `interact` | MUST | Met | README sections *Install*, *Contributing*; issue templates in [.github/ISSUE_TEMPLATE](../.github/ISSUE_TEMPLATE/); GitHub Discussions. |
| `contribution` | MUST | Met | [CONTRIBUTING.md, *Commits and pull requests*](../CONTRIBUTING.md#commits-and-pull-requests): fork, branch, pull request, CI, review. |
| `contribution_requirements` | SHOULD | Met | [CONTRIBUTING.md, *Coding standards*](../CONTRIBUTING.md#coding-standards) and [*Tests are required*](../CONTRIBUTING.md#tests-are-required). |
| `floss_license` | MUST | Met | GNU AGPL-3.0 (AGPL-3.0-only) from the release after 0.2.0; versions up to 0.2.0 were released under MIT: [LICENSE](../LICENSE). |
| `floss_license_osi` | SUGGESTED | Met | AGPL-3.0 is OSI-approved (as is MIT, for the earlier versions). |
| `license_location` | MUST | Met | [LICENSE](../LICENSE) at the repository root, copied into [python/LICENSE](../python/LICENSE) and [js/LICENSE](../js/LICENSE) for the packages. |
| `documentation_basics` | MUST | Met | [README.md](../README.md), [docs/](.), [CONTRIBUTING.md](../CONTRIBUTING.md). |
| `documentation_interface` | MUST | Met | README *Quick start* (Python, TypeScript, command line); rule pack format in [docs/rulepacks.md](rulepacks.md); JSON Schemas in [spec/](../spec/); typed APIs (`py.typed`, `.d.ts`). |
| `sites_https` | MUST | Met | Repository on github.com, demo on github.io, packages on pypi.org and npmjs.com: all HTTPS-only. |
| `discussion` | MUST | Met | GitHub Issues and Discussions: searchable, URL-addressable, usable in a browser. |
| `english` | SHOULD | Met | All documentation is in English, with the README translated into 11 more languages ([docs/readme](readme/)); issues are accepted in English or Turkish. |
| `maintained` | MUST | Met | Actively developed; see the commit history. Must stay true. |

## Change control

| Criterion | Level | Status | Evidence |
|---|---|---|---|
| `repo_public` | MUST | Met | `https://github.com/DoGood-Studio/legal-deadline-calculator` |
| `repo_track` | MUST | Met | Git records what changed, who changed it and when. |
| `repo_interim` | MUST | Met | Work is committed to `main` between releases, not only at release time. |
| `repo_distributed` | SUGGESTED | Met | Git. |
| `version_unique` | MUST | Met | One version for both packages (0.2.0), also returned in every result; [python/tests/test_metadata.py](../python/tests/test_metadata.py) fails if any manifest, version module or `CITATION.cff` disagrees. |
| `version_semver` | SUGGESTED | Met | Semantic Versioning, stated in [CHANGELOG.md](../CHANGELOG.md). |
| `version_tags` | SUGGESTED | Met | Releases `v0.1.0`, `v0.1.1` and `v0.2.0` are tags; the release workflow refuses a tag that does not match the package versions ([RELEASING.md](../RELEASING.md)). |
| `release_notes` | MUST | Met | [CHANGELOG.md](../CHANGELOG.md) (Keep a Changelog format), copied into each GitHub Release. |
| `release_notes_vulns` | MUST | N/A | No publicly known vulnerabilities have been fixed. Future ones go under `### Security` ([SECURITY.md](../SECURITY.md#disclosure-in-release-notes)). |

## Reporting

| Criterion | Level | Status | Evidence |
|---|---|---|---|
| `report_process` | MUST | Met | GitHub Issues with templates for bugs, rule corrections and new jurisdictions ([.github/ISSUE_TEMPLATE](../.github/ISSUE_TEMPLATE/)). |
| `report_tracker` | SHOULD | Met | GitHub Issues. |
| `report_responses` | MUST | Met | No bug reports from users yet (the issues so far come from the maintainer, Dependabot and the source watch). Every report will be acknowledged. |
| `enhancement_responses` | SHOULD | Met | Same as above for enhancement requests. |
| `report_archive` | MUST | Met | GitHub Issues are public and searchable. |
| `vulnerability_report_process` | MUST | Met | [SECURITY.md](../SECURITY.md#reporting-a-vulnerability). |
| `vulnerability_report_private` | MUST | Met | GitHub private vulnerability reporting is enabled; [SECURITY.md](../SECURITY.md#reporting-a-vulnerability) links the form and gives an email address for reporters without a GitHub account. |
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
| `tests_are_added` | MUST | Met | Feature commits include tests, e.g. `23193f1` (act catalogue: `test_acts.py` and a hand-derived vector per act), `eb49b01` (version field, both languages) and `35f6fc8` (property and differential tests). |
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
| `delivery_mitm` | MUST | Met | Packages are delivered over HTTPS by PyPI and npm and published with Trusted Publishing and provenance; the release files are also signed with Sigstore and attached to each GitHub Release ([release.yml](../.github/workflows/release.yml)). |
| `delivery_unsigned` | MUST | Met | Nothing retrieves a hash over HTTP; workflows download only over HTTPS. |
| `vulnerabilities_fixed_60_days` | MUST | Met | No known vulnerabilities, and no runtime dependencies. |
| `vulnerabilities_critical_fixed` | SHOULD | Met | SECURITY.md commits to a fix or mitigation plan within 14 days. |
| `no_leaked_credentials` | MUST | Met | No credentials in the repository or its history (scanned 2026-10-20). Releases use OIDC Trusted Publishing, so no tokens are stored. |

## Analysis

| Criterion | Level | Status | Evidence |
|---|---|---|---|
| `static_analysis` | MUST | Met | CodeQL for Python, TypeScript and the workflows ([codeql.yml](../.github/workflows/codeql.yml)), plus ruff and mypy in CI. |
| `static_analysis_common_vulnerabilities` | SUGGESTED | Met | CodeQL's security queries; ruff's bugbear rules. |
| `static_analysis_fixed` | MUST | Met | The CodeQL findings of medium or higher severity were fixed on 2026-10-20. None was exploitable: the demo's language switch and translation lookup now accept only known codes, calendar ids use the browser's secure random source, and the data build reads each directory entry once. New findings are fixed as they appear. |
| `static_analysis_often` | SUGGESTED | Met | Every push and pull request, and weekly. |
| `dynamic_analysis` | SUGGESTED | Met | Property-based testing with Hypothesis and fast-check, and a 1,800-case Python/TypeScript differential test. |
| `dynamic_analysis_unsafe` | SUGGESTED | N/A | Python and TypeScript are memory-safe. |
| `dynamic_analysis_enable_assertions` | SUGGESTED | Met | Tests run with assertions enabled; property tests assert invariants on every generated case. |
| `dynamic_analysis_fixed` | MUST | Met | Problems found by property tests are fixed, e.g. backward counting in `business_days_between` (`35f6fc8`). |

## Applying for the badge

1. Sign in to <https://www.bestpractices.dev/> with GitHub and choose **Get Your Badge Now**.
2. Add the repository URL `https://github.com/DoGood-Studio/legal-deadline-calculator`. The site fills in some answers from GitHub; check them against this file.
3. Enter the answers from this file, section by section. For each **Maintainer must confirm** row, answer only if it is true.
4. When the project reaches 100%, add the badge to `README.md` and to every translation in `docs/readme/`, with the project id that bestpractices.dev assigns:
   ```markdown
   [![OpenSSF Best Practices](https://www.bestpractices.dev/projects/<id>/badge)](https://www.bestpractices.dev/projects/<id>)
   ```
