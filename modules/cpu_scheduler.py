"""CPU scheduling simulations. These routines do not change OS scheduling."""

from collections import deque
from math import isfinite


class CPUScheduler:
    """Simulate FCFS, non-preemptive SJF/priority, and Round Robin workloads."""

    def __init__(self, processes):
        self.processes = [dict(process) for process in processes]
        self._validate()

    def _validate(self):
        if not self.processes:
            raise ValueError("At least one process is required.")
        ids = set()
        for index, process in enumerate(self.processes):
            for key in ("burst", "arrival"):
                if key not in process:
                    raise ValueError(f"Process {index + 1} is missing {key!r}.")
                value = process[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                    raise ValueError(f"{key} must be a finite number.")
                if value < 0 or (key == "burst" and value == 0):
                    raise ValueError(f"{key} must be {'positive' if key == 'burst' else 'non-negative'}.")
            pid = str(process.get("pid", f"P{index + 1}")).strip()
            if not pid or pid in ids:
                raise ValueError("Process IDs must be non-empty and unique.")
            ids.add(pid)
            process["pid"] = pid
            process.setdefault("priority", 0)
            if isinstance(process["priority"], bool) or not isinstance(process["priority"], (int, float)):
                raise ValueError("priority must be numeric (lower values run first).")

    def _result(self, name, starts, completions):
        rows = []
        for i, process in enumerate(self.processes):
            burst, arrival = process["burst"], process["arrival"]
            turnaround = completions[i] - arrival
            rows.append({
                "pid": process["pid"], "arrival": arrival, "burst": burst,
                "priority": process["priority"], "start": starts[i],
                "completion": completions[i], "waiting": turnaround - burst,
                "turnaround": turnaround, "response": starts[i] - arrival,
            })
        averages = {
            "avg_wait": round(sum(row["waiting"] for row in rows) / len(rows), 2),
            "avg_tat": round(sum(row["turnaround"] for row in rows) / len(rows), 2),
            "avg_turnaround": round(sum(row["turnaround"] for row in rows) / len(rows), 2),
            "avg_response": round(sum(row["response"] for row in rows) / len(rows), 2),
        }
        return {"algorithm": name, "processes": rows, **averages}

    def _non_preemptive(self, name, key):
        pending = set(range(len(self.processes)))
        starts, completions = {}, {}
        now = 0
        while pending:
            ready = [i for i in pending if self.processes[i]["arrival"] <= now]
            if not ready:
                now = min(self.processes[i]["arrival"] for i in pending)
                ready = [i for i in pending if self.processes[i]["arrival"] <= now]
            index = min(ready, key=lambda i: (key(self.processes[i]), self.processes[i]["arrival"], i))
            process = self.processes[index]
            starts[index] = now
            now += process["burst"]
            completions[index] = now
            pending.remove(index)
        return self._result(name, starts, completions)

    def fcfs(self):
        return self._non_preemptive("FCFS", lambda p: p["arrival"])

    def sjf(self):
        return self._non_preemptive("SJF", lambda p: p["burst"])

    def priority(self):
        return self._non_preemptive("Priority", lambda p: p["priority"])

    def round_robin(self, quantum=2):
        if isinstance(quantum, bool) or not isinstance(quantum, (int, float)) or not isfinite(quantum) or quantum <= 0:
            raise ValueError("Round Robin quantum must be a positive finite number.")
        order = sorted(range(len(self.processes)), key=lambda i: (self.processes[i]["arrival"], i))
        remaining = [p["burst"] for p in self.processes]
        starts, completions = {}, {}
        ready = deque()
        now = 0
        cursor = 0
        while cursor < len(order) or ready:
            if not ready:
                now = max(now, self.processes[order[cursor]]["arrival"])
                while cursor < len(order) and self.processes[order[cursor]]["arrival"] <= now:
                    ready.append(order[cursor])
                    cursor += 1
            index = ready.popleft()
            starts.setdefault(index, now)
            duration = min(quantum, remaining[index])
            end = now + duration
            while cursor < len(order) and self.processes[order[cursor]]["arrival"] <= end:
                ready.append(order[cursor])
                cursor += 1
            now = end
            remaining[index] -= duration
            if remaining[index] > 0:
                ready.append(index)
            else:
                completions[index] = now
        return self._result("Round Robin", starts, completions)

    def compare(self, quantum=2):
        return [self.fcfs(), self.sjf(), self.priority(), self.round_robin(quantum)]

    def recommend_best(self, quantum=2):
        """Recommend a simulated policy from workload shape and measured outcomes."""
        results = self.compare(quantum)
        bursts = [p["burst"] for p in self.processes]
        priorities = [p["priority"] for p in self.processes]
        if len(set(priorities)) > 1:
            preferred = next(result for result in results if result["algorithm"] == "Priority")
            rationale = "distinct priorities were provided (lower number means higher priority)"
        elif max(bursts) / min(bursts) >= 2:
            preferred = next(result for result in results if result["algorithm"] == "SJF")
            rationale = "burst times vary substantially, so SJF favors short jobs"
        elif any(p["burst"] > quantum for p in self.processes):
            preferred = next(result for result in results if result["algorithm"] == "Round Robin")
            rationale = "the workload includes longer jobs, so Round Robin improves time sharing"
        else:
            preferred = min(results, key=lambda result: (result["avg_wait"], result["avg_response"]))
            rationale = "this workload has similar short bursts; the recommendation minimizes simulated waiting time"
        message = (f"Recommended {preferred['algorithm']}: {rationale}. "
                   "This is a simulation; it does not change the operating system scheduler.")
        return results, message


if __name__ == "__main__":
    sample = [
        {"pid": "P1", "burst": 6, "arrival": 0, "priority": 2},
        {"pid": "P2", "burst": 2, "arrival": 1, "priority": 1},
        {"pid": "P3", "burst": 8, "arrival": 2, "priority": 3},
    ]
    results, recommendation = CPUScheduler(sample).recommend_best(quantum=2)
    print(results)
    print(recommendation)
