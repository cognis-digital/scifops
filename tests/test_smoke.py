import json, time
from pathlib import Path
from scifops.core import BadgeLog, BadgeEvent, verify_tpi, days_until_inspection, scan
from cognis_mil import AuditLog
D = Path(__file__).parent.parent / "demos"
def test_tpi_same_person(tmp_path):
    a = AuditLog(tmp_path / "a.jsonl")
    ok, _ = verify_tpi("alice","alice","destroy", a)
    assert not ok
def test_tpi_different(tmp_path):
    a = AuditLog(tmp_path / "a.jsonl")
    ok, _ = verify_tpi("alice","bob","destroy", a)
    assert ok
def test_badge_log_currently_inside(tmp_path):
    bl = BadgeLog(tmp_path / "b.jsonl")
    bl.record(BadgeEvent("B1","Alice", time.time(), "in"))
    bl.record(BadgeEvent("B2","Bob",   time.time(), "in"))
    bl.record(BadgeEvent("B1","Alice", time.time(), "out"))
    inside = bl.currently_inside()
    assert "B1" not in inside and "B2" in inside
def test_inspection_cadence():
    assert days_until_inspection(time.time()) > 360
    assert days_until_inspection(time.time() - 86400*400) < 0
def test_scan_demo():
    r = scan(str(D))
    ids = {f.id for f in r.findings}
    assert "SO-NOESCORT" in ids
    # Should flag the overdue container
    assert any("INSP-" in i for i in ids)
