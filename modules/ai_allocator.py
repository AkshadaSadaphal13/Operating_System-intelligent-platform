"""Transparent, non-executing resource allocation recommendations."""

from math import isfinite


class AIResourceAllocator:
    """Rule-based policy that reports recommendations and never applies them."""

    THRESHOLDS = {"cpu_high_pct": 85.0, "memory_high_pct": 85.0,
                  "memory_critical_pct": 95.0, "queue_wait_high_seconds": 10.0}

    @staticmethod
    def _validate(name, value, maximum=None):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError(f"{name} must be a finite number.")
        if value < 0 or (maximum is not None and value > maximum):
            suffix = f" and at most {maximum}" if maximum is not None else ""
            raise ValueError(f"{name} must be non-negative{suffix}.")

    def recommend(self, cpu_pct, ram_pct, page_faults, wait_time, available_memory_pct=None):
        for name, value, maximum in (("cpu_pct", cpu_pct, 100), ("ram_pct", ram_pct, 100),
                                     ("page_faults", page_faults, None), ("wait_time", wait_time, None)):
            self._validate(name, value, maximum)
        if available_memory_pct is not None:
            self._validate("available_memory_pct", available_memory_pct, 100)

        t = self.THRESHOLDS
        action, priority = "MAINTAIN", "normal"
        reasons = ["CPU and memory usage are within configured pressure thresholds."]
        if ram_pct >= t["memory_critical_pct"] or (ram_pct >= t["memory_high_pct"] and page_faults >= 50):
            action, priority = "PROTECT_MEMORY", "critical"
            reasons = ["Memory pressure is high and page-fault activity indicates contention.",
                       "Consider reducing nonessential workload or increasing an approved memory limit."]
        elif cpu_pct >= t["cpu_high_pct"] and wait_time >= t["queue_wait_high_seconds"]:
            action, priority = "REVIEW_CPU_CAPACITY", "high"
            reasons = ["CPU usage and queue wait both exceed thresholds.",
                       "Review CPU shares or schedule the workload for a less busy period."]
        elif wait_time >= t["queue_wait_high_seconds"] and cpu_pct < 60:
            action, priority = "REVIEW_CPU_PRIORITY", "medium"
            reasons = ["Queue wait is high while CPU use is moderate; the workload may be waiting for a fair share."]
        elif available_memory_pct is not None and available_memory_pct < 10:
            action, priority = "CONSERVE_MEMORY", "high"
            reasons = ["Available memory is below 10%; defer optional allocations and inspect memory consumers."]
        return {
            "action": action, "priority": priority, "reasons": reasons,
            "inputs": {"cpu_pct": float(cpu_pct), "ram_pct": float(ram_pct),
                       "page_faults": float(page_faults), "wait_time": float(wait_time),
                       "available_memory_pct": available_memory_pct},
            "thresholds": dict(t), "simulated": True,
            "performed_action": False,
            "notice": "Recommendation only. No process was terminated and no OS setting was changed.",
        }

    def evaluate_process(self, cpu_pct, ram_pct, page_faults, wait_time):
        """Backward-compatible text interface for existing callers."""
        result = self.recommend(cpu_pct, ram_pct, page_faults, wait_time)
        return f"{result['action']}: {' '.join(result['reasons'])} {result['notice']}"


if __name__ == "__main__":
    print(AIResourceAllocator().recommend(90, 96, 80, 15, available_memory_pct=4))
