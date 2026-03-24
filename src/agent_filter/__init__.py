"""agent-filter: composable data filtering and transformation pipeline for agent outputs."""

from .core import Filter, PredicateFilter, Transformer, Pipeline

__version__ = "1.0.0"
__all__ = ["Filter", "PredicateFilter", "Transformer", "Pipeline"]
