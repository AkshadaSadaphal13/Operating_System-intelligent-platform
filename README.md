# OS Intelligent Analytics and Resource Management Platform

A Streamlit application for live process and system monitoring, operating-system algorithm demonstrations, log analysis, and transparent resource recommendations. Simulators do not alter operating-system behavior.

## Features

- **Process monitoring:** live CPU, memory, disk, and process metrics from `psutil`.
- **CPU scheduling:** FCFS, non-preemptive SJF, non-preemptive priority, and Round Robin with per-process waiting, turnaround, response, and completion times.
- **Memory forecasting:** a persistence baseline, live memory sampling, one-step actual-versus-predicted evaluation, MAE, and RMSE. No training dataset is bundled, so the app does not claim an ML model.
- **Deadlock analysis:** Banker's safe-state analysis, multi-instance outstanding-request detection, and a wait-for dependency view.
- **Page replacement:** FIFO, LRU, and Optimal with fault/hit ratios and per-reference traces.
- **Log analysis:** bounded parsing for common ISO-timestamped records, severity totals, recurring messages, unusual events, and malformed-line reporting.
- **Performance dashboard:** live system summary plus results from modules run in the current Streamlit session.
- **Resource allocation:** explainable threshold recommendations. No action is applied to a process or system setting.

## Requirements

- Python 3.10–3.13
- pip

## Run locally

From the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

On macOS or Linux, activate with `source .venv/bin/activate` instead.

## Run tests

```powershell
python -m pytest -q
```

## Run with Docker

```powershell
docker build -t os-intelligent-platform .
docker run --rm -p 8501:8501 os-intelligent-platform
```

Open `http://localhost:8501` in a browser.

## Demonstration notes

Scheduling and page replacement are simulations. The memory predictor uses a persistence baseline because this repository has no validated dataset. For resource analysis, the default Banker matrices are an editable textbook example. Page-fault frequency and queue wait in the resource recommendation page must be supplied by the presenter; the app does not collect those OS counters. Process monitoring depends on permissions and platform facilities exposed to the current Python process.
