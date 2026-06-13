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
import time, json
from dataclasses import dataclass
from pathlib import Path
from cognis_mil import ScanResult, Finding, Severity, AuditLog

@dataclass
class BadgeEvent:
    badge_id: str
    holder_name: str
    ts: float
    direction: str       # "in" or "out"
    location: str = "MAIN"
    escort_for: str = ""  # if non-empty, this person is escorting a visitor
    visitor_id: str = ""

class BadgeLog:
    def __init__(self, path: Path):
        self.audit = AuditLog(path)

    def record(self, ev: BadgeEvent):
        return self.audit.append({
            "type":"badge", **{k:getattr(ev,k) for k in ("badge_id","holder_name","ts","direction","location","escort_for","visitor_id")}
        })

    def currently_inside(self) -> set[str]:
        inside = set()
        if not self.audit.path.exists(): return inside
        for line in self.audit.path.read_text().splitlines():
            try: e = json.loads(line)["event"]
            except: continue
            if e.get("type") != "badge": continue
            if e.get("direction") == "in": inside.add(e.get("badge_id"))
            elif e.get("direction") == "out": inside.discard(e.get("badge_id"))
        return inside

# Two-Person Integrity primitive
def verify_tpi(operator1: str, operator2: str, action: str, audit: AuditLog) -> tuple[bool, str]:
    """Return (allowed, reason). Operators must differ; logs to audit."""
    if not operator1 or not operator2:
        audit.append({"type":"tpi","action":action,"result":"deny","reason":"missing operator"})
        return False, "Both operators required"
    if operator1 == operator2:
        audit.append({"type":"tpi","action":action,"result":"deny","reason":"same operator"})
        return False, "Operators must be different individuals"
    audit.append({"type":"tpi","action":action,"result":"allow",
                  "operator1":operator1,"operator2":operator2})
    return True, "Approved"

# GSA container inspection cadence (public — Federal Standards 809/809A)
GSA_INSPECTION_CADENCE_DAYS = 365  # annual external inspection per public std

def days_until_inspection(last_inspection_ts: float, cadence_days: int = GSA_INSPECTION_CADENCE_DAYS) -> int:
    elapsed = (time.time() - last_inspection_ts) / 86400
    return int(cadence_days - elapsed)

def scan(target=".", **opts):
    """Scan a SCIF ops directory: badge logs + container records."""
    r = ScanResult(tool_name="scifops", tool_version="0.1.0")
    p = Path(target)
    r.items_scanned = 0
    # Badge log analysis
    for log_path in p.glob("badge*.jsonl"):
        r.items_scanned += 1
        bl = BadgeLog(log_path)
        ok, msg = bl.audit.verify()
        if not ok:
            r.add(Finding(f"SO-CHAIN-{log_path.stem}", Severity.VERY_HIGH,
                          f"Tamper-evident chain broken: {msg}",
                          location=str(log_path),
                          remediation="Immediate IR — preserve log; brief security officer"))
        inside = bl.currently_inside()
        if inside:
            r.add(Finding(f"SO-INSIDE-{log_path.stem}", Severity.MODERATE,
                          f"{len(inside)} badges currently inside (per log)",
                          location=str(log_path),
                          description=f"Badges: {sorted(inside)[:5]}",
                          remediation="Confirm with physical walkthrough"))
        # Detect unescorted visitor pattern (visitor in without escort_for)
        if log_path.exists():
            for line in log_path.read_text().splitlines():
                try: e = json.loads(line)["event"]
                except: continue
                if e.get("type")=="badge" and e.get("visitor_id") and not e.get("escort_for"):
                    r.add(Finding("SO-NOESCORT", Severity.VERY_HIGH,
                                  f"Visitor {e['visitor_id']} entered without escort_for",
                                  location=str(log_path),
                                  remediation="Halt; refer to ICD 705 / DoDM 5105.21 §4.3 visitor procedures"))
    # GSA container records
    for cfg in p.glob("containers*.json"):
        r.items_scanned += 1
        try: containers = json.loads(cfg.read_text())
        except: continue
        for c in containers:
            days = days_until_inspection(c.get("last_inspection_ts", 0))
            if days < 0:
                r.add(Finding(f"SO-INSP-{c.get('id','?')}", Severity.HIGH,
                              f"Container {c.get('id')} overdue inspection by {-days} days",
                              location=str(cfg),
                              remediation="Schedule inspection per Federal Std 809A"))
            elif days < 30:
                r.add(Finding(f"SO-INSPSOON-{c.get('id','?')}", Severity.LOW,
                              f"Container {c.get('id')} inspection due in {days} days",
                              location=str(cfg)))
    r.finalize(); return r
