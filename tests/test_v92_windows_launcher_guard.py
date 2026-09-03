from app.main import _filter_external_multibot_coordinators


COMMAND = "python -m app.main --mode multi-bot-daemon --execute"


def test_python_launcher_parent_is_not_a_duplicate():
    rows = [
        {"ProcessId": 5000, "ParentProcessId": 4000, "Name": "python.exe", "CommandLine": COMMAND},
        {"ProcessId": 6332, "ParentProcessId": 5000, "Name": "python.exe", "CommandLine": COMMAND},
        {"ProcessId": 7000, "ParentProcessId": 6332, "Name": "python.exe", "CommandLine": COMMAND},
    ]
    assert _filter_external_multibot_coordinators(rows, 7000, 6332) == []


def test_independent_coordinator_is_detected_but_own_launcher_is_excluded():
    rows = [
        {"ProcessId": 6332, "ParentProcessId": 5000, "Name": "python.exe", "CommandLine": COMMAND},
        {"ProcessId": 7000, "ParentProcessId": 6332, "Name": "python.exe", "CommandLine": COMMAND},
        {"ProcessId": 22636, "ParentProcessId": 8100, "Name": "python.exe", "CommandLine": COMMAND},
    ]
    found = _filter_external_multibot_coordinators(rows, 7000, 6332)
    assert [row["ProcessId"] for row in found] == [22636]


def test_workers_and_unrelated_python_are_not_coordinators():
    rows = [
        {"ProcessId": 9001, "ParentProcessId": 7000, "Name": "python.exe", "CommandLine": "python -m app.main --mode boom-daemon --coordinated-worker"},
        {"ProcessId": 9002, "ParentProcessId": 7000, "Name": "python.exe", "CommandLine": "python other.py"},
    ]
    assert _filter_external_multibot_coordinators(rows, 7000, 6332) == []
