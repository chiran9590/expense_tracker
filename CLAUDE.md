# Spendly — Personal Expense Tracker

> **Persistent context for Claude.** This file is the single source of truth for
> project conventions. You should not need to re-explain the project in future
> sessions — point Claude at this file.

## 1. Project Purpose

A small personal-finance web app for tracking day-to-day spending. The user can
log in, add expenses, categorize them, edit or delete entries, filter by date or
category, and see a monthly summary on a dashboard.

This is a **learning project** for agentic coding practices. Prioritize clarity
and small, reviewable changes over abstraction. Prefer the simplest thing that
works.

## 2. Tech Stack

- **Language:** Python 3.10+
- **Framework:** Flask 3.x
- **Templating:** Jinja2 (via Flask)
- **Database:** SQLite (file-based, no external server)
- **DB access:** `sqlite3` stdlib module (no ORM)
- **Frontend:** Server-rendered HTML, hand-written CSS, vanilla JS
- **Charts:** Chart.js (loaded from CDN)
- **Testing:** pytest + pytest-flask
- **Auth:** Flask sessions + Werkzeug password hashing
- **Code quality:** black (formatter), flake8 (linter)
- **Agentic tools:** Skills (expense-report, test-runner), MCP server (currency rates)

> **No new dependencies without checking first.** Add to `requirements.txt`
> with a pinned version, and update this section.

## 3. Folder Structure & Conventions

```
expense-tracker/
├── app.py                  # Flask app factory / entrypoint. Routes live here.
├── requirements.txt        # Pinned Python deps
├── CLAUDE.md               # This file
├── SPEC.md                 # Feature spec — the source of truth for what we're building
├── README.md               # User-facing intro (already exists)
├── database/
│   ├── __init__.py
│   └── db.py               # get_db(), init_db(), close_db(), schema
├── static/
│   ├── css/style.css
│   └── js/main.js
├── templates/              # Jinja2 templates
│   ├── base.html           # Layout with nav and footer
│   ├── auth/               # login.html, register.html
│   ├── expenses/           # list, add, edit, dashboard
│   └── categories/         # category management
├── tests/                  # pytest tests
├── skills/                 # Agentic skills
│   ├── expense_report.py   # Generate monthly/yearly expense reports
│   └── test_runner.py      # Run test suite with pass/fail report
├── mcp/                    # MCP (Model Context Protocol) servers
│   └── currency_server.py  # Currency exchange rate API server
├── scripts/                # Utility scripts
│   └── lint.sh             # Run black and flake8 linting
└── .windsurf/
    └── workflows/          # Custom slash command workflows
        ├── add-feature.md  # Scaffold new features
        └── db-migrate.md   # Add database columns
```

### Conventions

- **Entry point:** `python app.py` — do not use `flask run`; port is **5001**.
- **DB file:** `database/expense_tracker.db` (gitignored, auto-created).
- **DB module:** All schema and connection helpers live in `database/db.py`.
- **Templates:** Use `base.html` as the layout; child templates `{% extends
  "base.html" %}` and override `{% block content %}`.
- **Static assets:** Reference via `url_for('static', filename='...')`.
- **No ORM.** Use parameterized SQL: `cur.execute("... WHERE id = ?", (id,))`.
- **Secrets:** `SECRET_KEY` is read from env; fall back to a dev value in
  `app.py` so the app boots without a `.env` during development.
- **Currency:** All amounts are in **Indian Rupees (₹)**. Format with
  `₹{:,.2f}` in templates. Store as `REAL` in SQLite.

## 4. Coding Style

- **PEP 8.** Use 4-space indentation, `snake_case` for functions and variables,
  `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- **Functions do one thing.** If a route handler grows past ~25 lines, extract
  a helper into `database/db.py` or a new module.
- **Naming:**
  - Route functions: verb-first (`list_expenses`, `add_expense`, `edit_expense`).
  - DB helpers: `get_<thing>`, `create_<thing>`, `update_<thing>`,
    `delete_<thing>`.
  - Templates: lowercase, hyphenated filenames (`add-expense.html`).
- **Imports:** stdlib → third-party → local, separated by blank lines.
- **Type hints** on new functions in `app.py` and `database/db.py`. Not
  required in templates or tiny scripts.
- **Comments:** Explain *why*, not *what*. Use docstrings for modules and
  non-trivial functions.
- **Error handling:** Return user-friendly flash messages on form errors;
  never leak a stack trace to the user.

### Commit Messages

Use **Conventional Commits**:

```
<type>(<scope>): <short summary>

<body explaining why, not what>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`.
Example: `feat(expenses): add edit-expense route and template`.

Keep the summary under 72 chars. Reference issue numbers when relevant.

## 5. How to Run Locally

```bash
# 1. Create / activate venv (already exists as ./venv)
source venv/bin/activate

# 2. Install deps
pip install -r requirements.txt

# 3. Run the app
python app.py
# -> http://localhost:5001
```

The SQLite DB is created automatically on first run (see
`database/init_db()`).

### Run tests

```bash
pytest
```

Or use the test-runner skill for a formatted report:

```bash
python skills/test_runner.py
python skills/test_runner.py --verbose
```

### Code quality checks

```bash
# Run linting manually
./scripts/lint.sh

# Or run tools individually
black app.py database/ tests/ skills/ mcp/ --check
flake8 app.py database/ tests/ skills/ mcp/ --max-line-length=88
```

### Generate expense reports

```bash
# Monthly report
python skills/expense_report.py --user-id 1 --month 2026-07

# Yearly report
python skills/expense_report.py --user-id 1 --year 2026

# Save to file
python skills/expense_report.py --user-id 1 --month 2026-07 --output report.md
```

## 6. Workflow Reminders for Claude

- **Read SPEC.md before changing features.** It is the source of truth.
- **Make small, reviewable changes.** One feature per commit when possible.
- **After writing code, run it.** If a Flask route changes, exercise it
  end-to-end (use the `run` skill or manually).
- **Update SPEC.md** if scope changes — keep docs in sync with code.
- **Do not commit secrets, the venv, or the SQLite DB.** `.gitignore` already
  covers them.

## 7. Agentic Tools & Workflows

### Slash Commands

The project includes custom slash command workflows in `.windsurf/workflows/`:

- **/add-feature**: Scaffolds a new feature by creating the route, template, and updating documentation. Use this when adding new functionality.
- **/db-migrate**: Adds a new column to the database schema, updating the schema, routes, and templates. Use this when modifying the data model.

### Skills

Standalone Python scripts in `skills/` for specialized tasks:

- **expense_report.py**: Generates monthly or yearly expense reports in Markdown format from the database. Useful for exporting spending summaries.
- **test_runner.py**: Runs the pytest suite and provides a formatted pass/fail report. Use this after making changes to validate all routes.

### MCP Integration

- **currency_server.py**: A minimal MCP (Model Context Protocol) server that provides currency exchange rate conversion. Uses the free exchangerate-api.com API. Can be used to convert expenses between currencies if multi-currency support is added.

### Code Quality

- **black**: Code formatter (line length 88 chars)
- **flake8**: Linter (max line length 88, ignores E203 and W503 for black compatibility)
- **scripts/lint.sh**: Runs both tools together. Run this before committing Python changes.
