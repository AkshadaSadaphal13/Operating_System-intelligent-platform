"""Streamlit interface for OS analytics and algorithm demonstrations."""

import logging
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules.ai_allocator import AIResourceAllocator
from modules.cpu_scheduler import CPUScheduler
from modules.deadlock_detector import BankerAlgorithm
from modules.log_analyzer import LogAnalyzer
from modules.memory_predictor import MemoryPredictor
from modules.page_replacement import PageReplacementSimulator
from modules.process_monitor import ProcessMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("os_platform")

st.set_page_config(page_title="Intelligent OS Analytics", page_icon="🖥️", layout="wide")
PAGES = [
    "Performance Dashboard", "Process Monitoring", "CPU Scheduling",
    "Memory Prediction", "Deadlock Analysis", "Page Replacement",
    "Log Analysis", "Resource Allocation",
]


def _init_state():
    defaults = {
        "scheduler_results": None, "scheduler_recommendation": None,
        "memory_forecast": None, "deadlock_result": None,
        "page_results": None, "log_result": None, "allocation_result": None,
        "memory_samples": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _safe_process_data(limit=50):
    try:
        return ProcessMonitor.get_system_summary(), ProcessMonitor.get_process_list(top_n=limit)
    except Exception as exc:
        logger.exception("Could not collect system telemetry")
        st.error(f"System telemetry is unavailable: {exc}")
        return None, pd.DataFrame()


def _metric_row(summary):
    a, b, c, d = st.columns(4)
    a.metric("CPU usage", f"{summary['cpu_percent']:.1f}%")
    b.metric("Memory usage", f"{summary['memory_percent']:.1f}%",
             f"{summary['memory_used_gb']:.2f} / {summary['memory_total_gb']:.2f} GB")
    c.metric("Disk usage", f"{summary['disk_percent']:.1f}%")
    d.metric("Processes collected", summary.get("process_count", "—"))


def _stored_result(label, key):
    value = st.session_state.get(key)
    if value is None:
        st.caption(f"{label}: run that module to add results to this dashboard.")
    else:
        st.write(f"**{label}:** {value}")


def render_dashboard():
    st.title("OS Performance Dashboard")
    st.caption("Live system telemetry with results from analyses run in this session.")
    summary, processes = _safe_process_data()
    if summary is not None:
        _metric_row(summary)
        if not processes.empty:
            st.subheader("Processes using the most memory")
            st.dataframe(processes, use_container_width=True, hide_index=True)
    st.subheader("Module results")
    left, right = st.columns(2)
    with left:
        _stored_result("CPU scheduling", "scheduler_recommendation")
        _stored_result("Memory forecast", "memory_forecast")
        _stored_result("Deadlock analysis", "deadlock_result")
    with right:
        _stored_result("Log summary", "log_result")
        _stored_result("Resource recommendation", "allocation_result")
        page_data = st.session_state.get("page_results")
        _stored_result("Page replacement", "page_summary")
    if page_data:
        chart = pd.DataFrame([{"Algorithm": row["algorithm"], "Faults": row["page_faults"], "Hits": row["hits"]}
                              for row in page_data])
        st.plotly_chart(px.bar(chart, x="Algorithm", y=["Faults", "Hits"], barmode="group"), use_container_width=True)


def render_process_monitor():
    st.title("Process Monitoring")
    interval = st.slider("CPU sampling interval (seconds)", 0.1, 2.0, 0.5, 0.1)
    search = st.text_input("Filter by process name or PID")
    limit = st.slider("Maximum processes", 10, 200, 50, 10)
    if st.button("Refresh process snapshot", type="primary"):
        st.rerun()
    try:
        summary = ProcessMonitor.get_system_summary(cpu_interval=interval)
        processes = ProcessMonitor.get_process_list(top_n=limit)
    except Exception as exc:
        logger.exception("Process snapshot failed")
        st.error(f"Could not collect process information: {exc}")
        return
    _metric_row(summary)
    if search:
        mask = processes["name"].str.contains(search, case=False, na=False) | processes["pid"].astype(str).str.contains(search, na=False)
        processes = processes[mask]
    st.subheader("Processes")
    st.dataframe(processes, use_container_width=True, hide_index=True,
                 column_config={"memory_percent": st.column_config.ProgressColumn("Memory %", min_value=0, max_value=100),
                                "cpu_percent": st.column_config.NumberColumn("CPU %", format="%.1f")})
    if not processes.empty:
        st.plotly_chart(px.bar(processes.head(10), x="name", y="memory_percent", title="Top process memory usage"), use_container_width=True)


def render_scheduler():
    st.title("CPU Scheduling Recommendation")
    st.warning("All results are workload simulations. No operating-system scheduling policy is changed.")
    demo = pd.DataFrame([
        {"pid": "P1", "burst": 6, "arrival": 0, "priority": 2},
        {"pid": "P2", "burst": 2, "arrival": 1, "priority": 1},
        {"pid": "P3", "burst": 8, "arrival": 2, "priority": 3},
    ])
    st.caption("Edit the sample workload or replace it with your own. Lower numeric priority runs first.")
    workload = st.data_editor(demo, key="scheduler_workload", num_rows="dynamic", use_container_width=True)
    quantum = st.number_input("Round Robin time quantum", min_value=1, max_value=1000, value=2)
    if st.button("Compare scheduling policies", type="primary"):
        try:
            records = workload.to_dict("records")
            results, recommendation = CPUScheduler(records).recommend_best(int(quantum))
            st.session_state.scheduler_results = results
            st.session_state.scheduler_recommendation = recommendation
        except (TypeError, ValueError, KeyError) as exc:
            st.error(f"Invalid workload: {exc}")
    results = st.session_state.scheduler_results
    if results:
        st.success(st.session_state.scheduler_recommendation)
        frame = pd.DataFrame([{k: r[k] for k in ("algorithm", "avg_wait", "avg_tat", "avg_response")} for r in results])
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.plotly_chart(px.bar(frame.melt(id_vars="algorithm", var_name="Metric", value_name="Time"),
                               x="algorithm", y="Time", color="Metric", barmode="group"), use_container_width=True)
        chosen = st.selectbox("Inspect per-process metrics", [r["algorithm"] for r in results])
        row = next(result for result in results if result["algorithm"] == chosen)
        st.dataframe(pd.DataFrame(row["processes"]), use_container_width=True, hide_index=True)


def render_memory():
    st.title("Memory Usage Prediction")
    st.info("Small-data baseline: persistence forecast (the next value equals the latest observation). No trained ML model or external dataset is present.")
    if st.button("Record current system memory usage"):
        try:
            import psutil
            st.session_state.memory_samples.append({"timestamp": datetime.now().isoformat(timespec="seconds"),
                                                    "usage": float(psutil.virtual_memory().percent)})
            st.success("Recorded a live memory measurement.")
        except Exception as exc:
            logger.exception("Could not record memory sample")
            st.error(f"Could not read current memory usage: {exc}")
    if st.session_state.memory_samples:
        st.caption("Live samples recorded in this session")
        st.dataframe(pd.DataFrame(st.session_state.memory_samples), use_container_width=True, hide_index=True)
    use_live_samples = st.checkbox("Use recorded live samples as forecast history",
                                    disabled=not bool(st.session_state.memory_samples))
    raw = st.text_area("Historical memory usage (%) — comma-separated", value="", placeholder="e.g. 35.5, 38.0, 42.1, 45.0", key="memory_input")
    with st.expander("Load labeled demonstration series"):
        st.button("Load demonstration series", on_click=lambda: setattr(
            st.session_state, "memory_input", "35.5, 38.0, 42.1, 45.0, 52.3, 58.0"))
        st.caption("The series is illustrative input for demonstrating the baseline, not collected telemetry.")
    horizon = st.slider("Forecast steps", 1, 20, 5)
    if st.button("Evaluate and forecast", type="primary"):
        try:
            history = ([sample["usage"] for sample in st.session_state.memory_samples]
                       if use_live_samples else [float(part.strip()) for part in raw.split(",") if part.strip()])
            predictor = MemoryPredictor()
            forecast = predictor.forecast(history, horizon)
            evaluation = predictor.evaluate(history) if len(history) >= 2 else None
            st.session_state.memory_forecast = f"{forecast['predictions'][0]:.1f}% persistence forecast; MAE {evaluation['mae']:.2f}%" if evaluation else f"{forecast['predictions'][0]:.1f}% persistence forecast; evaluation needs 2+ observations"
            st.session_state.memory_forecast_data = {"forecast": forecast, "evaluation": evaluation}
        except (TypeError, ValueError) as exc:
            st.error(f"Cannot calculate forecast: {exc}")
    data = st.session_state.get("memory_forecast_data")
    if data:
        forecast, evaluation = data["forecast"], data["evaluation"]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(1, len(forecast["history"]) + 1)), y=forecast["history"], mode="lines+markers", name="Observed"))
        fig.add_trace(go.Scatter(x=list(range(len(forecast["history"]), len(forecast["history"]) + len(forecast["predictions"]) + 1)),
                                 y=[forecast["history"][-1], *forecast["predictions"]], mode="lines+markers", name="Forecast"))
        st.plotly_chart(fig, use_container_width=True)
        if evaluation:
            st.caption(f"Rolling one-step evaluation: MAE {evaluation['mae']:.3f} percentage points, RMSE {evaluation['rmse']:.3f}; {evaluation['samples']} evaluation samples.")
            actual = pd.DataFrame({"Step": range(2, len(evaluation["actual"]) + 2), "Actual": evaluation["actual"], "Predicted": evaluation["predicted"]})
            st.dataframe(actual, use_container_width=True, hide_index=True)


