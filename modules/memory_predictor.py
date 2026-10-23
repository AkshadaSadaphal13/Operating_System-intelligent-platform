"""Small-data memory forecasting with an explicit persistence baseline."""

from math import isfinite

import numpy as np


class MemoryPredictor:
    """Forecast future percentages by carrying the latest observation forward.

    The persistence baseline is deliberately used instead of fitting an ML model:
    the app has no verified training dataset or stable sampling cadence.
    """

    @staticmethod
    def _validate(history_usage, future_steps=None):
        values = list(history_usage)
        if not values:
            raise ValueError("Provide at least one historical memory measurement.")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or not 0 <= value <= 100 for value in values):
            raise ValueError("Memory measurements must be finite percentages from 0 to 100.")
        if future_steps is not None and (isinstance(future_steps, bool) or not isinstance(future_steps, int) or not 1 <= future_steps <= 1000):
            raise ValueError("future_steps must be an integer from 1 to 1000.")
        return [float(value) for value in values]

    def forecast(self, history_usage, future_steps=5):
        history = self._validate(history_usage, future_steps)
        predictions = [round(history[-1], 2)] * future_steps
        return {"history": history, "predictions": predictions, "method": "persistence baseline"}

    def train_and_predict(self, history_usage, future_steps=5):
        """Compatibility interface retained for callers of the original module."""
        return self.forecast(history_usage, future_steps)["predictions"]

    def evaluate(self, history_usage):
        """One-step rolling-origin evaluation against the previous-value baseline."""
        history = self._validate(history_usage)
        if len(history) < 2:
            raise ValueError("At least two measurements are required for evaluation.")
        actual = history[1:]
        predicted = history[:-1]
        errors = np.asarray(actual, dtype=float) - np.asarray(predicted, dtype=float)
        return {
            "actual": actual,
            "predicted": predicted,
            "mae": round(float(np.mean(np.abs(errors))), 4),
            "rmse": round(float(np.sqrt(np.mean(errors ** 2))), 4),
            "samples": len(actual),
            "method": "one-step rolling persistence baseline",
        }


if __name__ == "__main__":
    values = [30.5, 32.0, 35.1, 40.2, 42.8, 45.0, 49.3]
    predictor = MemoryPredictor()
    print("Evaluation:", predictor.evaluate(values))
    print("Forecast:", predictor.forecast(values, future_steps=3))
