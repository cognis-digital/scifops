"""scifops — SCIF / SAPF operational compliance helpers.

Implements operational primitives for a SCIF environment using PUBLIC
references (ICD 705, DoDM 5105.21). All data is placeholder; operators
on cleared systems supply real values.

Primitives:
  - BadgeLog (entry/exit audit log)
  - TwoPersonIntegrity (TPI verification for sensitive operations)
  - EscortTracker (visitor escort compliance)
  - GSAContainer inspection cadence reminders
"""
from __future__ import annotations
import time
import json
from dataclasses import dataclass
from pathlib import Path
from cognis_mil import ScanResult, Finding, Severity, AuditLog

_VALID_DIRECTIONS = {"in", "out"}


@dataclass
class BadgeEvent:
    badge_id: str
    holder_name: str
    ts: float
    direction: str       # "in" or "out"
    location: str = "MAIN"
    escort_for: str = ""  # if non-empty, this person is escorting a visitor
    visitor_id: str = ""

    def __post_init__(self) -> None:
        if not self.badge_id or not isinstance(self.badge_id, str):
            raise ValueError("badge_id must be a non-empty string")
        if self.direction not in _VALID_DIRECTIONS:
            raise ValueError(
                f"direction must be one of {_VALID_DIRECTIONS!r}, got {self.direction!r}"
            )


class BadgeLog:
    def __init__(self, path: Path):
        self.audit = AuditLog(path)

    def record(self, ev: BadgeEvent):
        return self.audit.append({
            "type": "badge",
            **{k: getattr(ev, k) for k in (
                "badge_id", "holder_name", "ts", "direction",
                "location", "escort_for", "visitor_id",
            )},
        })

    def currently_inside(self) -> set[str]:
        inside: set[str] = set()
        if not self.audit.path.exists():
            return inside
        for line in self.audit.path.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
                e = entry["event"]
            except (json.JSONDecodeError, KeyError):
                continue
            if e.get("type") != "badge":
                continue
            direction = e.get("direction")
            badge_id = e.get("badge_id")
            if not badge_id:
                continue
            if direction == "in":
                inside.add(badge_id)
            elif direction == "out":
                inside.discard(badge_id)
        return inside


# Two-Person Integrity primitive
def verify_tpi(
    operator1: str, operator2: str, action: str, audit: AuditLog
) -> tuple[bool, str]:
    """Return (allowed, reason). Operators must differ; logs to audit."""
    if not operator1 or not operator2:
        audit.append({"type": "tpi", "action": action, "result": "deny",
                      "reason": "missing operator"})
        return False, "Both operators required"
    if operator1 == operator2:
        audit.append({"type": "tpi", "action": action, "result": "deny",
                      "reason": "same operator"})
        return False, "Operators must be different individuals"
    audit.append({"type": "tpi", "action": action, "result": "allow",
                  "operator1": operator1, "operator2": operator2})
    return True, "Approved"


# GSA container inspection cadence (public — Federal Standards 809/809A)
GSA_INSPECTION_CADENCE_DAYS = 365  # annual external inspection per public std


def days_until_inspection(
    last_inspection_ts: float,
    cadence_days: int = GSA_INSPECTION_CADENCE_DAYS,
) -> int:
    """Return days remaining until next inspection (negative = overdue).

    Raises ValueError if cadence_days <= 0.
    """
    if cadence_days <= 0:
        raise ValueError(f"cadence_days must be positive, got {cadence_days}")
    elapsed = (time.time() - last_inspection_ts) / 86400
    return int(cadence_days - elapsed)


def _parse_badge_log_lines(log_path: Path) -> list[dict]:
    """Return parsed event dicts from a badge JSONL file, skipping bad lines."""
    events: list[dict] = []
    try:
        text = log_path.read_text(encoding="utf-8")
    except OSError:
        return events
    for line in text.splitlines():
        try:
            entry = json.loads(line)
            e = entry["event"]
        except (json.JSONDecodeError, KeyError):
            continue
        events.append(e)
    return events


def scan(target=".", **opts):
    """Scan a SCIF ops directory: badge logs + container records."""
    r = ScanResult(tool_name="scifops", tool_version="0.1.0")
    p = Path(target)

    if not p.exists():
        r.finalize()
        return r

    r.items_scanned = 0

    # Badge log analysis
    for log_path in p.glob("badge*.jsonl"):
        r.items_scanned += 1
        bl = BadgeLog(log_path)
        try:
            ok, msg = bl.audit.verify()
        except OSError as exc:
            r.add(Finding(
                f"SO-CHAIN-{log_path.stem}", Severity.VERY_HIGH,
                f"Could not read audit log: {exc}",
                location=str(log_path),
                remediation="Verify file permissions and integrity",
            ))
            continue

        if not ok:
            r.add(Finding(
                f"SO-CHAIN-{log_path.stem}", Severity.VERY_HIGH,
                f"Tamper-evident chain broken: {msg}",
                location=str(log_path),
                remediation=(
                    "Immediate IR — preserve log; brief security officer"
                ),
            ))

        inside = bl.currently_inside()
        if inside:
            r.add(Finding(
                f"SO-INSIDE-{log_path.stem}", Severity.MODERATE,
                f"{len(inside)} badges currently inside (per log)",
                location=str(log_path),
                description=f"Badges: {sorted(inside)[:5]}",
                remediation="Confirm with physical walkthrough",
            ))

        # Detect unescorted visitor pattern (visitor in without escort_for)
        for e in _parse_badge_log_lines(log_path):
            if (
                e.get("type") == "badge"
                and e.get("visitor_id")
                and not e.get("escort_for")
            ):
                r.add(Finding(
                    "SO-NOESCORT", Severity.VERY_HIGH,
                    f"Visitor {e['visitor_id']} entered without escort_for",
                    location=str(log_path),
                    remediation=(
                        "Halt; refer to ICD 705 / DoDM 5105.21 §4.3 "
                        "visitor procedures"
                    ),
                ))

    # GSA container records
    for cfg in p.glob("containers*.json"):
        r.items_scanned += 1
        try:
            containers = json.loads(cfg.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            r.add(Finding(
                f"SO-PARSE-{cfg.stem}", Severity.HIGH,
                f"Could not parse container file: {exc}",
                location=str(cfg),
                remediation="Verify JSON syntax in container record file",
            ))
            continue

        if not isinstance(containers, list):
            r.add(Finding(
                f"SO-PARSE-{cfg.stem}", Severity.HIGH,
                "Container file must be a JSON array",
                location=str(cfg),
                remediation="Correct container record file format",
            ))
            continue

        for c in containers:
            if not isinstance(c, dict):
                continue
            try:
                days = days_until_inspection(
                    float(c.get("last_inspection_ts", 0))
                )
            except (ValueError, TypeError):
                continue
            container_id = c.get("id", "?")
            if days < 0:
                r.add(Finding(
                    f"SO-INSP-{container_id}", Severity.HIGH,
                    f"Container {container_id} overdue inspection by {-days} days",
                    location=str(cfg),
                    remediation="Schedule inspection per Federal Std 809A",
                ))
            elif days < 30:
                r.add(Finding(
                    f"SO-INSPSOON-{container_id}", Severity.LOW,
                    f"Container {container_id} inspection due in {days} days",
                    location=str(cfg),
                ))

    r.finalize()
    return r