def render_deadlock():
    st.title("Deadlock and Safe-State Analysis")
    st.caption("Banker's safety uses maximum claims. Deadlock detection uses current outstanding requests. An unsafe state is a risk condition, not proof that a deadlock is currently occurring.")
    resources = st.number_input("Number of resource types", min_value=1, max_value=5, value=3)
    processes = st.number_input("Number of processes", min_value=1, max_value=10, value=5)
    rcols = [f"R{i + 1}" for i in range(int(resources))]
    pids = [f"P{i}" for i in range(int(processes))]
    alloc_default = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
    max_default = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
    if resources == 3 and processes == 5:
        alloc = pd.DataFrame(alloc_default, columns=rcols, index=pids)
        maximum = pd.DataFrame(max_default, columns=rcols, index=pids)
        total_default = [10, 5, 7]
    else:
        alloc = pd.DataFrame(0, index=pids, columns=rcols)
        maximum = pd.DataFrame(1, index=pids, columns=rcols)
        total_default = [int(processes)] * int(resources)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Current allocation")
        alloc_edit = st.data_editor(alloc, key="deadlock_alloc", use_container_width=True)
        st.subheader("Current outstanding requests")
        request_edit = st.data_editor(pd.DataFrame(0, index=pids, columns=rcols), key="deadlock_request", use_container_width=True)
    with c2:
        st.subheader("Maximum claims")
        max_edit = st.data_editor(maximum, key="deadlock_max", use_container_width=True)
        totals = [st.number_input(f"Total {resource}", min_value=0, max_value=100000, value=total_default[i], key=f"resource_total_{i}") for i, resource in enumerate(rcols)]
    if st.button("Analyze resource state", type="primary"):
        try:
            banker = BankerAlgorithm(totals, alloc_edit.to_numpy(), max_edit.to_numpy())
            safe, sequence, message = banker.check_safety_state()
            deadlock = banker.detect_deadlock(request_edit.to_numpy())
            graph = banker.wait_for_graph(request_edit.to_numpy())
            st.session_state.deadlock_result = f"{'Safe' if safe else 'Unsafe'}; {'deadlock' if deadlock['deadlocked'] else 'no current deadlock'}"
            st.session_state.deadlock_data = {"safe": safe, "sequence": sequence, "message": message, "deadlock": deadlock, "graph": graph}
        except (TypeError, ValueError, IndexError) as exc:
            st.error(f"Invalid resource matrices: {exc}")
    result = st.session_state.get("deadlock_data")
    if result:
        st.success(result["message"]) if result["safe"] else st.error(result["message"])
        st.write(result["deadlock"]["message"])
        if result["sequence"]:
            st.write("Safe sequence:", " → ".join(result["sequence"]))
        st.subheader("Wait-for dependencies (blocked processes)")
        st.json(result["graph"])


