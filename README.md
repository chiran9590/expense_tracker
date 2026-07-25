# Spendly - Expense Tracker

A simple expense tracking web application built with Flask.

## Features

- User authentication (login/register)
- Profile management
- Expense tracking (add, edit, delete)
- Responsive design

## Project Structure

```
expense-tracker/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── database/              # Database modules
│   ├── __init__.py
│   └── db.py
├── static/                # Static assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── templates/             # HTML templates
    ├── base.html
    ├── landing.html
    ├── login.html
    └── register.html
```

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Visit http://localhost:5001 in your browser

## Routes

- `GET /` - Landing page
- `GET /register` - User registration
- `GET /login` - User login
- `GET /logout` - User logout (placeholder)
- `GET /profile` - User profile (placeholder)
- `GET /expenses/add` - Add expense (placeholder)
- `GET /expenses/<int:id>/edit` - Edit expense (placeholder)
- `GET /expenses/<int:id>/delete` - Delete expense (placeholder)

## Development

This application uses:
- Flask 3.1.3
- Werkzeug 3.1.6
- pytest 8.3.5 (for testing)
- pytest-flask 1.3.0 (for Flask testing)

## Database

The application uses SQLite for data storage. The database file is automatically created when the application runs and is located in the `database/` directory (gitignored).
