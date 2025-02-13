import pytest
import sqlite3
import os
from flask import Flask
from routes import study_sessions

@pytest.fixture
def app():
    # Create a test Flask app
    app = Flask(__name__)
    
    # Use an in-memory SQLite database for testing
    app.db = sqlite3.connect(':memory:', check_same_thread=False)
    app.db.row_factory = sqlite3.Row
    
    # Create test tables
    cursor = app.db.cursor()
    cursor.executescript('''
        CREATE TABLE groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at DATETIME NOT NULL
        );

        CREATE TABLE study_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at DATETIME NOT NULL
        );

        CREATE TABLE words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kanji TEXT NOT NULL,
            romaji TEXT NOT NULL,
            english TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            correct_count INTEGER NOT NULL DEFAULT 0,
            wrong_count INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            study_activity_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME,
            completed INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (group_id) REFERENCES groups(id),
            FOREIGN KEY (study_activity_id) REFERENCES study_activities(id)
        );

        CREATE TABLE word_review_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            study_session_id INTEGER NOT NULL,
            word_id INTEGER NOT NULL,
            correct INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL,
            updated_at DATETIME,
            FOREIGN KEY (study_session_id) REFERENCES study_sessions(id),
            FOREIGN KEY (word_id) REFERENCES words(id)
        );
    ''')
    app.db.commit()
    cursor.close()

    # Load routes
    study_sessions.load(app)

    yield app

    # Cleanup
    app.db.close()

@pytest.fixture
def client(app):
    return app.test_client() 