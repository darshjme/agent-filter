# Contributing

Thank you for your interest in contributing to `agent-filter`!

## Development Setup

```bash
git clone https://github.com/example/agent-filter
cd agent-filter
pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Guidelines

- All new features must include tests.
- Keep zero runtime dependencies.
- Follow PEP 8 and type-annotate all public APIs.
- Open an issue before submitting large PRs.

## Pull Request Process

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes with clear messages.
4. Push and open a pull request.
5. Ensure all CI checks pass.
