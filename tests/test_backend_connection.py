from werkzeug.security import generate_password_hash

import database.db as db
from database.db import create_user
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)

EMAIL = "asha@example.com"
PASSWORD = "longenough1"
NAME = "Asha Rao"

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"


def make_user(email=EMAIL, password=PASSWORD, name=NAME):
    return create_user(name, email, generate_password_hash(password))


def sign_in(client, email=DEMO_EMAIL, password=DEMO_PASSWORD):
    return client.post("/login", data={"email": email, "password": password})


# ------------------------------------------------------------------ #
# get_user_by_id                                                      #
# ------------------------------------------------------------------ #

def test_get_user_by_id_returns_correct_fields(app):
    user_id = make_user()

    user = get_user_by_id(user_id)

    assert user["name"] == NAME
    assert user["email"] == EMAIL
    assert isinstance(user["member_since"], str) and user["member_since"]


def test_get_user_by_id_returns_none_for_missing_user(app):
    assert get_user_by_id(999999) is None


# ------------------------------------------------------------------ #
# get_summary_stats                                                   #
# ------------------------------------------------------------------ #

def test_summary_stats_for_seeded_demo_user(app):
    db.seed_db()
    demo_user = db.get_user_by_email(DEMO_EMAIL)

    stats = get_summary_stats(demo_user["id"])

    assert stats == {
        "total_spent": 5300.0,
        "transaction_count": 8,
        "top_category": "Shopping",
    }


def test_summary_stats_for_user_with_no_expenses(app):
    user_id = make_user()

    stats = get_summary_stats(user_id)

    assert stats == {
        "total_spent": 0,
        "transaction_count": 0,
        "top_category": "—",
    }


# ------------------------------------------------------------------ #
# get_recent_transactions                                             #
# ------------------------------------------------------------------ #

def test_seeded_user_transactions_are_newest_first(app):
    db.seed_db()
    demo_user = db.get_user_by_email(DEMO_EMAIL)

    transactions = get_recent_transactions(demo_user["id"])

    assert len(transactions) == 8
    dates = [txn["date"] for txn in transactions]
    assert dates == sorted(dates, reverse=True)
    for txn in transactions:
        assert set(txn.keys()) == {"date", "description", "category", "amount"}


def test_user_with_no_expenses_has_empty_transaction_list(app):
    user_id = make_user()

    assert get_recent_transactions(user_id) == []


# ------------------------------------------------------------------ #
# get_category_breakdown                                              #
# ------------------------------------------------------------------ #

def test_seeded_demo_user_breakdown_is_ordered_and_sums_to_100(app):
    db.seed_db()
    demo_user = db.get_user_by_email(DEMO_EMAIL)

    result = get_category_breakdown(demo_user["id"])

    assert len(result) == 7
    assert result[0]["name"] == "Shopping"
    assert result[0]["amount"] == 1800.0

    amounts = [row["amount"] for row in result]
    assert amounts == sorted(amounts, reverse=True)

    for row in result:
        assert isinstance(row["pct"], int)

    assert sum(row["pct"] for row in result) == 100


def test_new_user_with_no_expenses_has_empty_breakdown(app):
    user_id = make_user()

    assert get_category_breakdown(user_id) == []


# ------------------------------------------------------------------ #
# GET /profile route                                                  #
# ------------------------------------------------------------------ #

def test_profile_redirects_when_signed_out(client):
    response = client.get("/profile")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_profile_shows_seed_user_data(client):
    db.seed_db()

    response = sign_in(client)
    assert response.status_code == 302

    page = client.get("/profile")

    assert page.status_code == 200
    assert b"Demo User" in page.data
    assert "demo@spendly.com".encode() in page.data
    assert "₹".encode() in page.data
    assert "₹5300.00".encode() in page.data
    assert b"Shopping" in page.data

    # Transactions appear newest-first.
    demo_user = db.get_user_by_email(DEMO_EMAIL)
    transactions = get_recent_transactions(demo_user["id"])
    body = page.data.decode()
    positions = [body.find(txn["description"]) for txn in transactions]
    assert all(p != -1 for p in positions)
    assert positions == sorted(positions)

    # All 7 categories appear in the breakdown.
    categories = get_category_breakdown(demo_user["id"])
    assert len(categories) == 7
    for cat in categories:
        assert cat["name"].encode() in page.data


def test_profile_for_brand_new_user_shows_zero_state(client):
    make_user(email="fresh@example.com", password="freshpass1", name="Fresh User")

    response = client.post(
        "/login", data={"email": "fresh@example.com", "password": "freshpass1"}
    )
    assert response.status_code == 302

    page = client.get("/profile")

    assert page.status_code == 200
    assert "₹0.00".encode() in page.data
    assert b'<span class="stat-value">0</span>' in page.data
    assert b"No transactions yet." in page.data
    assert b"No spending yet." in page.data
