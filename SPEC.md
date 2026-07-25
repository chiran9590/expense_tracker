# SPEC — Spendly Personal Expense Tracker

> **Status:** Draft, awaiting approval.
> **Authoritative document.** If code disagrees with this spec, the spec wins
> (or the spec gets updated). Always read this file before changing features.

## 1. Scope

A small, multi-user Flask web app for tracking personal expenses. Each user
sees only their own data. Auth is required for everything except the landing
page, login, and register.

**In scope for v1:**

- Account creation and login (email + password)
- Add, edit, delete expenses
- Categories managed by the user (CRUD)
- Filter expenses by date range and/or category
- Monthly summary on a dashboard (totals + a Chart.js chart)
- Polished, responsive UI with hand-written CSS

**Out of scope for v1** (defer if asked):

- Multi-currency, currency conversion
- Recurring expenses / scheduled transactions
- Receipts / attachments
- Budgets, alerts, export (CSV/PDF)
- Email verification, password reset, OAuth
- Mobile app / PWA

## 2. Users & Roles

- Single role: **authenticated user**.
- A user owns their expenses and categories. No sharing, no admin role.
- Anonymous visitors can only see: landing page, login, register.

## 3. Core Features

### 3.1 Authentication

- **Register** (`/register`): email, display name, password, confirm password.
  Email is unique. Password ≥ 8 chars. Passwords stored as
  `werkzeug.security.generate_password_hash`.
- **Login** (`/login`): email + password. Sets a Flask session cookie.
- **Logout** (`/logout`, POST): clears the session.
- All other routes require login; unauthenticated users are redirected to
  `/login?next=<original-path>`.

### 3.2 Categories

Users manage their own categories. Each user starts with a small set of
defaults seeded on first login (Food, Travel, Bills, Shopping, Other).

- **List** (`/categories`): show user's categories with edit/delete actions.
- **Create** (`/categories/new`): name (required, ≤ 40 chars, unique per user).
- **Edit** (`/categories/<id>/edit`): rename.
- **Delete** (`/categories/<id>/delete`): blocked if any expense uses the
  category — show error with link to reassign. Cascade-delete is **off**.

### 3.3 Expenses

Data fields per expense (see §4 for the schema):

| Field   | Type   | Notes                                       |
|---------|--------|---------------------------------------------|
| amount  | REAL   | Required. > 0. Stored as ₹ value.           |
| category| FK     | Required. Must belong to the current user.  |
| date    | DATE   | Required. Defaults to today.                |
| note    | TEXT   | Optional. ≤ 200 chars.                      |

Routes:

- **List** (`/expenses`, GET): all user's expenses, newest first. Optional
  query params: `?from=YYYY-MM-DD&to=YYYY-MM-DD&category=<id>`. Filters
  compose with AND. Show a small filter form above the list.
- **Add** (`/expenses/new`, GET/POST): form with amount, category
  (dropdown), date, note. POST validates and inserts; on success, redirect
  to `/expenses` with a flash "Expense added."
- **Edit** (`/expenses/<id>/edit`, GET/POST): same form pre-filled. 404 if
  the expense isn't the current user's.
- **Delete** (`/expenses/<id>/delete`, POST): 404 if not owner. Redirect
  to `/expenses` with flash.

### 3.4 Dashboard

- **Route:** `/dashboard` (also the implicit landing page after login).
- **Sections:**
  1. **Month-to-date total** — sum of expenses in the current calendar month.
  2. **Previous month total** — for comparison.
  3. **Top categories this month** — top 5 categories by total, as a list.
  4. **Chart** — Chart.js doughnut chart of spending by category for the
     current month. If no expenses, render an empty-state card instead of
     an empty chart.
  5. **Recent expenses** — last 5 expenses, linking to their edit page.
- A date selector (`?month=YYYY-MM`) lets the user view any month; default
  is the current month.

### 3.5 UI / UX

- **Layout:** every page extends `templates/base.html`, which provides the
  nav and footer.
- **Nav (authenticated):** Dashboard · Expenses · Categories · user name ·
  Logout.
- **Nav (anonymous):** Sign in · Get started.
- **Forms:** server-side validation with flash messages on error. Preserve
  user input on validation failure.
