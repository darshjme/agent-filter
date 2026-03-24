"""22+ pytest tests for agent-filter."""

import pytest
from agent_filter import Filter, PredicateFilter, Transformer, Pipeline


# ============================================================
# Filter (base)
# ============================================================

class TestFilter:
    def test_default_name(self):
        f = Filter()
        assert f.name == "Filter"

    def test_custom_name(self):
        f = Filter(name="MyFilter")
        assert f.name == "MyFilter"

    def test_apply_identity(self):
        f = Filter()
        items = [1, 2, 3]
        assert f.apply(items) == [1, 2, 3]

    def test_call_is_alias(self):
        f = Filter()
        items = ["a", "b"]
        assert f(items) == f.apply(items)

    def test_apply_returns_new_list(self):
        f = Filter()
        items = [1, 2, 3]
        result = f.apply(items)
        result.append(99)
        assert items == [1, 2, 3]  # original unchanged


# ============================================================
# PredicateFilter
# ============================================================

class TestPredicateFilter:
    def test_keeps_matching(self):
        pf = PredicateFilter(lambda x: x > 2)
        assert pf.apply([1, 2, 3, 4]) == [3, 4]

    def test_empty_result(self):
        pf = PredicateFilter(lambda x: False)
        assert pf.apply([1, 2, 3]) == []

    def test_all_pass(self):
        pf = PredicateFilter(lambda x: True)
        assert pf.apply([1, 2, 3]) == [1, 2, 3]

    def test_string_predicate(self):
        pf = PredicateFilter(lambda s: s.startswith("ok"))
        result = pf.apply(["ok good", "bad", "ok also"])
        assert result == ["ok good", "ok also"]

    def test_non_callable_raises(self):
        with pytest.raises(TypeError):
            PredicateFilter("not_callable")

    def test_custom_name(self):
        pf = PredicateFilter(lambda x: x, name="MyPred")
        assert pf.name == "MyPred"

    def test_call_alias(self):
        pf = PredicateFilter(lambda x: x % 2 == 0)
        assert pf([1, 2, 3, 4]) == [2, 4]


# ============================================================
# Transformer
# ============================================================

class TestTransformer:
    def test_maps_items(self):
        t = Transformer(lambda x: x * 2)
        assert t.apply([1, 2, 3]) == [2, 4, 6]

    def test_string_upper(self):
        t = Transformer(str.upper)
        assert t.apply(["hello", "world"]) == ["HELLO", "WORLD"]

    def test_empty_input(self):
        t = Transformer(lambda x: x + 1)
        assert t.apply([]) == []

    def test_non_callable_raises(self):
        with pytest.raises(TypeError):
            Transformer(42)

    def test_custom_name(self):
        t = Transformer(lambda x: x, name="Doubler")
        assert t.name == "Doubler"

    def test_call_alias(self):
        t = Transformer(lambda x: x.strip())
        assert t([" a ", " b "]) == ["a", "b"]


# ============================================================
# Pipeline
# ============================================================

class TestPipeline:
    def test_empty_pipeline(self):
        p = Pipeline()
        assert p.run([1, 2, 3]) == [1, 2, 3]

    def test_add_fluent(self):
        p = Pipeline()
        result = p.add(Pipeline.strip_empty()).add(Pipeline.dedup())
        assert result is p  # fluent returns self

    def test_call_alias(self):
        p = Pipeline([Pipeline.dedup()])
        assert p([1, 1, 2]) == p.run([1, 1, 2])

    def test_steps_constructor(self):
        p = Pipeline(steps=[Pipeline.limit(2)])
        assert p.run([10, 20, 30]) == [10, 20]

    # --- dedup ---
    def test_dedup(self):
        f = Pipeline.dedup()
        assert f.apply([1, 2, 1, 3, 2]) == [1, 2, 3]

    def test_dedup_preserves_order(self):
        f = Pipeline.dedup()
        assert f.apply(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]

    # --- strip_empty ---
    def test_strip_empty(self):
        f = Pipeline.strip_empty()
        assert f.apply([None, "", "hello", None, "world"]) == ["hello", "world"]

    def test_strip_empty_keeps_zeros(self):
        f = Pipeline.strip_empty()
        assert f.apply([0, False, None, ""]) == [0, False]

    # --- truncate ---
    def test_truncate(self):
        t = Pipeline.truncate(5)
        assert t.apply(["hello world", "hi"]) == ["hello", "hi"]

    def test_truncate_non_strings_pass_through(self):
        t = Pipeline.truncate(3)
        assert t.apply([42, "hello"]) == [42, "hel"]

    def test_truncate_negative_raises(self):
        with pytest.raises(ValueError):
            Pipeline.truncate(-1)

    # --- limit ---
    def test_limit(self):
        f = Pipeline.limit(3)
        assert f.apply([1, 2, 3, 4, 5]) == [1, 2, 3]

    def test_limit_zero(self):
        f = Pipeline.limit(0)
        assert f.apply([1, 2, 3]) == []

    def test_limit_negative_raises(self):
        with pytest.raises(ValueError):
            Pipeline.limit(-1)

    # --- regex_filter ---
    def test_regex_filter(self):
        f = Pipeline.regex_filter(r"\d+")
        assert f.apply(["abc", "123", "x9y", "no"]) == ["123", "x9y"]

    def test_regex_filter_no_match(self):
        f = Pipeline.regex_filter(r"^ZZZ")
        assert f.apply(["hello", "world"]) == []

    # --- keyword_exclude ---
    def test_keyword_exclude(self):
        f = Pipeline.keyword_exclude(["spam", "ads"])
        items = ["buy now ads!", "good content", "spam alert", "clean"]
        assert f.apply(items) == ["good content", "clean"]

    def test_keyword_exclude_case_insensitive(self):
        f = Pipeline.keyword_exclude(["SPAM"])
        assert f.apply(["This is SPAM", "this is fine"]) == ["this is fine"]

    # --- composed pipeline ---
    def test_full_pipeline(self):
        """Simulate cleaning agent output."""
        raw = [
            "  Great answer!  ",
            "",
            None,
            "hallucinated data xyz",
            "clean result one",
            "clean result one",  # duplicate
            "another clean result",
        ]
        pipeline = (
            Pipeline()
            .add(Pipeline.strip_empty())
            .add(Transformer(lambda x: x.strip() if isinstance(x, str) else x))
            .add(Pipeline.keyword_exclude(["hallucinated"]))
            .add(Pipeline.dedup())
        )
        result = pipeline.run(raw)
        assert None not in result
        assert "" not in result
        assert all("hallucinated" not in r for r in result)
        assert len(result) == len(set(result))  # no duplicates

    def test_pipeline_limit_and_truncate(self):
        items = ["alpha", "beta", "gamma", "delta"]
        pipeline = Pipeline().add(Pipeline.truncate(3)).add(Pipeline.limit(2))
        assert pipeline.run(items) == ["alp", "bet"]
