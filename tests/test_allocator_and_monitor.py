import pytest

from modules.ai_allocator import AIResourceAllocator
from modules.process_monitor import ProcessMonitor


def test_allocator_returns_explained_recommendation_without_action():
    result = AIResourceAllocator().recommend(90, 96, 80, 15, available_memory_pct=4)
    assert result["action"] == "PROTECT_MEMORY"
    assert result["priority"] == "critical"
    assert result["reasons"]
    assert result["simulated"] is True
    assert result["performed_action"] is False


def test_allocator_validates_metrics():
    with pytest.raises(ValueError):
        AIResourceAllocator().recommend(101, 20, 0, 0)
    with pytest.raises(ValueError):
        AIResourceAllocator().recommend(20, 20, -1, 0)


def test_process_monitor_returns_sensible_snapshot():
    summary = ProcessMonitor.get_system_summary(cpu_interval=0)
    processes = ProcessMonitor.get_process_list(top_n=5)
    assert 0 <= summary["memory_percent"] <= 100
    assert summary["memory_total_gb"] > 0
    assert len(processes) <= 5
    assert {"pid", "name", "cpu_percent", "memory_percent", "status"}.issubset(processes.columns)


def test_process_monitor_validates_sampling_interval():
    with pytest.raises(ValueError):
        ProcessMonitor.get_system_summary(cpu_interval=-1)
