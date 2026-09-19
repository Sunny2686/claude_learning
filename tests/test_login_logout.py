import pytest
from werkzeug.security import generate_password_hash

from database.db import create_user

EMAIL = "asha@example.com"
PASSWORD = "longenough1"
NAME = "Asha Rao"

PROTECTED = [
    ("/profile", b"Profile page"),
    ("/expenses/add", b"Add expense"),
    ("/expenses/1/edit", b"Edit expense"),
    ("/expenses/1/delete", b"Delete expense"),
]


def make_user(email=EMAIL, password=PASSWORD, name=NAME):
    return create_user(name, email, generate_password_hash(password))


def sign_in(client, email=EMAIL, password=PASSWORD, **kwargs):
    return client.post("/login", data={"email": email, "password": password}, **kwargs)


def session_data(client):
    with client.session_transaction() as sess:
        return dict(sess)


def test_get_login_renders_form(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b'action="/login"' in response.data
    assert b'name="email"' in response.data
    assert b'name="password"' in response.data


def test_valid_login_sets_session_and_redirects_to_profile(client):
    user_id = make_user()

    response = sign_in(client)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")
    data = session_data(client)
    assert data == {"user_id": user_id, "user_name": NAME}


def test_login_email_is_case_insensitive(client):
    make_user()

    response = sign_in(client, email="  ASHA@Example.COM ")

    assert response.status_code == 302
    assert "user_id" in session_data(client)


def test_wrong_password_rejected_and_email_kept(client):
    make_user()

    response = sign_in(client, password="not-the-password")

    assert response.status_code == 401
    assert b"Invalid email or password." in response.data
    assert b'value="asha@example.com"' in response.data
    assert b"not-the-password" not in response.data
    assert session_data(client) == {}


def test_unknown_email_gets_same_message_as_wrong_password(client):
    make_user()

    wrong_password = sign_in(client, password="not-the-password")
    unknown_email = sign_in(client, email="nobody@example.com")

    assert unknown_email.status_code == 401
    assert b"Invalid email or password." in unknown_email.data
    assert session_data(client) == {}
    # Same status and message, so the form does not reveal which emails exist.
    assert unknown_email.status_code == wrong_password.status_code


@pytest.mark.parametrize(
    "email, password",
    [("", PASSWORD), (EMAIL, ""), ("", "")],
)
def test_missing_fields_rejected_without_error(client, email, password):
    make_user()

    response = sign_in(client, email=email, password=password)

    assert response.status_code == 401
    assert b"Invalid email or password." in response.data
    assert session_data(client) == {}


def test_login_cookie_is_httponly_and_samesite_lax(client):
    make_user()

    response = sign_in(client)

    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_login_discards_previous_session_data(client):
    make_user()
    with client.session_transaction() as sess:
        sess["leftover"] = "from-before-login"

    sign_in(client)

    assert "leftover" not in session_data(client)


def test_register_then_login_flow(client):
    registered = client.post(
        "/register",
        data={
            "name": NAME,
            "email": EMAIL,
            "password": PASSWORD,
            "confirm_password": PASSWORD,
        },
        follow_redirects=True,
    )
    assert b"Account created. Please sign in." in registered.data

    response = sign_in(client)
    assert response.status_code == 302
    assert "user_id" in session_data(client)


def test_logout_clears_session_and_shows_message(client):
    make_user()
    sign_in(client)

    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    assert session_data(client) == {"_flashes": [("info", "You have been signed out.")]}

    page = client.get("/login")
    assert b"You have been signed out." in page.data


def test_logout_when_signed_out_redirects_without_error(client):
    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


@pytest.mark.parametrize("path, placeholder", PROTECTED)
def test_protected_routes_redirect_when_signed_out(client, path, placeholder):
    response = client.get(path)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    page = client.get("/login")
    assert b"Please sign in to continue." in page.data


@pytest.mark.parametrize("path, placeholder", PROTECTED)
def test_protected_routes_allow_signed_in_user(client, path, placeholder):
    make_user()
    sign_in(client)

    response = client.get(path)

    assert response.status_code == 200
    assert placeholder in response.data


@pytest.mark.parametrize("path", ["/login", "/register"])
def test_auth_pages_redirect_when_signed_in(client, path):
    make_user()
    sign_in(client)

    response = client.get(path)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")


def test_navbar_when_signed_out(client):
    response = client.get("/")

    assert b"Sign in" in response.data
    assert b"Get started" in response.data
    assert b"Sign out" not in response.data


def test_navbar_when_signed_in(client):
    make_user()
    sign_in(client)

    response = client.get("/")

    assert b"Sign out" in response.data
    assert b'<span class="nav-user">Asha</span>' in response.data
    assert b"Get started" not in response.data
