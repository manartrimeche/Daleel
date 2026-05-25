"""Tests for roadmap_service — topological sort and roadmap generation."""

from app.services.roadmap_service import _topological_sort, _LEVEL_ORDER


class TestTopologicalSort:
    def test_empty_actions(self):
        result = _topological_sort([], [], {})
        assert result == []

    def test_single_action_no_deps(self):
        result = _topological_sort(["a1"], [], {})
        assert result == ["a1"]

    def test_simple_chain(self):
        deps = [
            {"action_id": "a2", "depends_on_id": "a1"},
            {"action_id": "a3", "depends_on_id": "a2"},
        ]
        result = _topological_sort(["a1", "a2", "a3"], deps, {})
        assert result.index("a1") < result.index("a2")
        assert result.index("a2") < result.index("a3")

    def test_criticality_ordering_no_deps(self):
        crit_map = {
            "a1": {"level": "secondaire", "score": 0.3},
            "a2": {"level": "critique", "score": 0.9},
            "a3": {"level": "importante", "score": 0.6},
        }
        result = _topological_sort(["a1", "a2", "a3"], [], crit_map)
        assert result[0] == "a2"
        assert result[1] == "a3"
        assert result[2] == "a1"

    def test_dependency_with_criticality(self):
        deps = [{"action_id": "a2", "depends_on_id": "a1"}]
        crit_map = {
            "a1": {"level": "secondaire", "score": 0.2},
            "a2": {"level": "critique", "score": 0.95},
            "a3": {"level": "importante", "score": 0.7},
        }
        result = _topological_sort(["a1", "a2", "a3"], deps, crit_map)
        assert result.index("a1") < result.index("a2")

    def test_cycle_detection_appends_remaining(self):
        deps = [
            {"action_id": "a1", "depends_on_id": "a2"},
            {"action_id": "a2", "depends_on_id": "a1"},
        ]
        result = _topological_sort(["a1", "a2", "a3"], deps, {})
        assert "a3" in result
        assert len(result) == 3

    def test_deps_referencing_outside_actions_ignored(self):
        deps = [{"action_id": "a1", "depends_on_id": "unknown"}]
        result = _topological_sort(["a1", "a2"], deps, {})
        assert set(result) == {"a1", "a2"}

    def test_diamond_dependency(self):
        deps = [
            {"action_id": "b", "depends_on_id": "a"},
            {"action_id": "c", "depends_on_id": "a"},
            {"action_id": "d", "depends_on_id": "b"},
            {"action_id": "d", "depends_on_id": "c"},
        ]
        result = _topological_sort(["a", "b", "c", "d"], deps, {})
        assert result.index("a") < result.index("b")
        assert result.index("a") < result.index("c")
        assert result.index("b") < result.index("d")
        assert result.index("c") < result.index("d")


class TestLevelOrder:
    def test_all_levels_present(self):
        assert "critique" in _LEVEL_ORDER
        assert "importante" in _LEVEL_ORDER
        assert "secondaire" in _LEVEL_ORDER
        assert "unknown" in _LEVEL_ORDER

    def test_critique_is_highest_priority(self):
        assert _LEVEL_ORDER["critique"] < _LEVEL_ORDER["importante"]
        assert _LEVEL_ORDER["importante"] < _LEVEL_ORDER["secondaire"]