def render_pages():
    st.title("Page Replacement Simulation")
    st.caption("Algorithm simulation only; this does not alter physical memory or OS page tables.")
    raw = st.text_input("Page reference sequence", "7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3")
    capacity = st.slider("Frame count", 1, 20, 3)
    if st.button("Run page replacement", type="primary"):
        try:
            pages = [int(part.strip()) for part in raw.split(",") if part.strip()]
            if not pages:
                raise ValueError("Enter at least one page reference.")
            sim = PageReplacementSimulator(pages, capacity)
            st.session_state.page_results = [sim.fifo(), sim.lru(), sim.optimal()]
            st.session_state.page_summary = "; ".join(
                f"{result['algorithm']}: {result['page_faults']} faults" for result in st.session_state.page_results)
        except (TypeError, ValueError) as exc:
            st.error(f"Invalid reference string: {exc}")
    results = st.session_state.page_results
    if results:
        metrics = pd.DataFrame([{k: item[k] for k in ("algorithm", "page_faults", "hits", "hit_ratio")} for item in results])
        st.dataframe(metrics, use_container_width=True, hide_index=True)
        selected = st.selectbox("Replacement-step trace", [item["algorithm"] for item in results])
        selected_result = next(item for item in results if item["algorithm"] == selected)
        frames = max((len(snapshot) for snapshot in selected_result["frame_snapshots"]), default=0)
        pages = [int(x.strip()) for x in raw.split(",") if x.strip()]
        trace = []
        for index, snapshot in enumerate(selected_result["frame_snapshots"]):
            trace.append({"Step": index + 1, "Page": pages[index],
                          "Result": selected_result["outcomes"][index],
                          **{f"Frame {n + 1}": snapshot[n] if n < len(snapshot) else "—" for n in range(max(capacity, frames))}})
        st.dataframe(pd.DataFrame(trace), use_container_width=True, hide_index=True)


