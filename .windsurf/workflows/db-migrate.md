---
description: Add a new column to the database schema
---

# Database Migration Workflow

This workflow helps you add a new column to an existing table in the SQLite database. It will update the schema, routes, and templates accordingly.

## Steps

1. **Understand the migration**
   - Read the column description provided by the user
   - Identify which table needs the new column
   - Determine the data type and constraints (NOT NULL, DEFAULT, etc.)

2. **Backup the database**
   - Copy `database/expense_tracker.db` to `database/expense_tracker.db.backup`
   - This allows rollback if something goes wrong

3. **Update the schema in database/db.py**
   - Find the `init_db()` function
   - Add the new column to the appropriate CREATE TABLE statement
   - If the table already exists, add ALTER TABLE logic:
     ```python
     # Check if column exists, add if not
     cur.execute("PRAGMA table_info(expenses)")
     columns = [col[1] for col in cur.fetchall()]
     if 'new_column' not in columns:
         cur.execute("ALTER TABLE expenses ADD COLUMN new_column TEXT")
     ```
   - Update any related helper functions to include the new column

4. **Update app.py routes**
   - Update form parsing functions to include the new field
   - Update handler functions to pass the new field to DB functions
   - Update validation logic if needed
   - Update template rendering to pass the new field

5. **Update templates**
   - Add the new field to relevant forms (add/edit)
   - Add the new field to list/display templates
   - Use appropriate input types based on data type

6. **Run the migration**
   - Delete the old database file: `rm database/expense_tracker.db`
   - Run the app to trigger `init_db()`: `python app.py`
   - Verify the new column exists in the database

7. **Test the migration**
   - Test adding a record with the new field
   - Test editing a record with the new field
   - Test displaying the new field
   - Run existing tests to ensure nothing broke: `pytest`

8. **Update documentation**
   - Update SPEC.md §4 (Data Model) with the new column
   - Update CLAUDE.md if conventions changed

9. **Commit the changes**
   - Use conventional commit format: `feat(db): add column_name to table_name`
   - Example: `feat(db): add receipt_url column to expenses`
