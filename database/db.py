"""Database module for Spendly.

Owns the SQLite schema, connection lifecycle, and every helper that touches
the database. Routes in app.py should never call ``sqlite3`` directly — go
through the helpers here so SQL stays in one place.
"""
from __future__ import annotations

import os
import sqlite3
from typing import Any, Iterable, Optional

# Database file lives next to this module so the path is stable regardless
# of the working directory the app is launched from.
# Can be overridden via SPENDLY_TEST_DB environment variable for testing.
DB_PATH = os.environ.get(
    "SPENDLY_TEST_DB",
    os.path.join(os.path.dirname(__file__), "expense_tracker.db")
)

# Categories seeded for every new user (SPEC §4 "Defaults").
DEFAULT_CATEGORIES: tuple[str, ...] = (
    "Food",
    "Travel",
    "Bills",
    "Shopping",
    "Other",
)


# ------------------------------------------------------------------ #
# Connection lifecycle                                                #
# ------------------------------------------------------------------ #

def get_db() -> sqlite3.Connection:
    """Return a SQLite connection scoped to the current app context.

    The connection is created lazily and stored on ``flask.g`` so the same
    connection is reused for the duration of a request. ``Row`` factory
    makes rows indexable by column name, and foreign-key enforcement is
    turned on (off by default in SQLite).
    """
    from flask import current_app, g

    if "db" not in g:
        conn = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_exc: Optional[BaseException] = None) -> None:
    """Close the request-scoped connection, if any."""
    from flask import g

    db: Optional[sqlite3.Connection] = g.pop("db", None)
    if db is not None:
        db.close()


# ------------------------------------------------------------------ #
# Schema                                                              #
# ------------------------------------------------------------------ #

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    display_name  TEXT    NOT NULL,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    name       TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, name),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    amount      REAL    NOT NULL CHECK (amount > 0),
    date        TEXT    NOT NULL,
    note        TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_date
    ON expenses (user_id, date);
