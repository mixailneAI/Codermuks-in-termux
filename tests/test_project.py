from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from core.project import Project
from core.workspace import delete_project


class TestProject:
    def test_create(self):
        p = Project.create("test-proj-create", language="python")
        try:
            assert p.exists
            assert p.language == "python"
        finally:
            delete_project(p.name)

    def test_write_read(self):
        p = Project.create("test-proj-io", "python")
        try:
            p.write_file("main.py", "print('hi')")
            assert p.read_file("main.py") == "print('hi')"
            assert p.file_exists("main.py")
        finally:
            delete_project(p.name)

    def test_path_traversal(self):
        p = Project.create("test-proj-sec", "python")
        try:
            with pytest.raises(ValueError):
                p.write_file("../evil.txt", "hack")
        finally:
            delete_project(p.name)

    def test_list_files(self):
        p = Project.create("test-proj-list", "python")
        try:
            p.write_file("a.py", "a")
            p.write_file("sub/b.py", "b")
            files = p.list_files()
            assert "a.py" in files
            assert "sub/b.py" in files
        finally:
            delete_project(p.name)

    def test_add_task(self):
        p = Project.create("test-proj-task", "python")
        try:
            p.add_task("test query", "success", provider="mistral")
            tasks = p.get_recent_tasks()
            assert len(tasks) == 1
            assert tasks[0]["query"] == "test query"
        finally:
            delete_project(p.name)
