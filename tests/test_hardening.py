"""Tests for hardened error-handling and edge-case paths in scifops."""
import json
import subprocess
import sys
import time

import pytest

from scifops.core import (
    BadgeEvent,
    days_until_inspection,
    scan,
)


# ---------------------------------------------------------------------------
# BadgeEvent validation
# ---------------------------------------------------------------------------

def test_badge_event_invalid_direction():
    """BadgeEvent rejects directions other than 'in' or 'out'."""
    with pytest.raises(ValueError, match="direction"):
        BadgeEvent("B1", "Alice", time.time(), "sideways")


def test_badge_event_empty_badge_id():
    """BadgeEvent rejects an empty badge_id."""
    with pytest.raises(ValueError, match="badge_id"):
        BadgeEvent("", "Alice", time.time(), "in")


# ---------------------------------------------------------------------------
# days_until_inspection guard
# ---------------------------------------------------------------------------

def test_days_until_inspection_zero_cadence():
    """days_until_inspection raises ValueError for cadence_days <= 0."""
    with pytest.raises(ValueError, match="cadence_days"):
        days_until_inspection(time.time(), cadence_days=0)


def test_days_until_inspection_negative_cadence():
    with pytest.raises(ValueError, match="cadence_days"):
        days_until_inspection(time.time(), cadence_days=-5)


# ---------------------------------------------------------------------------
# scan() with missing / non-existent target
# ---------------------------------------------------------------------------

def test_scan_nonexistent_target():
    """scan() on a missing directory returns empty results, not an exception."""
    r = scan("/nonexistent/path/xyz_scifops_test")
    assert r.items_scanned == 0
    assert r.findings == []


def test_scan_empty_directory(tmp_path):
    """scan() on an empty directory finds nothing and does not raise."""
    r = scan(str(tmp_path))
    assert r.items_scanned == 0
    assert r.findings == []


# ---------------------------------------------------------------------------
# Malformed input files
# ---------------------------------------------------------------------------

def test_scan_malformed_badge_jsonl(tmp_path):
    """scan() skips corrupt lines in badge JSONL and doesn't crash."""
    (tmp_path / "badge_test.jsonl").write_text(
        "not-json\n{\"broken\":\n", encoding="utf-8"
    )
    r = scan(str(tmp_path))
    assert r.items_scanned == 1
    # Chain verify fails on malformed JSON — a VERY_HIGH finding is raised
    # but no unhandled exception should escape.
    assert isinstance(r.findings, list)


def test_scan_malformed_containers_json(tmp_path):
    """scan() produces a parse-error Finding for invalid containers JSON."""
    (tmp_path / "containers_bad.json").write_text("{invalid json", encoding="utf-8")
    r = scan(str(tmp_path))
    assert r.items_scanned == 1
    ids = {f.id for f in r.findings}
    assert any("PARSE" in fid for fid in ids)


def test_scan_containers_not_a_list(tmp_path):
    """scan() produces a parse-error Finding when containers JSON is not an array."""
    (tmp_path / "containers_obj.json").write_text(
        json.dumps({"id": "X"}), encoding="utf-8"
    )
    r = scan(str(tmp_path))
    ids = {f.id for f in r.findings}
    assert any("PARSE" in fid for fid in ids)


def test_scan_container_missing_inspection_ts(tmp_path):
    """scan() handles containers missing last_inspection_ts gracefully."""
    containers = [{"id": "GSA-NO-TS"}]
    (tmp_path / "containers_nots.json").write_text(
        json.dumps(containers), encoding="utf-8"
    )
    # last_inspection_ts defaults to 0 (epoch), so container is long overdue
    r = scan(str(tmp_path))
    ids = {f.id for f in r.findings}
    assert "SO-INSP-GSA-NO-TS" in ids


# ---------------------------------------------------------------------------
# CLI: bad target -> non-zero exit, no traceback
# ---------------------------------------------------------------------------

def test_cli_missing_target_exits_cleanly(tmp_path):
    """CLI on a missing target exits 0 (nothing to scan) with no traceback."""
    result = subprocess.run(
        [sys.executable, "-m", "scifops", "/nonexistent/xyz_cli_test"],
        capture_output=True,
        text=True,
    )
    # Should not crash with a Python traceback
    assert "Traceback" not in result.stderr
    assert result.returncode == 0


def test_cli_version_flag():
    """CLI --version flag prints version and exits 0."""
    result = subprocess.run(
        [sys.executable, "-m", "scifops", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout or "0.1.0" in result.stderr
