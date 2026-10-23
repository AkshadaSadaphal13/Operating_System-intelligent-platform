import pytest

from modules.cpu_scheduler import CPUScheduler


WORKLOAD = [
    {"pid": "P1", "burst": 5, "arrival": 0, "priority": 2},
    {"pid": "P2", "burst": 3, "arrival": 1, "priority": 1},
    {"pid": "P3", "burst": 1, "arrival": 2, "priority": 3},
]


def test_all_policies_report_process_metrics_and_averages():
    scheduler = CPUScheduler(WORKLOAD)
    results = scheduler.compare(quantum=2)
    assert [result["algorithm"] for result in results] == ["FCFS", "SJF", "Priority", "Round Robin"]
    for result in results:
        assert len(result["processes"]) == 3
        assert result["avg_wait"] == pytest.approx(sum(p["waiting"] for p in result["processes"]) / 3, abs=0.01)
        assert result["avg_tat"] == pytest.approx(sum(p["turnaround"] for p in result["processes"]) / 3, abs=0.01)
        assert result["avg_response"] == pytest.approx(sum(p["response"] for p in result["processes"]) / 3, abs=0.01)


def test_round_robin_known_completion_and_recommendation_is_simulated():
    result = CPUScheduler(WORKLOAD).round_robin(2)
    by_pid = {row["pid"]: row for row in result["processes"]}
    assert {pid: row["completion"] for pid, row in by_pid.items()} == {"P1": 9, "P2": 8, "P3": 5}
    _, recommendation = CPUScheduler(WORKLOAD).recommend_best(2)
    assert "simulation" in recommendation.lower()
    assert "Priority" in recommendation


@pytest.mark.parametrize("workload", [[], [{"pid": "P1", "burst": 0, "arrival": 0}],
                                       [{"pid": "P1", "burst": 1, "arrival": -1}]])
def test_invalid_workloads_rejected(workload):
    with pytest.raises(ValueError):
        CPUScheduler(workload)


def test_invalid_quantum_rejected():
    with pytest.raises(ValueError):
        CPUScheduler(WORKLOAD).round_robin(0)
