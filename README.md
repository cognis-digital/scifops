# scifops — SCIF / SAPF operational compliance helpers

[![CI](https://github.com/cognis-digital/scifops/workflows/CI/badge.svg)](https://github.com/cognis-digital/scifops/actions)
[![Classification](https://img.shields.io/badge/classification-UNCLASSIFIED-green.svg)](./UPSTREAM.md)

> Public primitives for SCIF/SAPF compliance: badge log w/ tamper-evident audit, TPI, escort tracking, GSA container cadence.

## Usage — step by step

`scifops` is built on the shared `cognis_mil` CLI: a positional target plus
standard output/scoring flags.

1. **Install** (editable from a clone, or from the wheel):
   ```bash
   pip install -e .
   # provides the `scifops` console script
   ```
2. **Run the primary scan** against a path or target (defaults to `.`):
   ```bash
   scifops .
   ```
3. **Emit machine-readable output** — pick any of `console|json|markdown|sarif|oscal`:
   ```bash
   scifops ./target --format json --out scifops-report.json
   ```
4. **Read / use the output.** The JSON report carries the findings list and a
   severity-weighted `composite_score`; SARIF drops straight into code-scanning,
   and `oscal` emits an OSCAL skeleton. A `--classification` banner can be
   stamped on the report (placeholder only — the tool does not interpret it):
   ```bash
   scifops ./target --classification "UNCLASSIFIED//FOR PUBLIC RELEASE" --format markdown
   ```
5. **Gate CI on severity** with `--fail-on` (`very_high|high|moderate|low|none`).
   The process exits non-zero when a finding at/above the threshold exists:
   ```bash
   scifops ./target --format sarif --out scifops.sarif --fail-on high
   ```

## Upstream

Forks / wraps **(original)**. See [`UPSTREAM.md`](./UPSTREAM.md) for the
licensing posture, supported commits, and how to upgrade.

## What this adds for military / IC use

- BadgeLog with hash-chained audit (cognis_mil.AuditLog)
- TPI verification primitive
- Visitor escort enforcement
- GSA container inspection-due reminders

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
    pip install cognis-scifops
    scifops . --format=oscal --out=assessment-results.json --fail-on=high
- name: Upload to eMASS/Xacta
  run: cognis-rmf-package import assessment-results.json
```

## Part of the Cognis Digital military / IC ecosystem

12 repos. All MIT/Apache-2.0/GPL-3 (per upstream). Cognis additions are
Apache-2.0 unless stated otherwise.

See [the master index](../../MASTER-INDEX.md).

## Interoperability

`{}` composes with the 300+ tool Cognis suite — JSON in/out and a shared
OpenAI-compatible `/v1` backbone. See **[INTEROP.md](INTEROP.md)** for the
suite map, composition patterns, and reference stacks.