def render_logs():
    st.title("Log Analysis")
    st.caption(f"Up to {LogAnalyzer.MAX_TEXT_BYTES // 1_000_000} MB per analysis. Common ISO-timestamped INFO/WARN/ERROR/CRITICAL records are recognized; malformed lines are counted.")
    mode = st.radio("Log source", ["Paste or use sample", "Upload a log file"], horizontal=True)
    sample = ("2026-08-05 10:00:01 [INFO] Kernel initialized successfully.\n"
              "2026-08-05 10:02:14 [WARN] Memory pressure threshold exceeded.\n"
              "2026-08-05 10:05:00 [ERROR] Out of memory: process 2041 terminated.\n"
              "2026-08-05 10:10:00 [CRITICAL] Deadlock state detected on resource R2.")
    if mode == "Paste or use sample":
        text = st.text_area("Log text", sample, height=180)
    else:
        upload = st.file_uploader("Choose a .log or .txt file", type=["log", "txt"])
        text = ""
        if upload is not None:
            blob = upload.getvalue()
            if len(blob) > LogAnalyzer.MAX_TEXT_BYTES:
                st.error("The selected file exceeds the 5 MB safety limit.")
                return
            text = blob.decode("utf-8", errors="replace")
            bad_bytes = "�" in text
            if bad_bytes:
                st.warning("Some bytes were not valid UTF-8 and were replaced before parsing.")
    if st.button("Analyze logs", type="primary"):
        try:
            frame, summary = LogAnalyzer.parse_logs(text)
            st.session_state.log_data = {"frame": frame, "summary": summary}
            st.session_state.log_result = f"{summary['total_parsed']} parsed; {summary['error_like']} error/critical; {summary['malformed_lines']} malformed"
        except (TypeError, ValueError) as exc:
            st.error(f"Could not analyze logs: {exc}")
    data = st.session_state.get("log_data")
    if data:
        summary = data["summary"]
        cols = st.columns(4)
        for col, label in zip(cols, ("INFO", "WARN", "ERROR", "CRITICAL")):
            col.metric(label, summary[label])
        st.write(f"Parsed {summary['total_parsed']} records · {summary['malformed_lines']} malformed lines · {len(summary['recurring_patterns'])} recurring messages")
        st.subheader("Parsed events")
        st.dataframe(data["frame"], use_container_width=True, hide_index=True)
        with st.expander("Recurring patterns and unusual events"):
            st.json({"recurring_patterns": summary["recurring_patterns"], "unusual_events": summary["unusual_events"], "malformed": summary["malformed"][:100]})


