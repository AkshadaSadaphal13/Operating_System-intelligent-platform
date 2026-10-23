import numpy as np
import pytest

from modules.deadlock_detector import BankerAlgorithm


TOTAL = [10, 5, 7]
ALLOC = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
MAX = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]


def test_textbook_banker_state_is_safe():
    banker = BankerAlgorithm(TOTAL, ALLOC, MAX)
    safe, sequence, _ = banker.check_safety_state()
    assert safe
    assert len(sequence) == 5
    assert set(sequence) == {f"P{i}" for i in range(5)}


def test_multi_instance_detection_finds_wait_cycle_deadlock():
    banker = BankerAlgorithm([1, 1], [[1, 0], [0, 1]], [[1, 1], [1, 1]])
    request = [[0, 1], [1, 0]]
    result = banker.detect_deadlock(request)
    assert result["deadlocked"] is True
    assert result["processes"] == ["P0", "P1"]
    assert banker.wait_for_graph(request) == {"P0": ["P1"], "P1": ["P0"]}


def test_no_outstanding_requests_means_no_current_deadlock():
    banker = BankerAlgorithm([2], [[1], [1]], [[2], [2]])
    assert banker.detect_deadlock(np.zeros((2, 1), dtype=int))["deadlocked"] is False


def test_bad_resource_matrices_rejected():
    with pytest.raises(ValueError):
        BankerAlgorithm([1], [[2]], [[2]])
    with pytest.raises(ValueError):
        BankerAlgorithm([1], [[0]], [[1, 2]])
    with pytest.raises(ValueError):
        BankerAlgorithm([1.5], [[0]], [[1]])
