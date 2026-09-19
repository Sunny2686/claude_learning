# Spec: Registration

## Overview

Registration lets a new visitor create a Spendly account from the existing `/register` page. The form is already built and styled, but the route only renders it and ignores submissions. This feature adds POST handling: server-side validation (including a confirm-password check that asks the user to re-enter a mismatched password), a werkzeug-hashed password, a new row in the `users` table, and a redirect to the login page with a success message. It is the first write path into the `users` table and the entry point for login (Step 3) and every user-scoped feature after it.

## Dependencies

- Step 1 — Database setup (`get_db()`, `init_db()` and the `users` table in `database/db.py`) must be in place. It is already implemented and merged on `main`.
- No dependency on login/sessions. Registration does not log the user in.

## Navigation approach (Route or link)

- `GET /register` — existing route. Renders the empty form. Reached from the navbar "Get started" button, the landing page CTAs, and the "Create one free" link on the login page.
- `POST /register` — new behaviour on the existing route, so the route now accepts `methods=["GET", "POST"]`.
  - Validation fails: re-render `register.html` with HTTP 400, an `error` message and the submitted `name` and `email` kept (never either password field).
  - Registration succeeds: flash "Account created. Please sign in." and redirect (302) to `url_for('login')`.
- The existing "Sign in" link on the register page already goes to `url_for('login')`. No other new routes.

## Existing Files changes

- `app.py` — Change the `/register` route to accept GET and POST. On POST it reads the form (`name`, `email`, `password`, `confirm_password`), validates it, calls the db helpers and either re-renders with an error or flashes and redirects. It also sets `app.secret_key`, read from the `SECRET_KEY` env var with a dev-only fallback, because `flash()` needs it. It must contain no SQL, per CLAUDE.md.
- `database/db.py` — Add `create_user(name, email, password_hash)` and `get_user_by_email(email)`. Both use parameterised queries and close their connections. `create_user` returns the new user id, and `get_user_by_email` returns a `sqlite3.Row` or `None`. This keeps all DB logic out of the route.
- `templates/register.html` — Replace the hardcoded `action="/register"` with `action="{{ url_for('register') }}"` (CLAUDE.md: never hardcode URLs). Add a "Confirm password" field (`id` and `name` of `confirm_password`, type `password`, required) directly below the password field. Repopulate the `name` and `email` inputs from the values passed back on a failed submit; both password fields are always left empty.
- `templates/login.html` — Render flashed messages above the form, so the success message appears after redirect. Use a new `.auth-success` block that mirrors the existing `.auth-error` block. Leave the rest of the file, including its form action, alone; that belongs to the login step.
- `static/css/style.css` — Add `--success` and `--success-light` variables to `:root` and an `.auth-success` rule that uses only CSS variables, never hardcoded hex.

## New Files

- `tests/test_registration.py` — pytest and pytest-flask tests for the register route, using a temporary database so the real `expense_tracker.db` is not touched. They cover a successful registration, a duplicate email, a short password, a mismatched or empty confirm password, missing fields and an invalid email. `pytest` and `pytest-flask` are already in `requirements.txt`.
- `tests/conftest.py` — provides the `app` fixture, which points `database.db.DB_PATH` at a temporary file and calls `init_db()`. pytest-flask builds the `client` fixture from it. It is required, not optional.
- `pytest.ini` — sets `pythonpath = .` and `testpaths = tests` so `import app` resolves from the project root. `tests/` has no `__init__.py`, so without this the tests cannot import the app.

## Any Packages dependencies

No packages dependencies. Use only Flask, werkzeug and the standard library (`sqlite3`, `re`, `os`). `requirements.txt` stays unchanged.

## Constraint Rules

- No SQLAlchemy or ORMs
- Parameterised queries only, with no string formatting in SQL
- Passwords hashed with werkzeug (`generate_password_hash`); plain-text passwords are never stored, logged or re-rendered
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No DB logic in route functions; it lives in `database/db.py`
- Use `url_for()` for every URL in templates and redirects
- Vanilla JS only, and none is required for this feature
- Keep the app on port 5001

### Validation rules (server-side, enforced in the route)

| Field    | Rule                                                             | Error message                                    |
| -------- | ---------------------------------------------------------------- | ------------------------------------------------ |
| name     | Trimmed, not empty, at most 100 characters                       | "Please enter your full name."                   |
| email    | Trimmed, lowercased, basic `local@domain.tld` shape              | "Please enter a valid email address."            |
| password | At least 8 characters (matches the form placeholder)             | "Password must be at least 8 characters."        |
| confirm  | `confirm_password` is identical to `password` (exact match, not trimmed) | "Passwords do not match. Please re-enter your password." |
| email    | Not already in `users` (pre-check and `sqlite3.IntegrityError`)  | "An account with this email already exists."     |

The route catches `sqlite3.IntegrityError` from `create_user` so a race between the pre-check and the insert still shows the duplicate-email message, not a 500.

## Defenation of done:

Verify each item by running the app (`python app.py`, http://localhost:5001):

- [ ] `GET /register` renders the form with no error and no console errors
- [ ] The form posts to `/register` via `url_for` and there are no hardcoded URLs in the changed templates
- [ ] Submitting valid details creates a row in `users` (check with `sqlite3 expense_tracker.db "SELECT id, name, email FROM users"`)
- [ ] The stored `password_hash` is a werkzeug hash (for example `scrypt:` or `pbkdf2:` prefix), not the plain password
- [ ] After a successful registration the browser lands on `/login` and shows "Account created. Please sign in."
- [ ] Refreshing `/login` after that no longer shows the success message
- [ ] Registering the same email again, including a different case such as `A@x.com` vs `a@x.com`, re-renders the form with "An account with this email already exists." and creates no second row
- [ ] A password shorter than 8 characters shows the length error and creates no row
- [ ] The form shows a "Confirm password" field below "Password"
- [ ] If the two password fields differ, the form re-renders with "Passwords do not match. Please re-enter your password.", creates no row, and both password fields are empty
- [ ] Leaving "Confirm password" empty (bypassing browser validation via dev tools) shows the same mismatch error
- [ ] An empty or whitespace-only name shows the name error and creates no row
- [ ] An invalid email such as `abc` or `a@b` (bypassing browser validation via dev tools) shows the email error
- [ ] After any failed submit the name and email fields keep their values and both password fields are empty
- [ ] The demo user (`demo@spendly.com`) is still present and unaffected
- [ ] The `.auth-success` block and any new CSS use only CSS variables, with no new hex values
- [ ] `pytest` passes, including the new registration tests
- [ ] No new pip packages were added and `requirements.txt` is unchanged
