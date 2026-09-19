# Spec: Login and Logout

## Overview

Login and logout give Spendly its first real notion of "who is using the app". Login turns the existing `/login` form into a working sign-in: it looks the user up by email, checks the password against the werkzeug hash saved at registration, and stores the user's id and name in Flask's signed session cookie. Logout clears that session. The navbar changes with session state, and the placeholder pages (`/profile` and the `/expenses/...` routes) send signed-out visitors to the login page. Every user-scoped feature after this (profile, add, edit and delete expense) depends on it.

## Dependencies

- Step 1 — Database setup (`get_db()`, `users` table).
- Step 2 — Registration (`create_user`, `get_user_by_email`, `app.secret_key`, the flash message on `/login`). This branch is created from `feature/registration`, which is not merged into `main` yet, so the registration PR must be merged before this one.

## Navigation approach (Route or link)

- `GET /login` — existing route. Renders the sign-in form. If the visitor is already signed in, redirect (302) to `url_for('profile')` instead.
- `POST /login` — new behaviour on the existing route, so it now accepts `methods=["GET", "POST"]`.
  - Failure (unknown email, wrong password, or missing fields): re-render `login.html` with HTTP 401, the generic message "Invalid email or password." and the submitted email kept (never the password). The same message is used whether the email or the password was wrong, so the form does not reveal which emails are registered.
  - Success: clear any old session, store `user_id` and `user_name`, then redirect (302) to `url_for('profile')`. Profile is still a placeholder until Step 4, so the user sees its placeholder text for now.
- `GET /logout` — existing stub, now implemented. Clears the session, flashes "You have been signed out." and redirects (302) to `url_for('login')`. It is safe to call when not signed in. It stays a GET link to match the scaffold (see Constraint Rules).
- `GET /register` — an already signed-in visitor is redirected to `url_for('profile')`.
- `GET /profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete` — when signed out, flash "Please sign in to continue." and redirect (302) to `url_for('login')`. When signed in they behave exactly as today (placeholder text).
- Navbar (in `base.html`): signed out shows "Sign in" and "Get started"; signed in shows the user's first name, a link to `url_for('profile')`, and a "Sign out" link to `url_for('logout')`.

End-to-end: landing → "Sign in" → `/login` → valid credentials → `/profile`. Navbar "Sign out" → `/logout` → `/login` with the sign-out message. Signed-out visit to `/profile` → `/login` with the sign-in prompt.

## Existing Files changes

- `app.py` — Import `session` and `check_password_hash`. Set `SESSION_COOKIE_SAMESITE = "Lax"`; the existing `secret_key` signs the cookie. Turn `/login` into a GET/POST route that validates the form, checks the hash and stores the session. Implement `/logout`. Add a small `login_required` decorator and apply it to `/profile` and the three `/expenses/...` stubs. The two auth pages redirect signed-in users. No SQL in the file.
- `database/db.py` — Extend `get_user_by_email` to also return `password_hash`, so login can verify the password. Still parameterised and still returns a `sqlite3.Row` or `None`. Registration only checks the result for `None`, so it is unaffected.
- `templates/login.html` — Replace the hardcoded `action="/login"` with `action="{{ url_for('login') }}"` (CLAUDE.md: never hardcode URLs) and repopulate the email input on a failed submit. The password input stays empty. The existing flash block already shows the registration and sign-out messages.
- `templates/base.html` — Make the navbar depend on `session.get('user_id')` as described above. The "Sign out" link uses the `nav-cta` class so it stays visible on mobile, where the stylesheet hides the other nav links. All links use `url_for()`.
- `static/css/style.css` — Add a small `.nav-user` rule for the signed-in name, using existing CSS variables only. Add a `.auth-info` style only if the "please sign in" flash needs a different look from the success message; otherwise reuse existing classes.
- `.claude/CLAUDE.md` — Update the stale Architecture and Notes text (it still says login/register only render forms, no sessions exist and `db.py` is empty) so the file matches the code after this step.

## New Files

- `tests/test_login_logout.py` — pytest and pytest-flask tests using the existing temporary-database fixtures in `tests/conftest.py`. They create a user with `create_user` and `generate_password_hash`, then cover a successful login, a wrong password, an unknown email, missing fields, logout, redirects for signed-out and signed-in visitors, and the navbar in both states.

## Any Packages dependencies

No packages dependencies. Use only Flask (`session`, `redirect`, `url_for`, `flash`), werkzeug (`check_password_hash`) and the standard library. `requirements.txt` stays unchanged.

## Constraint Rules

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug; verify only with `check_password_hash`, and never store, log or re-render a plain-text password
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No DB logic in route functions; it lives in `database/db.py`
- Use `url_for()` for every URL in templates and redirects
- Vanilla JS only, and none is required for this feature
- Keep the app on port 5001
- Store only `user_id` and `user_name` in the session, never the email or the hash. Call `session.clear()` before setting them on login, so a session id from before login is never reused.
- Normalise the email (trim and lowercase) before the lookup, matching registration.
- Do not add a `next` redirect parameter; it needs open-redirect handling and is out of scope.
- `/logout` stays a GET, as the scaffold has it. That is a known small trade-off, because a cross-site request could sign a user out, and nothing sensitive is exposed. Move it to POST in a later hardening step if wanted.
- `SECRET_KEY` must come from the environment in any real deployment; the dev fallback is only for local use.

## Defenation of done:

Verify each item by running the app (`python app.py`, http://localhost:5001), using an account created through `/register` or the seeded `demo@spendly.com` / `demo123`:

- [ ] `GET /login` renders the form, and the form posts to `/login` via `url_for` (no hardcoded URL)
- [ ] Signing in with valid credentials lands on `/profile` (the Step 4 placeholder text) and the navbar shows the user's first name and "Sign out"
- [ ] The email is matched case-insensitively (`DEMO@Spendly.com` works)
- [ ] A wrong password re-renders `/login` with "Invalid email or password." and keeps the email filled in
- [ ] An unregistered email shows exactly the same message as a wrong password
- [ ] The password field is empty after every failed attempt
- [ ] Empty fields (bypassing browser validation via dev tools) show the same error and do not raise a 500
- [ ] After registering, `/login` shows "Account created. Please sign in." and signing in works with the new account
- [ ] Clicking "Sign out" lands on `/login` with "You have been signed out." and the navbar shows "Sign in" and "Get started" again
- [ ] After signing out, pressing the browser Back button and refreshing `/profile` redirects to `/login`
- [ ] Visiting `/logout` while signed out redirects to `/login` without an error
- [ ] Signed out, visiting `/profile`, `/expenses/add`, `/expenses/1/edit` and `/expenses/1/delete` each redirects to `/login` with "Please sign in to continue."
- [ ] Signed in, visiting `/login` or `/register` redirects to `/profile`
- [ ] The session cookie is set, marked HttpOnly and SameSite=Lax, and does not contain the password or hash (check in browser dev tools)
- [ ] The navbar links, including "Sign out" on a narrow mobile-width window, are visible and work
- [ ] The new CSS uses only CSS variables, with no new hex values
- [ ] `pytest` passes, including the new login/logout tests and the existing registration tests
- [ ] No new pip packages were added and `requirements.txt` is unchanged
