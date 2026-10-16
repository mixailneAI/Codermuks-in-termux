from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.workspace import (
    create_project,
    delete_project,
    get_project_names,
    get_workspace_dir,
    list_projects,
    project_exists,
    read_metadata,
    write_metadata,
    update_metadata,
)


class TestWorkspace:
    def test_workspace_dir(self):
        ws = get_workspace_dir()
        assert ws.name == "codermuks-workspace"

    def test_create_and_delete(self):
        proj = create_project("test-ws-project", "python")
        try:
            assert proj.exists()
            assert project_exists(proj.name)
            meta = read_metadata(proj)
            assert meta["language"] == "python"
        finally:
            delete_project(proj.name)
        assert not project_exists(proj.name)

    def test_list_projects(self):
        proj = create_project("test-list", "python")
        try:
            names = get_project_names()
            assert "test-list" in names
            projects = list_projects()
            assert any(p["name"] == "test-list" for p in projects)
        finally:
            delete_project(proj.name)

    def test_update_metadata(self):
        proj = create_project("test-meta", "python")
        try:
            update_metadata(proj, language="go", last_task="test")
            meta = read_metadata(proj)
            assert meta["language"] == "go"
            assert meta["last_task"] == "test"
        finally:
            delete_project(proj.name)