def render_allocator():
    st.title("Resource Allocation Recommendations")
    st.caption("Rule-based and transparent. Recommendations are simulated; this module never terminates a process or changes system settings.")
    summary, _ = _safe_process_data(limit=1)
    if summary is None:
        cpu_default, ram_default = 0.0, 0.0
    else:
        cpu_default, ram_default = summary["cpu_percent"], summary["memory_percent"]
    c1, c2 = st.columns(2)
    cpu = c1.slider("System CPU usage (%)", 0, 100, int(cpu_default), key="alloc_cpu")
    ram = c2.slider("System memory usage (%)", 0, 100, int(ram_default), key="alloc_ram")
    faults = c1.number_input("Page faults per second (provide measured value)", min_value=0, max_value=1_000_000, value=0)
    wait = c2.number_input("Queue wait seconds (provide measured value)", min_value=0, max_value=1_000_000, value=0)
    st.caption("CPU and memory defaults are live system values. Page faults and wait time are user-supplied because this app does not collect those OS counters.")
    if st.button("Generate recommendation", type="primary"):
        try:
            decision = AIResourceAllocator().recommend(cpu, ram, faults, wait, available_memory_pct=100 - ram)
            st.session_state.allocation_data = decision
            st.session_state.allocation_result = f"{decision['priority'].title()} priority: {decision['action']} (simulated)"
        except ValueError as exc:
            st.error(f"Cannot make recommendation: {exc}")
    decision = st.session_state.get("allocation_data")
    if decision:
        st.subheader(f"{decision['action']} · {decision['priority']} priority")
        for reason in decision["reasons"]:
            st.write(f"- {reason}")
        st.info(decision["notice"])
        st.json({"inputs": decision["inputs"], "thresholds": decision["thresholds"], "performed_action": decision["performed_action"]})


_init_state()
st.sidebar.title("OS Analytics")
page = st.sidebar.radio("Modules", PAGES, key="navigation")
if page == "Performance Dashboard":
    render_dashboard()
elif page == "Process Monitoring":
    render_process_monitor()
elif page == "CPU Scheduling":
    render_scheduler()
elif page == "Memory Prediction":
    render_memory()
elif page == "Deadlock Analysis":
    render_deadlock()
elif page == "Page Replacement":
    render_pages()
elif page == "Log Analysis":
    render_logs()
elif page == "Resource Allocation":
    render_allocator()
