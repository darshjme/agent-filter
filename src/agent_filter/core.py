"""Core components: Filter, PredicateFilter, Transformer, Pipeline."""

from __future__ import annotations

import re
from typing import Any, Callable


class Filter:
    """Base filter interface. Subclass and override apply()."""

    def __init__(self, name: str | None = None) -> None:
        self.name = name or self.__class__.__name__

    def apply(self, items: list[Any]) -> list[Any]:
        """Return filtered list. Default: identity (no-op)."""
        return list(items)

    def __call__(self, items: list[Any]) -> list[Any]:
        return self.apply(items)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class PredicateFilter(Filter):
    """Keeps items where predicate(item) is True."""

    def __init__(self, predicate: Callable[[Any], bool], name: str | None = None) -> None:
        super().__init__(name or "PredicateFilter")
        if not callable(predicate):
            raise TypeError("predicate must be callable")
        self.predicate = predicate

    def apply(self, items: list[Any]) -> list[Any]:
        return [item for item in items if self.predicate(item)]


class Transformer(Filter):
    """Maps each item through transform_fn. Does not remove items."""

    def __init__(self, transform_fn: Callable[[Any], Any], name: str | None = None) -> None:
        super().__init__(name or "Transformer")
        if not callable(transform_fn):
            raise TypeError("transform_fn must be callable")
        self.transform_fn = transform_fn

    def apply(self, items: list[Any]) -> list[Any]:
        return [self.transform_fn(item) for item in items]


# ---------------------------------------------------------------------------
# Built-in step factories (returned as Filter/Transformer instances)
# ---------------------------------------------------------------------------

class _DedupFilter(Filter):
    """Remove duplicate items while preserving first-seen order."""

    def apply(self, items: list[Any]) -> list[Any]:
        seen: list[Any] = []
        for item in items:
            if item not in seen:
                seen.append(item)
        return seen


class _StripEmptyFilter(Filter):
    """Remove None values and empty strings."""

    def apply(self, items: list[Any]) -> list[Any]:
        return [item for item in items if item is not None and item != ""]


class _TruncateTransformer(Transformer):
    """Truncate string items to max_length characters."""

    def __init__(self, max_length: int) -> None:
        if max_length < 0:
            raise ValueError("max_length must be >= 0")
        super().__init__(
            transform_fn=lambda item: item[:max_length] if isinstance(item, str) else item,
            name=f"Truncate(max={max_length})",
        )


class _LimitFilter(Filter):
    """Keep only first n items."""

    def __init__(self, n: int) -> None:
        if n < 0:
            raise ValueError("n must be >= 0")
        super().__init__(name=f"Limit(n={n})")
        self.n = n

    def apply(self, items: list[Any]) -> list[Any]:
        return list(items[: self.n])


class _RegexFilter(Filter):
    """Keep string items matching the given regex pattern."""

    def __init__(self, pattern: str) -> None:
        super().__init__(name=f"RegexFilter(pattern={pattern!r})")
        self._pattern = re.compile(pattern)

    def apply(self, items: list[Any]) -> list[Any]:
        return [item for item in items if isinstance(item, str) and self._pattern.search(item)]


class _KeywordExcludeFilter(Filter):
    """Remove string items that contain any of the given keywords (case-insensitive)."""

    def __init__(self, words: list[str]) -> None:
        super().__init__(name=f"KeywordExclude(words={words!r})")
        self._words = [w.lower() for w in words]

    def apply(self, items: list[Any]) -> list[Any]:
        result = []
        for item in items:
            if isinstance(item, str):
                lower = item.lower()
                if not any(w in lower for w in self._words):
                    result.append(item)
            else:
                result.append(item)
        return result


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class Pipeline:
    """Chain filters and transformers. Items pass through each step in order."""

    def __init__(self, steps: list[Filter | Transformer] | None = None) -> None:
        self._steps: list[Filter | Transformer] = list(steps) if steps else []

    def add(self, step: Filter | Transformer) -> "Pipeline":
        """Append a step and return self (fluent API)."""
        self._steps.append(step)
        return self

    def run(self, items: list[Any]) -> list[Any]:
        """Pass items through all steps in order."""
        result = list(items)
        for step in self._steps:
            result = step.apply(result)
        return result

    def __call__(self, items: list[Any]) -> list[Any]:
        return self.run(items)

    def __repr__(self) -> str:
        return f"Pipeline(steps={self._steps!r})"

    # ------------------------------------------------------------------
    # Built-in step factory class methods
    # ------------------------------------------------------------------

    @classmethod
    def dedup(cls) -> _DedupFilter:
        """Return a filter that removes duplicate items."""
        return _DedupFilter(name="Dedup")

    @classmethod
    def truncate(cls, max_length: int) -> _TruncateTransformer:
        """Return a transformer that truncates string items to max_length."""
        return _TruncateTransformer(max_length)

    @classmethod
    def strip_empty(cls) -> _StripEmptyFilter:
        """Return a filter that removes None and empty-string items."""
        return _StripEmptyFilter(name="StripEmpty")

    @classmethod
    def limit(cls, n: int) -> _LimitFilter:
        """Return a filter that keeps only the first n items."""
        return _LimitFilter(n)

    @classmethod
    def regex_filter(cls, pattern: str) -> _RegexFilter:
        """Return a filter that keeps strings matching the regex pattern."""
        return _RegexFilter(pattern)

    @classmethod
    def keyword_exclude(cls, words: list[str]) -> _KeywordExcludeFilter:
        """Return a filter that removes strings containing any keyword."""
        return _KeywordExcludeFilter(words)
