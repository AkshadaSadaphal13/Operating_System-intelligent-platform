from pathlib import Path

from modules.ai_allocator import AIResourceAllocator
from modules.cpu_scheduler import CPUScheduler
from modules.deadlock_detector import BankerAlgorithm
from modules.log_analyzer import LogAnalyzer
from modules.memory_predictor import MemoryPredictor
from modules.page_replacement import PageReplacementSimulator


def test_analysis_modules_produce_dashboard_ready_results():
    schedule, recommendation = CPUScheduler([
        {"pid": "A", "burst": 4, "arrival": 0, "priority": 1},
        {"pid": "B", "burst": 2, "arrival": 1, "priority": 2},
    ]).recommend_best(quantum=2)
    forecast = MemoryPredictor().forecast([40, 45, 50], 2)
    banker = BankerAlgorithm([1, 1], [[1, 0], [0, 1]], [[1, 1], [1, 1]])
    deadlock = banker.detect_deadlock([[0, 1], [1, 0]])
    pages = PageReplacementSimulator([1, 2, 1, 3], 2).lru()
    _, logs = LogAnalyzer.parse_logs("2026-01-01 10:00:00 [ERROR] Example failure")
    allocation = AIResourceAllocator().recommend(90, 50, 2, 12)

    assert len(schedule) == 4 and "simulation" in recommendation.lower()
    assert forecast["predictions"] == [50.0, 50.0]
    assert deadlock["deadlocked"] is True
    assert pages["page_faults"] == 3
    assert logs["error_like"] == 1
    assert allocation["performed_action"] is False


def test_streamlit_app_starts_and_navigation_renders():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
    assert not app.exception
    assert "Performance Dashboard" in [option for option in app.sidebar.radio[0].options]
    for page in ["Process Monitoring", "CPU Scheduling", "Memory Prediction", "Deadlock Analysis",
                 "Page Replacement", "Log Analysis", "Resource Allocation", "Performance Dashboard"]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, f"Streamlit page failed: {page}"
        if page == "CPU Scheduling":
            assert any("CPU Scheduling Recommendation" in str(element.value) for element in app.title)
            next(button for button in app.button if button.label == "Compare scheduling policies").click().run()
        elif page == "Memory Prediction":
            next(button for button in app.button if button.label == "Load demonstration series").click().run()
            next(button for button in app.button if button.label == "Evaluate and forecast").click().run()
        elif page == "Deadlock Analysis":
            next(button for button in app.button if button.label == "Analyze resource state").click().run()
        elif page == "Page Replacement":
            next(button for button in app.button if button.label == "Run page replacement").click().run()
        elif page == "Log Analysis":
            next(button for button in app.button if button.label == "Analyze logs").click().run()
        elif page == "Resource Allocation":
            next(button for button in app.button if button.label == "Generate recommendation").click().run()
        assert not app.exception, f"Module workflow failed on {page}"

