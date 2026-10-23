import pytest

from modules.log_analyzer import LogAnalyzer


def test_severity_recurring_and_malformed_summary():
    text = "\n".join([
        "2026-01-01 10:00:00 [INFO] Started",
        "2026-01-01 10:01:00 [WARNING] Disk pressure",
        "2026-01-01 10:02:00 ERROR: Failed to open file",
        "2026-01-01 10:03:00 [ERROR] Failed to open file",
        "not a recognized record",
    ])
    frame, summary = LogAnalyzer.parse_logs(text)
    assert len(frame) == 4
    assert summary["WARN"] == 1
    assert summary["ERROR"] == 2
    assert summary["malformed_lines"] == 1
    assert summary["recurring_patterns"] == [{"message": "Failed to open file", "count": 2}]
    assert summary["error_like"] == 2


def test_empty_and_large_input_handling():
    frame, summary = LogAnalyzer.parse_logs("")
    assert frame.empty
    assert summary["INFO"] == summary["CRITICAL"] == 0
    with pytest.raises(ValueError, match="safety limit"):
        LogAnalyzer.parse_logs("x" * 20, max_bytes=10)


def test_input_type_and_limit_validation():
    with pytest.raises(TypeError):
        LogAnalyzer.parse_logs(b"bytes")
    with pytest.raises(ValueError):
        LogAnalyzer.parse_logs("ok", max_bytes=0)
