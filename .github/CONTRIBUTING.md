# Welcome!

Thanks for considering contributing to **FastOpenAPI** 🎉  
This guide explains how to get started, make contributions, write commits, open pull requests, and run tests.

---

## 📦 Setup & Running

Install dependencies with:

```bash
# Fork the repo on GitHub first, then:
git clone https://github.com/yourusername/fastopenapi.git
cd fastopenapi
poetry install
```

If you don't use `poetry`, you can install manually from `pyproject.toml`:

```bash
pip install -e .[dev]
```

---

## 🚧 Project Structure

- `fastopenapi/` — core library
- `examples/` — examples for different frameworks
- `tests/` — tests for each supported framework
- `benchmarks/` — performance comparisons
- `docs/` — documentation in multiple languages

---

## 🧪 Running Tests

To run tests:

```bash
pytest
```

Tests cover both internal logic and integration with aiohttp, flask, sanic, and more.

---

## 🧼 Code Style

This project uses:
- `black` — code formatting
- `flake8` — linting
- `isort` — import sorting
- `pre-commit` — hooks for clean code before commit

Install pre-commit hooks:

```bash
pre-commit install
```

Run all checks manually:

```bash
pre-commit run --all-files
```

---

## 🧾 Git & Pull Requests

1. Fork the repository
2. Create a new branch: `feature/your-feature` or `fix/your-fix`
3. Keep commits atomic and meaningful
4. Open a PR with a clear description:
   - What was added/changed?
   - Which frameworks were affected?
   - How was it tested?

---

## 📚 Documentation

If your change affects public APIs or behavior, update the relevant documentation:
- `docs/en/`
- If possible, update other languages too (optional)

---

## 📤 Feedback

Not sure how to implement a feature?  
Feel free to open an issue with your proposal. We’re happy to discuss it with you!

