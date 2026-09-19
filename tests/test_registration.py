import pytest
from werkzeug.security import check_password_hash

from database.db import get_db

VALID = {
    "name": "Asha Rao",
    "email": "asha@example.com",
    "password": "longenough1",
    "confirm_password": "longenough1",
}


def user_rows():
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM users").fetchall()
    finally:
        conn.close()


def test_get_register_renders_form(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b'name="email"' in response.data


def test_valid_signup_creates_hashed_user_and_redirects(client):
    response = client.post("/register", data=VALID)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    rows = user_rows()
    assert len(rows) == 1
    assert rows[0]["email"] == "asha@example.com"
    assert rows[0]["password_hash"] != VALID["password"]
    assert check_password_hash(rows[0]["password_hash"], VALID["password"])


def test_success_message_shown_once_on_login(client):
    response = client.post("/register", data=VALID, follow_redirects=True)
    assert b"Account created. Please sign in." in response.data

    again = client.get("/login")
    assert b"Account created. Please sign in." not in again.data


def test_duplicate_email_rejected_case_insensitively(client):
    client.post("/register", data=VALID)
    response = client.post("/register", data={**VALID, "email": "ASHA@Example.com"})

    assert response.status_code == 400
    assert b"An account with this email already exists." in response.data
    assert len(user_rows()) == 1


def test_short_password_rejected(client):
    response = client.post(
        "/register", data={**VALID, "password": "1234567", "confirm_password": "1234567"}
    )

    assert response.status_code == 400
    assert b"Password must be at least 8 characters." in response.data
    assert user_rows() == []


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_name_rejected(client, name):
    response = client.post("/register", data={**VALID, "name": name})

    assert response.status_code == 400
    assert b"Please enter your full name." in response.data
    assert user_rows() == []


@pytest.mark.parametrize("email", ["abc", "a@b"])
def test_invalid_email_rejected(client, email):
    response = client.post("/register", data={**VALID, "email": email})

    assert response.status_code == 400
    assert b"Please enter a valid email address." in response.data
    assert user_rows() == []


def test_failed_post_keeps_name_and_email_but_not_password(client):
    response = client.post(
        "/register", data={**VALID, "password": "qx9zk1!", "confirm_password": "qx9zk1!"}
    )

    assert response.status_code == 400
    assert b'value="Asha Rao"' in response.data
    assert b'value="asha@example.com"' in response.data
    assert b"qx9zk1!" not in response.data


@pytest.mark.parametrize("confirm", ["different123", ""])
def test_mismatched_confirm_password_rejected(client, confirm):
    response = client.post("/register", data={**VALID, "confirm_password": confirm})

    assert response.status_code == 400
    assert b"Passwords do not match. Please re-enter your password." in response.data
    assert user_rows() == []


def test_mismatch_keeps_name_and_email_and_clears_both_passwords(client):
    response = client.post(
        "/register", data={**VALID, "password": "firstpass99", "confirm_password": "secondpass99"}
    )

    assert response.status_code == 400
    assert b'value="Asha Rao"' in response.data
    assert b'value="asha@example.com"' in response.data
    assert b"firstpass99" not in response.data
    assert b"secondpass99" not in response.data


def test_get_register_has_confirm_password_field(client):
    response = client.get("/register")
    assert b'name="confirm_password"' in response.data
