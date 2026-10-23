import pytest

from modules.page_replacement import PageReplacementSimulator


def test_algorithms_match_reference_fault_counts_and_trace():
    sim = PageReplacementSimulator([1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5], 3)
    fifo, lru, optimal = sim.fifo(), sim.lru(), sim.optimal()
    assert [fifo["page_faults"], lru["page_faults"], optimal["page_faults"]] == [9, 10, 7]
    assert [fifo["hits"], lru["hits"], optimal["hits"]] == [3, 2, 5]
    assert all(len(row["frame_snapshots"]) == 12 for row in (fifo, lru, optimal))
    assert all(len(row["outcomes"]) == 12 for row in (fifo, lru, optimal))


def test_empty_sequence_is_a_valid_zero_result():
    result = PageReplacementSimulator([], 2).fifo()
    assert result["page_faults"] == 0
    assert result["hit_ratio"] == 0


@pytest.mark.parametrize("capacity", [0, -1, 1.5])
def test_invalid_frame_capacity_rejected(capacity):
    with pytest.raises(ValueError):
        PageReplacementSimulator([1], capacity)


def test_invalid_reference_rejected():
    with pytest.raises(ValueError):
        PageReplacementSimulator([1, -2], 3)
