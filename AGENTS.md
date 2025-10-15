# Repository Guidelines

## Project Structure & Module Organization
- `app.py` — application entry point (Flask-style structure with `templates/` and `static/`).
- `templates/` — Jinja2 HTML templates; `static/` — CSS/JS/assets.
- `output/` — generated artifacts (logs, exports, temp files).
- `pic/` — image assets used by the app/docs.
- `config.example.json` — safe template; copy to `config.json` for local config. Never commit secrets.

## Build, Test, and Development Commands
- Create venv (PowerShell): `python -m venv .venv; .\.venv\Scripts\Activate`.
- Install deps: `pip install -r requirements.txt`.
- Run locally: `python app.py` (set env vars as needed before running).
- Lint/format (optional but recommended): `pip install black ruff`; then `black .` and `ruff .`.
- Tests (if `tests/` exists): `pip install pytest`; `pytest -q`.

## Coding Style & Naming Conventions
- Python: PEP 8; 4-space indents; UTF-8; max line length 100.
- Naming: `snake_case` for files/functions, `CapWords` for classes, `UPPER_SNAKE_CASE` for constants.
- Templates: keep blocks small, reuse with `{% extends %}`/`{% include %}`; assets under `static/css`, `static/js`, `static/img`.

## Testing Guidelines
- Framework: `pytest` with tests in `tests/` named `test_*.py`.
- Aim for ≥80% coverage on changed code; prefer pure functions; mock I/O and external services.
- Example: `pytest -q -k feature_x` to run focused tests.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`.
- Keep PRs focused; include clear description, linked issues, and steps to verify. Add screenshots for UI changes.
- Update `README.md` and `config.example.json` when behavior or config changes.

## Security & Configuration Tips
- Do not commit secrets in `config.json`. Use `config.example.json` as a template and environment variables to override (e.g., `APP_PORT`, `API_KEY`).
- Validate inputs; avoid writing sensitive data to `output/`.
- For agents: keep patches minimal and scoped; do not modify unrelated files or licensing.

