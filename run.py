#!/usr/bin/env python
"""
Run script for the application
Run from project root: python run.py
"""
import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
sys.path.insert(0, os.path.dirname(__file__))

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use environment variables directly

# Change to backend directory
os.chdir(backend_path)

# Import and run app
from app import app, init_db

# Try to use config for host/port, otherwise use defaults
try:
    from config import get_config
    config = get_config()
    host = config.HOST
    port = config.PORT
    debug = config.DEBUG
except (ImportError, AttributeError):
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'

if __name__ == '__main__':
    init_db()
    print("\n" + "="*60)
    print("Starting Swasthya Sampark Application")
    print("="*60)
    print(f"Backend: {backend_path}")
    print(f"Frontend Templates: {app.template_folder}")
    print(f"Frontend Static: {app.static_folder}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("="*60 + "\n")
    app.run(debug=debug, host=host, port=port)

