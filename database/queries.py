from datetime import datetime

from database.db import get_db


def get_user_by_id(user_id):
    """Return a user's profile info as a plain dict, or None if not found.

    Dict has keys `name`, `email`, `member_since` (formatted "Month YYYY",
    derived from `users.created_at`).
    """
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    created = datetime.strptime(row["created_at"][:10], "%Y-%m-%d")
    return {
        "name": row["name"],
        "email": row["email"],
        "member_since": created.strftime("%B %Y"),
    }


def get_summary_stats(user_id):
    """Return total spent, transaction count, and top category for a user.

    Returns a dict:
        {"total_spent": float|int, "transaction_count": int, "top_category": str}

    - total_spent: sum of expenses.amount for the user, rounded to 2 decimal
      places; 0 (plain int) if the user has no expenses.
    - transaction_count: count of expenses rows for the user.
    - top_category: the category with the highest summed amount (ties broken
      alphabetically); the em-dash "—" if the user has no expenses.
    """
    conn = get_db()
    try:
        total_row = conn.execute(
            "SELECT SUM(amount) AS total FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        total_value = total_row["total"]
        total_spent = 0 if total_value is None else round(total_value, 2)

        count_row = conn.execute(
            "SELECT COUNT(*) AS count FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        transaction_count = count_row["count"]

        top_row = conn.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY total DESC, category ASC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        top_category = "—" if top_row is None else top_row["category"]

        return {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_category,
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10):
    """Return the user's most recent expenses as plain dicts.

    Each dict has exactly the keys `date`, `description`, `category`,
    `amount`. Results are ordered newest-first (`date DESC`, with `id DESC`
    as a tiebreak so same-date rows come back in insertion order) and
    capped at `limit` rows. Returns `[]` if the user has no expenses.
    """
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT date, description, category, amount
            FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_category_breakdown(user_id):
    """Return per-category spending totals and integer percentages for a user.

    Each item is a dict with keys `name` (category), `amount` (float sum of
    that category's expenses), and `pct` (int percentage of the user's total
    spend, rounded so all pct values sum to exactly 100). Ordered by amount
    descending, with category name ascending as a tiebreak. Returns an empty
    list if the user has no expenses.
    """
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT category, SUM(amount) AS amount
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY amount DESC, category ASC
            """,
            (user_id,),
        ).fetchall()

        if not rows:
            return []

        total = sum(row["amount"] for row in rows)
        raw_pcts = [(row["amount"] / total) * 100 for row in rows]
        floor_pcts = [int(p) for p in raw_pcts]
        remainder = 100 - sum(floor_pcts)
        floor_pcts[0] += remainder

        return [
            {"name": row["category"], "amount": row["amount"], "pct": pct}
            for row, pct in zip(rows, floor_pcts)
        ]
    finally:
        conn.close()
