from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.naming import (
    slugify,
    resolve_collision,
    similarity,
    find_similar,
    guess_project_name_from_query,
)


class TestSlugify:
    def test_basic(self):
        assert slugify("hello world") == "hello-world"

    def test_cyrillic(self):
        assert slugify("привет мир") == "privet-mir"

    def test_uppercase(self):
        assert slugify("HelloWorld") == "helloworld"

    def test_special_chars(self):
        assert slugify("hello!@#world") == "helloworld"

    def test_empty(self):
        assert slugify("") == "project"

    def test_only_specials(self):
        assert slugify("!!!") == "project"

    def test_long(self):
        long_name = "a" * 100
        assert len(slugify(long_name)) <= 50


class TestResolveCollision:
    def test_no_collision(self):
        assert resolve_collision("snake", []) == "snake"

    def test_one_collision(self):
        assert resolve_collision("snake", ["snake"]) == "snake-2"

    def test_two_collisions(self):
        assert resolve_collision("snake", ["snake", "snake-2"]) == "snake-3"


class TestSimilarity:
    def test_identical(self):
        assert similarity("abc", "abc") == 1.0

    def test_empty(self):
        assert similarity("", "abc") == 0.0

    def test_different(self):
        assert similarity("abc", "xyz") < 0.5


class TestFindSimilar:
    def test_exact(self):
        result = find_similar("calculator", ["calculator", "snake-game"])
        assert result and result[0][0] == "calculator"

    def test_none_found(self):
        result = find_similar("nonexistent", ["a", "b", "c"])
        assert result == []


class TestGuessName:
    def test_simple(self):
        name = guess_project_name_from_query("сделай калькулятор")
        assert "kalkulyator" in name or "calculator" in name

    def test_empty(self):
        assert guess_project_name_from_query("") == "project"
