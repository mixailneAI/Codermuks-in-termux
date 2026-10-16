from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.history import (
    add_task,
    get_context_for_llm,
    get_recent,
    get_summary,
    get_tasks,
    load_history,
    save_history,
)
from core.workspace import create_project, delete_project


class TestHistory:
    def test_empty(self):
        proj = create_project("test-hist", "python")
        try:
            h = load_history(proj)
            assert h["tasks"] == []
        finally:
            delete_project(proj.name)

    def test_add_task(self):
        proj = create_project("test-hist-add", "python")
        try:
            add_task(proj, "query1", "success", provider="mistral")
            add_task(proj, "query2", "failure")
            tasks = get_tasks(proj)
            assert len(tasks) == 2
            assert tasks[0]["query"] == "query1"
            assert tasks[0]["result"] == "success"
        finally:
            delete_project(proj.name)

    def test_get_recent(self):
        proj = create_project("test-hist-recent", "python")
        try:
            for i in range(5):
                add_task(proj, f"q{i}", "success")
            recent = get_recent(proj, limit=2)
            assert len(recent) == 2
            assert recent[0]["query"] == "q4"
        finally:
            delete_project(proj.name)

    def test_summary(self):
        proj = create_project("test-hist-sum", "python")
        try:
            add_task(proj, "a", "success")
            add_task(proj, "b", "success")
            add_task(proj, "c", "failure")
            s = get_summary(proj)
            assert s["total_tasks"] == 3
            assert s["success"] == 2
            assert s["failure"] == 1
        finally:
            delete_project(proj.name)
