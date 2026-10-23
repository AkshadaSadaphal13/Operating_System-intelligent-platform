"""Bounded parser for common timestamped application and system log lines."""

from collections import Counter
import re

import pandas as pd


class LogAnalyzer:
    MAX_TEXT_BYTES = 5_000_000
    PATTERN = re.compile(
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})\s+"
        r"(?:\[(?P<bracket_level>DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL)\]|"
        r"(?P<plain_level>DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL))\s*[:\]-]?\s*(?P<message>.*)$",
        re.IGNORECASE,
    )
    LEVELS = ("DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL")

    @classmethod
    def parse_logs(cls, log_text, max_bytes=None):
        if not isinstance(log_text, str):
            raise TypeError("log_text must be text.")
        limit = cls.MAX_TEXT_BYTES if max_bytes is None else max_bytes
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("max_bytes must be a positive integer.")
        encoded = log_text.encode("utf-8", errors="replace")
        if len(encoded) > limit:
            raise ValueError(f"Log input exceeds the {limit:,}-byte safety limit.")
        parsed = []
        malformed = []
        for number, line in enumerate(log_text.splitlines(), start=1):
            if not line.strip():
                continue
            match = cls.PATTERN.match(line.strip())
            if not match:
                malformed.append({"line": number, "text": line[:500]})
                continue
            level = (match.group("bracket_level") or match.group("plain_level")).upper()
            if level == "WARNING":
                level = "WARN"
            parsed.append({
                "timestamp": match.group("timestamp"), "level": level,
                "message": match.group("message").strip(), "line": number,
            })
        df = pd.DataFrame(parsed, columns=["timestamp", "level", "message", "line"])
        summary = {level: int((df["level"] == level).sum()) for level in ("DEBUG", "INFO", "WARN", "ERROR", "CRITICAL")}
        recurring = Counter(row["message"] for row in parsed)
        repeated = [{"message": message, "count": count}
                    for message, count in recurring.most_common() if count > 1]
        summary.update({
            "total_parsed": len(parsed), "malformed_lines": len(malformed),
            "error_like": summary["ERROR"] + summary["CRITICAL"],
            "recurring_patterns": repeated,
            "unusual_events": [row for row in parsed if row["level"] in ("ERROR", "CRITICAL")],
            "malformed": malformed,
        })
        return df, summary


if __name__ == "__main__":
    sample = "2026-08-05 10:00:01 [INFO] System booted.\n2026-08-05 10:05:12 [WARNING] High memory."
    frame, result = LogAnalyzer.parse_logs(sample)
    print(frame.to_string(index=False))
    print(result)