- **Currency formatting:** `₹{:,.2f}` in templates. Dates as `YYYY-MM-DD` in
  inputs, human-friendly (`21 Jul 2026`) in display.
- **Accessibility:** semantic HTML, labels on every input, focus styles,
  reasonable color contrast.

## 4. Data Model

SQLite schema, created by `init_db()` in `database/db.py`. All tables include
`created_at` for auditing; `users.id`, `expenses.id`, `categories.id` are
INTEGER PRIMARY KEY AUTOINCREMENT.

```sql
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
    date        TEXT    NOT NULL,           -- ISO 'YYYY-MM-DD'
    note        TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_date
    ON expenses (user_id, date);
```

### Defaults

On first registration, seed these categories for the new user:

```
Food, Travel, Bills, Shopping, Other
```

## 5. User Flow

```
                ┌──────────────┐
   visitor ───► │  / (landing) │
                └──────┬───────┘
                       │ click "Get started"
                       ▼
                ┌──────────────┐         ┌──────────────┐
                │  /register   │ ──────► │  /login      │
                └──────┬───────┘  alt    └──────┬───────┘
                       └────────┬──────────────┘
                                ▼
                          ┌──────────┐
                          │ /dashboard │ ◄── default after login
                          └─────┬─────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
  ┌──────────┐           ┌────────────┐          ┌────────────┐
  │ /expenses│           │ /expenses/ │          │/categories │
  │  (list)  │           │   new      │          │  (manage)  │
  └────┬─────┘           └────────────┘          └────────────┘
       │ filter (date / category)
       ▼
  /expenses?from=...&to=...&category=...
       │ edit / delete (per row)
       ▼
  /expenses/<id>/edit  ·  POST /expenses/<id>/delete
```

Typical session: **register → dashboard → add an expense → see it on
dashboard → filter by category → edit → done.**

## 6. URL & Route Summary

| Method | Path                                | Purpose                          |
|--------|-------------------------------------|----------------------------------|
| GET    | `/`                                 | Landing page (public)            |
| GET    | `/register`                         | Registration form (public)       |
| POST   | `/register`                         | Create account                   |
| GET    | `/login`                            | Login form (public)              |
| POST   | `/login`                            | Authenticate                     |
| POST   | `/logout`                           | Clear session                    |
| GET    | `/dashboard`                        | Monthly summary (auth)           |
| GET    | `/expenses`                         | List + filter (auth)             |
| GET    | `/expenses/new`                     | Add form (auth)                  |
| POST   | `/expenses/new`                     | Create expense                   |
| GET    | `/expenses/<id>/edit`               | Edit form (auth)                 |
| POST   | `/expenses/<id>/edit`               | Update expense                   |
| POST   | `/expenses/<id>/delete`             | Delete expense                   |
| GET    | `/categories`                       | List categories (auth)           |
| GET    | `/categories/new`                   | New category form (auth)         |
| POST   | `/categories/new`                   | Create category                  |
| GET    | `/categories/<id>/edit`             | Edit category form (auth)        |
| POST   | `/categories/<id>/edit`             | Update category                  |
| POST   | `/categories/<id>/delete`           | Delete category (blocked if used)|

## 7. Non-Functional Notes

- **No external services.** Runs entirely on a developer laptop.
- **No background jobs.** Everything is request/response.
- **Errors:** 404 page for unknown routes; generic 500 page that doesn't leak
  tracebacks. Flash messages for form errors.
- **Security:** parameterized SQL, password hashing, CSRF protection on POST
  forms (Flask-WTF or hand-rolled — see open question below).
- **Performance:** trivially small datasets; no pagination needed for v1.

## 8. Open Questions for the User

These do **not** block approval — they can be decided when we get to the
relevant step. Flagging them so they don't surprise you:

1. **CSRF protection.** Flask-WTF adds a dependency; hand-rolled is fine for
   a learning project. Default: hand-rolled hidden token per session.
2. **Session lifetime.** "Remember me" checkbox? Default: no, session ends
   when the browser closes.
3. **Edit category from expense form?** "Create new category" inline link on
   the add-expense form? Default: separate page for now.

---

**Please review and either approve as-is, or tell me what to change.**
Once approved, I'll move on to the Flask skeleton (Step 4 in your original
brief).
