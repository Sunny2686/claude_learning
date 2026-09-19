import pytest


@pytest.fixture
def app(tmp_path, monkeypatch):
    """App wired to a throwaway SQLite file so the real DB is never touched."""
    monkeypatch.setattr("database.db.DB_PATH", str(tmp_path / "test.db"))

    from app import app as flask_app
    from database.db import init_db

    flask_app.config.update(TESTING=True)
    init_db()
    return flask_app
