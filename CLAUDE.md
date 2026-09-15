# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Spendly — a Flask expense tracker built as a step-by-step learning exercise. The codebase is intentionally scaffolded: templates and styling are in place, but most server-side logic is left as placeholder routes and stub files with comments describing what should be implemented at each "Step".

## Commands

```bash
# Activate the virtualenv (already created as my_env/)
source my_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the dev server (http://localhost:5001)
python app.py

# Run tests
pytest

# Run a single test
pytest path/to/test_file.py::test_name
```

There is no build/lint step configured.

## Architecture

- `app.py` — single-file Flask app defining all routes. Currently only `/`, `/register`, and `/login` render templates (GET only, no form handling yet). `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete` are placeholder stubs returning plain strings — each is tagged with the Step number it belongs to (Step 3, 4, 7, 8, 9).
- `database/db.py` — stub for Step 1. Intended to hold `get_db()` (SQLite connection with `row_factory` and foreign keys enabled), `init_db()` (creates tables via `CREATE TABLE IF NOT EXISTS`), and `seed_db()` (sample data for dev). Not yet implemented — the app has no persistence layer.
- `templates/` — Jinja2 templates all extend `base.html`, which defines the shared nav/footer and pulls in `static/css/style.css` and `static/js/main.js`. `login.html` and `register.html` POST to `/login` and `/register` respectively, but those endpoints don't yet handle POST or sessions.
- SQLite DB file is expected at the project root as `expense_tracker.db` (gitignored, created by `init_db()` once implemented).

## Notes

- When implementing a new "Step" (auth, expense CRUD, etc.), check the placeholder route/comment in `app.py` or `database/db.py` first — it describes the expected shape of that step.
- No auth/session mechanism exists yet; login/register currently only render forms without processing submissions.
