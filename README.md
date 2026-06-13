# scifops — SCIF / SAPF operational compliance helpers

[![CI](https://github.com/cognis-digital/scifops/workflows/CI/badge.svg)](https://github.com/cognis-digital/scifops/actions)
[![Classification](https://img.shields.io/badge/classification-UNCLASSIFIED-green.svg)](./UPSTREAM.md)

> Public primitives for SCIF/SAPF compliance: badge log w/ tamper-evident audit, TPI, escort tracking, GSA container cadence.

<!-- cognis:layman:start -->
## What is this?

scifops is a command-line tool that helps security teams track and verify compliance inside Sensitive Compartmented Information Facilities (SCIFs) — the secure rooms used by military and intelligence organizations. It monitors who enters and exits the facility using badge logs, checks that safes and storage containers are inspected on schedule, and enforces the "two-person rule" that requires a second authorized person to witness sensitive operations. It is designed for cleared facilities managers, security officers, and DevOps pipelines that need an automated, tamper-evident record of physical access control activities.
<!-- cognis:layman:end -->

## Upstream

Forks / wraps **(original)**. See [`UPSTREAM.md`](./UPSTREAM.md) for the
licensing posture, supported commits, and how to upgrade.

## What this adds for military / IC use

- BadgeLog with hash-chained audit (cognis_mil.AuditLog)
- TPI verification primitive
- Visitor escort enforcement
- GSA container inspection-due reminders

<!-- cognis:domains:start -->
## Domains

**Primary domain:** Defense & Aerospace  ·  **JTF MERIDIAN division:** IRONCLAD · INDIA

**Topics:** `cognis` `defense` `aerospace` `defense-tech`

Part of the **Cognis Neural Suite** — 300+ source-available tools organized across 12 domains under the JTF MERIDIAN command structure. See the [suite on GitHub](https://github.com/cognis-digital) and [jtf-meridian](https://github.com/cognis-digital/jtf-meridian) for how the pieces fit together.
<!-- cognis:domains:end -->

<!-- cognis:install:start -->
## Install

`scifops` is source-available (not published to PyPI) — every method below installs
straight from GitHub. Pick whichever you prefer; the one-line scripts auto-detect
the best tool available on your machine.

**One-liner (Linux / macOS):**
```sh
curl -fsSL https://raw.githubusercontent.com/cognis-digital/scifops/HEAD/install.sh | sh
```

**One-liner (Windows PowerShell):**
```powershell
irm https://raw.githubusercontent.com/cognis-digital/scifops/HEAD/install.ps1 | iex
```

**Or install manually — any one of:**
```sh
pipx install "git+https://github.com/cognis-digital/scifops.git"     # isolated (recommended)
uv tool install "git+https://github.com/cognis-digital/scifops.git"  # uv
pip install "git+https://github.com/cognis-digital/scifops.git"      # pip
```

**From source:**
```sh
git clone https://github.com/cognis-digital/scifops.git
cd scifops && pip install .
```

Then run:
```sh
scifops --help
```
<!-- cognis:install:end -->

## Install

```bash
# Shared library (only once for the whole ecosystem):
pip install -e ../../shared

# This tool:
pip install -e .
```

## Demo

```bash
scifops demos/
```

Outputs are available in five formats — all respect an operator-supplied
classification banner (passed via `--classification`):

```bash
scifops <target> --format=console     # default
scifops <target> --format=json
scifops <target> --format=sarif       # for code-scanning pipelines
scifops <target> --format=markdown    # for PRs / briefings
scifops <target> --format=oscal       # OSCAL Assessment Results skeleton
```

## Classification banner

All output is wrapped with an operator-supplied classification banner.
**Default**: `UNCLASSIFIED//FOR PUBLIC RELEASE`.

> ⚠️ This tool **does not** generate or validate the *content* of higher
> classifications. Operators on cleared systems supply real markings at runtime.
> See [`../shared/cognis_mil/classmark.py`](../../shared/cognis_mil/classmark.py).

## Compliance crosswalks (built in)

Every finding can carry references to:
- **NIST 800-53 Rev 5** controls (e.g. `AC-2(1)`)
- **DISA STIG** rule IDs (e.g. `V-242414`)
- **MITRE ATT&CK** technique IDs (e.g. `T1078`)
- **CCI** (Control Correlation Identifier)

These are emitted in JSON, SARIF, and the OSCAL skeleton.

## CI / RMF integration

```yaml
- name: scifops scan
  run: |
    pip install "git+https://github.com/cognis-digital/scifops.git"
    scifops . --format=oscal --out=assessment-results.json --fail-on=high
- name: Upload to eMASS/Xacta
  run: cognis-rmf-package import assessment-results.json
```

## Part of the Cognis Digital military / IC ecosystem

12 repos. All MIT/Apache-2.0/GPL-3 (per upstream). Cognis additions are
Apache-2.0 unless stated otherwise.

See [the master index](../../MASTER-INDEX.md).

<a name="verification"></a>
## Verification

[![tests](https://img.shields.io/badge/tests-5%20passing-2ea44f.svg)](AUDIT.md)

Every push is verified end-to-end. Latest audit (2026-06-13):

```text
tests        : 5 passed, 0 failed, 0 errored
compile      : all modules parse
cli          : scifops 0.1.0
package      : scifops
```

<details><summary>CLI surface (<code>--help</code>)</summary>

```text
usage: scifops [-h] [--format {console,json,markdown,sarif,oscal}] [--out OUT]
               [--fail-on {very_high,high,moderate,low,none}]
               [--classification CLASSIFICATION] [-v]
               [target]

scifops — Cognis Digital · Military/IC ecosystem

positional arguments:
  target                Path/target

options:
  -h, --help            show this help message and exit
  --format {console,json,markdown,sarif,oscal}
  --out OUT             Write output to file
```
</details>

Full machine-readable results: [`AUDIT.md`](AUDIT.md) · regenerate with `python -m scifops --help` + `pytest -q`.

<div align="right"><a href="#top">↑ back to top</a></div>

