---
description: Add a new feature to the expense tracker app
---

# Add Feature Workflow

This workflow helps you add a new feature to the Spendly expense tracker. It will scaffold the necessary route, template, and update documentation.

## Steps

1. **Understand the feature**
   - Read the feature description provided by the user
   - Identify if it's a new route, new database field, or new template
   - Check SPEC.md to ensure it aligns with the project scope

2. **Create/update the route in app.py**
   - Add the route function following existing patterns
   - Use `@login_required` decorator if authentication is needed
   - Add CSRF check for POST routes: `if not _check_csrf(): abort(400, "Invalid CSRF token.")`
   - Follow naming convention: verb-first (e.g., `list_expenses`, `add_expense`)
   - Add type hints to function signature
   - Keep handler functions under ~25 lines; extract helpers if needed

3. **Create/update database functions in database/db.py**
   - Add any new DB helper functions needed
   - Use parameterized SQL: `cur.execute("... WHERE id = ?", (id,))`
   - Follow naming: `get_<thing>`, `create_<thing>`, `update_<thing>`, `delete_<thing>`
   - Add type hints

4. **Create/update templates**
   - Create template in appropriate subdirectory (auth/, expenses/, categories/)
   - Use lowercase, hyphenated filenames (e.g., `add-expense.html`)
   - Extend `base.html`: `{% extends "base.html" %}`
   - Override `{% block content %}`
   - Include CSRF token in forms: `<input type="hidden" name="_csrf" value="{{ csrf_token() }}">`
   - Use `url_for()` for links and form actions

5. **Update CLAUDE.md**
   - If the feature adds new dependencies, update the Tech Stack section
   - If it changes the folder structure, update the Folder Structure section
   - Document any new conventions or patterns introduced

6. **Update SPEC.md (if scope changes)**
   - If the feature changes the project scope, update SPEC.md
   - Keep documentation in sync with code

7. **Test the feature**
   - Run the app: `python app.py`
   - Manually test the new route(s)
   - Add tests to tests/ if appropriate

8. **Commit the changes**
   - Use conventional commit format: `feat(scope): description`
   - Example: `feat(expenses): add bulk-delete route`
