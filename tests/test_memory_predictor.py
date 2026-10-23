import pytest

from modules.memory_predictor import MemoryPredictor


def test_persistence_forecast_and_compatibility_interface():
    predictor = MemoryPredictor()
    result = predictor.forecast([20, 30, 45], future_steps=3)
    assert result["method"] == "persistence baseline"
    assert result["predictions"] == [45.0, 45.0, 45.0]
    assert predictor.train_and_predict([20, 30, 45], 2) == [45.0, 45.0]


def test_rolling_evaluation_metrics():
    result = MemoryPredictor().evaluate([10, 12, 15])
    assert result["actual"] == [12.0, 15.0]
    assert result["predicted"] == [10.0, 12.0]
    assert result["mae"] == 2.5
    assert result["rmse"] == pytest.approx((13 / 2) ** 0.5, abs=0.0001)


@pytest.mark.parametrize("history", [[], [-1, 2], [101], [float("nan")]])
def test_invalid_history_rejected(history):
    with pytest.raises(ValueError):
        MemoryPredictor().forecast(history)


def test_one_measurement_can_forecast_but_not_be_evaluated():
    predictor = MemoryPredictor()
    assert predictor.forecast([44], 1)["predictions"] == [44.0]
    with pytest.raises(ValueError, match="two measurements"):
        predictor.evaluate([44])
