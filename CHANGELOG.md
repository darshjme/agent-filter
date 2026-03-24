# Changelog

All notable changes to `agent-filter` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-01

### Added
- `Filter` base class with identity `apply()` and `__call__` alias
- `PredicateFilter` — keep items matching a callable predicate
- `Transformer` — map each item through a transform function
- `Pipeline` — chain filters and transformers with fluent `.add()` API
- Built-in steps: `dedup`, `strip_empty`, `truncate`, `limit`, `regex_filter`, `keyword_exclude`
- Full pytest test suite (22+ tests)
- Zero runtime dependencies
