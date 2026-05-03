"""
Entry point for the Election Navigator Flask app.
Run from the election-navigator/ directory:
    python run.py
"""
import sys
import os

# Ensure the election-navigator directory is on the path
sys.path.insert(0, os.path.dirname(__file__))

from backend.app import app

if __name__ == "__main__":
    app.run(debug=True)