"""


def init_db(db_path: Optional[str] = None) -> None:
    """Create all tables and indexes if they don't already exist.

    ``db_path`` defaults to the module-level ``DB_PATH`` so this can be
    called either from inside an app context (which uses ``DATABASE``) or
    from the factory before the first request.
    """
    path = db_path
    if path is None:
        try:
            from flask import current_app

            path = current_app.config["DATABASE"]
        except RuntimeError:
            path = DB_PATH
    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


# ------------------------------------------------------------------ #
# Users                                                               #
# ------------------------------------------------------------------ #

def create_user(email: str, display_name: str, password_hash: str) -> int:
    """Insert a new user and return the assigned id.

    Raises ``sqlite3.IntegrityError`` if the email is already taken.
    """
    db = get_db()
    cur = db.execute(
        "INSERT INTO users (email, display_name, password_hash) VALUES (?, ?, ?)",
        (email, display_name, password_hash),
    )
    db.commit()
    user_id = cur.lastrowid
    seed_default_categories(user_id)
    return user_id


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    return get_db().execute(
        "SELECT id, email, display_name, password_hash, created_at "
        "FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    return get_db().execute(
        "SELECT id, email, display_name, password_hash, created_at "
        "FROM users WHERE email = ?",
        (email,),
    ).fetchone()


# ------------------------------------------------------------------ #
# Categories                                                          #
# ------------------------------------------------------------------ #

def get_categories(user_id: int) -> list[sqlite3.Row]:
    return get_db().execute(
        "SELECT id, name FROM categories WHERE user_id = ? ORDER BY name",
        (user_id,),
    ).fetchall()


def get_category(user_id: int, category_id: int) -> Optional[sqlite3.Row]:
    return get_db().execute(
        "SELECT id, name FROM categories WHERE id = ? AND user_id = ?",
        (category_id, user_id),
    ).fetchone()


def create_category(user_id: int, name: str) -> int:
    """Insert a new category and return the assigned id.

    Raises ``sqlite3.IntegrityError`` on duplicate (user_id, name).
    """
    db = get_db()
    cur = db.execute(
        "INSERT INTO categories (user_id, name) VALUES (?, ?)",
        (user_id, name),
    )
    db.commit()
    return cur.lastrowid


def update_category(user_id: int, category_id: int, name: str) -> None:
    db = get_db()
    db.execute(
        "UPDATE categories SET name = ? WHERE id = ? AND user_id = ?",
        (name, category_id, user_id),
    )
    db.commit()


def delete_category(user_id: int, category_id: int) -> None:
    db = get_db()
    db.execute(
        "DELETE FROM categories WHERE id = ? AND user_id = ?",
        (category_id, user_id),
    )
    db.commit()


def category_in_use(category_id: int) -> bool:
    row = get_db().execute(
        "SELECT 1 FROM expenses WHERE category_id = ? LIMIT 1",
        (category_id,),
    ).fetchone()
    return row is not None


def seed_default_categories(user_id: int) -> None:
    """Populate the standard set of categories for a new user."""
    for name in DEFAULT_CATEGORIES:
        try:
            create_category(user_id, name)
        except sqlite3.IntegrityError:
            # Already exists — shouldn't happen for a new user, but stay
            # defensive in case seed is rerun.
            continue


# ------------------------------------------------------------------ #
# Expenses                                                            #
# ------------------------------------------------------------------ #

def create_expense(
    user_id: int,
    category_id: int,
    amount: float,
    date: str,
    note: Optional[str],
) -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO expenses (user_id, category_id, amount, date, note) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, category_id, amount, date, note),
    )
    db.commit()
    return cur.lastrowid


def get_expense(user_id: int, expense_id: int) -> Optional[sqlite3.Row]:
    return get_db().execute(
        "SELECT e.id, e.user_id, e.category_id, e.amount, e.date, e.note, "
        "       c.name AS category_name "
        "FROM expenses e "
        "JOIN categories c ON c.id = e.category_id "
        "WHERE e.id = ? AND e.user_id = ?",
        (expense_id, user_id),
    ).fetchone()


def update_expense(
    user_id: int,
    expense_id: int,
    category_id: int,
    amount: float,
    date: str,
    note: Optional[str],
) -> None:
    db = get_db()
    db.execute(
        "UPDATE expenses "
        "SET category_id = ?, amount = ?, date = ?, note = ? "
        "WHERE id = ? AND user_id = ?",
        (category_id, amount, date, note, expense_id, user_id),
    )
    db.commit()


def delete_expense(user_id: int, expense_id: int) -> None:
    db = get_db()
    db.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id),
    )
    db.commit()


def list_expenses(
    user_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    category_id: Optional[int] = None,
) -> list[sqlite3.Row]:
    """Return the user's expenses, newest first, with filters applied.

    All filters are AND'd. A None or empty value means "no filter for that
    column". The caller is responsible for any input validation; this
    function trusts that ``date_from``/``date_to`` are ISO strings and
    ``category_id`` is a valid integer referencing a row owned by the user.
    """
    sql = (
        "SELECT e.id, e.amount, e.date, e.note, "
        "       c.id AS category_id, c.name AS category_name "
        "FROM expenses e "
        "JOIN categories c ON c.id = e.category_id "
        "WHERE e.user_id = ? "
    )
    params: list[Any] = [user_id]
    if date_from:
        sql += "AND e.date >= ? "
        params.append(date_from)
    if date_to:
        sql += "AND e.date <= ? "
        params.append(date_to)
    if category_id:
        sql += "AND e.category_id = ? "
        params.append(category_id)
    sql += "ORDER BY e.date DESC, e.id DESC"
    return get_db().execute(sql, params).fetchall()


def sum_expenses(
    user_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    category_id: Optional[int] = None,
) -> float:
    """Sum amounts over the same filter set as ``list_expenses``."""
    sql = "SELECT COALESCE(SUM(e.amount), 0) AS total FROM expenses e WHERE e.user_id = ? "
    params: list[Any] = [user_id]
    if date_from:
        sql += "AND e.date >= ? "
        params.append(date_from)
    if date_to:
        sql += "AND e.date <= ? "
        params.append(date_to)
    if category_id:
        sql += "AND e.category_id = ? "
        params.append(category_id)
    row = get_db().execute(sql, params).fetchone()
    return float(row["total"])


def _month_bounds(year: int, month: int) -> tuple[str, str]:
    """Return (first_day, first_day_of_next_month) for a calendar month.

    The interval is half-open: ``[first, next_first)`` so callers can use
    ``date >= first AND date < next_first`` and never worry about the
    varying length of February or leap years.
    """
    if month == 12:
        return (f"{year:04d}-12-01", f"{year + 1:04d}-01-01")
    return (f"{year:04d}-{month:02d}-01", f"{year:04d}-{month + 1:02d}-01")


def sum_for_month(user_id: int, year: int, month: int) -> float:
    """Total spending in a single calendar month (1-indexed month)."""
    first, next_first = _month_bounds(year, month)
    db = get_db()
    row = db.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses "
        "WHERE user_id = ? AND date >= ? AND date < ?",
        (user_id, first, next_first),
    ).fetchone()
    return float(row["total"])


def by_category_for_month(
    user_id: int, year: int, month: int
) -> list[sqlite3.Row]:
    """Per-category totals for a month, ordered by amount descending.

    Categories with zero spending in the month are omitted (``HAVING
    total > 0``).
    """
    first, next_first = _month_bounds(year, month)
    return get_db().execute(
        "SELECT c.id AS category_id, c.name AS category_name, "
        "       COALESCE(SUM(e.amount), 0) AS total "
        "FROM categories c "
        "LEFT JOIN expenses e "
        "  ON e.category_id = c.id "
        " AND e.date >= ? AND e.date < ? "
        "WHERE c.user_id = ? "
        "GROUP BY c.id, c.name "
        "HAVING total > 0 "
        "ORDER BY total DESC",
        (first, next_first, user_id),
    ).fetchall()


def recent_expenses(user_id: int, limit: int = 5) -> list[sqlite3.Row]:
    return get_db().execute(
        "SELECT e.id, e.amount, e.date, e.note, "
        "       c.name AS category_name "
        "FROM expenses e "
        "JOIN categories c ON c.id = e.category_id "
        "WHERE e.user_id = ? "
        "ORDER BY e.date DESC, e.id DESC "
        "LIMIT ?",
        (user_id, limit),
    ).fetchall()
