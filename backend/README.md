# Backend

This folder contains the backend application code.

## Structure

- `app.py` - Main Flask application
- `health_system.db` - SQLite database
- `pkl/` - Machine learning models
- `uploads/` - Uploaded files (prescriptions, reports)
- `*.py` - Python scripts (training, testing)
- `*.md` - Documentation files

## Running the Application

From the backend directory:
```bash
python app.py
```

Or from the project root:
```bash
cd backend
python app.py
```

## Configuration

The Flask app is configured to use:
- Templates: `../frontend/templates/`
- Static files: `../frontend/static/`
- Database: `health_system.db` (in backend folder)
- Models: `pkl/` (in backend folder)
- Uploads: `uploads/` (in backend folder)

