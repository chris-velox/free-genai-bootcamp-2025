import pytest
from datetime import datetime
import logging

@pytest.fixture(autouse=True)
def setup_logging():
    logging.basicConfig(level=logging.INFO)

def test_create_study_session_success(client, app):
    logging.info("Starting test_create_study_session_success")
    # Insert test data
    cursor = app.db.cursor()
    
    # Create test group
    cursor.execute('''
        INSERT INTO groups (name, created_at) 
        VALUES ('Test Group', datetime('now'))
    ''')
    group_id = cursor.lastrowid

    # Create test activity
    cursor.execute('''
        INSERT INTO study_activities (name, created_at) 
        VALUES ('Test Activity', datetime('now'))
    ''')
    activity_id = cursor.lastrowid

    # Create test words
    word_ids = []
    for i in range(3):
        cursor.execute('''
            INSERT INTO words (kanji, romaji, english, created_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (f'漢字{i}', f'kanji{i}', f'english{i}'))
        word_ids.append(cursor.lastrowid)
    
    app.db.commit()
    cursor.close()

    # Test creating a study session
    response = client.post('/api/study-sessions', json={
        'group_id': group_id,
        'study_activity_id': activity_id,
        'word_ids': word_ids
    })

    assert response.status_code == 201
    data = response.get_json()
    
    # Verify response structure
    assert 'id' in data
    assert data['group_id'] == group_id
    assert data['group_name'] == 'Test Group'
    assert data['activity_id'] == activity_id
    assert data['activity_name'] == 'Test Activity'
    assert data['review_items_count'] == len(word_ids)
    assert 'start_time' in data
    assert 'end_time' in data

def test_create_study_session_validation_errors(client):
    logging.info("Starting test_create_study_session_validation_errors")
    # Test missing required fields
    response = client.post('/api/study-sessions', json={})
    assert response.status_code == 400
    assert 'Missing required field' in response.get_json()['error']

    # Test invalid data types
    response = client.post('/api/study-sessions', json={
        'group_id': 'not an integer',
        'study_activity_id': 1,
        'word_ids': [1, 2, 3]
    })
    assert response.status_code == 400
    assert 'group_id must be an integer' in response.get_json()['error']

    # Test empty word_ids
    response = client.post('/api/study-sessions', json={
        'group_id': 1,
        'study_activity_id': 1,
        'word_ids': []
    })
    assert response.status_code == 400
    assert 'word_ids cannot be empty' in response.get_json()['error']

def test_create_study_session_invalid_references(client, app):
    logging.info("Starting test_create_study_session_invalid_references")
    # Test invalid group_id and study_activity_id
    response = client.post('/api/study-sessions', json={
        'group_id': 99999,
        'study_activity_id': 99999,
        'word_ids': [1]
    })
    assert response.status_code == 400
    assert 'Invalid group_id or study_activity_id' in response.get_json()['error']

    # Create valid group and activity
    cursor = app.db.cursor()
    cursor.execute('''
        INSERT INTO groups (name, created_at) 
        VALUES ('Test Group', datetime('now'))
    ''')
    group_id = cursor.lastrowid

    cursor.execute('''
        INSERT INTO study_activities (name, created_at) 
        VALUES ('Test Activity', datetime('now'))
    ''')
    activity_id = cursor.lastrowid
    
    app.db.commit()
    cursor.close()

    response = client.post('/api/study-sessions', json={
        'group_id': group_id,
        'study_activity_id': activity_id,
        'word_ids': [99999]
    })
    assert response.status_code == 400
    assert 'One or more word_ids are invalid' in response.get_json()['error']

def test_submit_study_session_review_success(client, app):
    cursor = app.db.cursor()
    try:
        # Create test group
        cursor.execute('''
            INSERT INTO groups (name, created_at) 
            VALUES ('Test Group', datetime('now'))
        ''')
        group_id = cursor.lastrowid

        # Create test activity
        cursor.execute('''
            INSERT INTO study_activities (name, created_at) 
            VALUES ('Test Activity', datetime('now'))
        ''')
        activity_id = cursor.lastrowid

        # Create test words
        cursor.execute('''
            INSERT INTO words (kanji, romaji, english, created_at) 
            VALUES 
                ('犬', 'inu', 'dog', datetime('now')),
                ('猫', 'neko', 'cat', datetime('now'))
        ''')
        word1_id = cursor.lastrowid
        word2_id = cursor.lastrowid - 1

        # Create study session
        cursor.execute('''
            INSERT INTO study_sessions (
                group_id, 
                study_activity_id, 
                created_at,
                completed
            ) VALUES (?, ?, datetime('now'), 0)
        ''', (group_id, activity_id))
        session_id = cursor.lastrowid

        # Add word review items
        for word_id in [word1_id, word2_id]:
            cursor.execute('''
                INSERT INTO word_review_items (study_session_id, word_id, correct, created_at)
                VALUES (?, ?, 0, datetime('now'))
            ''', (session_id, word_id))

        app.db.commit()

        # Test the review submission
        response = client.post(f'/api/study-sessions/{session_id}/review', json={
            'reviews': [
                {'word_id': word1_id, 'is_correct': True},
                {'word_id': word2_id, 'is_correct': False}
            ]
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Review submitted successfully'
        assert data['stats']['total_reviews'] == 2
        assert data['stats']['correct_count'] == 1
        assert data['stats']['wrong_count'] == 1

        # Verify database updates
        cursor.execute('SELECT correct FROM word_review_items WHERE word_id = ?', (word1_id,))
        assert cursor.fetchone()['correct'] == 1

        cursor.execute('SELECT correct FROM word_review_items WHERE word_id = ?', (word2_id,))
        assert cursor.fetchone()['correct'] == 0

        cursor.execute('SELECT correct_count, wrong_count FROM words WHERE id = ?', (word1_id,))
        word1_stats = cursor.fetchone()
        assert word1_stats['correct_count'] == 1
        assert word1_stats['wrong_count'] == 0

        cursor.execute('SELECT correct_count, wrong_count FROM words WHERE id = ?', (word2_id,))
        word2_stats = cursor.fetchone()
        assert word2_stats['correct_count'] == 0
        assert word2_stats['wrong_count'] == 1

    finally:
        cursor.close()

def test_submit_study_session_review_validation(client, app):
    """Test various validation cases for the review submission endpoint"""
    cursor = app.db.cursor()
    try:
        # Create minimal test data
        cursor.execute('''
            INSERT INTO groups (name, created_at) 
            VALUES ('Test Group', datetime('now'))
        ''')
        group_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO study_activities (name, created_at) 
            VALUES ('Test Activity', datetime('now'))
        ''')
        activity_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO study_sessions (
                group_id, 
                study_activity_id, 
                created_at,
                completed
            ) VALUES (?, ?, datetime('now'), 0)
        ''', (group_id, activity_id))
        session_id = cursor.lastrowid

        app.db.commit()

        # Test missing JSON
        response = client.post(f'/api/study-sessions/{session_id}/review')
        assert response.status_code == 400
        assert 'Request must be JSON' in response.get_json()['error']

        # Test missing reviews array
        response = client.post(f'/api/study-sessions/{session_id}/review', json={})
        assert response.status_code == 400
        assert 'Missing reviews array' in response.get_json()['error']

        # Test invalid reviews format
        response = client.post(f'/api/study-sessions/{session_id}/review', json={
            'reviews': 'not an array'
        })
        assert response.status_code == 400
        assert 'Reviews must be an array' in response.get_json()['error']

        # Test invalid review object
        response = client.post(f'/api/study-sessions/{session_id}/review', json={
            'reviews': [{'word_id': 'not a number', 'is_correct': 'not a boolean'}]
        })
        assert response.status_code == 400
        assert 'word_id must be an integer' in response.get_json()['error']

        # Test non-existent session
        response = client.post('/api/study-sessions/99999/review', json={
            'reviews': [{'word_id': 1, 'is_correct': True}]
        })
        assert response.status_code == 404
        assert 'Study session not found' in response.get_json()['error']

    finally:
        cursor.close()

def test_submit_study_session_review_prevent_double_submission(client, app):
    """Test that a study session cannot be reviewed twice"""
    cursor = app.db.cursor()
    try:
        # Create test data
        cursor.execute('''
            INSERT INTO groups (name, created_at) 
            VALUES ('Test Group', datetime('now'))
        ''')
        group_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO study_activities (name, created_at) 
            VALUES ('Test Activity', datetime('now'))
        ''')
        activity_id = cursor.lastrowid

        # Create test word
        cursor.execute('''
            INSERT INTO words (kanji, romaji, english, created_at) 
            VALUES ('犬', 'inu', 'dog', datetime('now'))
        ''')
        word_id = cursor.lastrowid

        # Create completed study session
        cursor.execute('''
            INSERT INTO study_sessions (
                group_id, 
                study_activity_id, 
                created_at,
                completed,
                updated_at
            ) VALUES (?, ?, datetime('now'), 1, datetime('now'))
        ''', (group_id, activity_id))
        session_id = cursor.lastrowid

        # Add word review item
        cursor.execute('''
            INSERT INTO word_review_items (
                study_session_id, 
                word_id, 
                correct, 
                created_at
            ) VALUES (?, ?, 1, datetime('now'))
        ''', (session_id, word_id))

        app.db.commit()

        # Attempt to submit review for completed session
        response = client.post(f'/api/study-sessions/{session_id}/review', json={
            'reviews': [
                {'word_id': word_id, 'is_correct': True}
            ]
        })

        assert response.status_code == 400
        assert 'Study session is already completed' in response.get_json()['error']

    finally:
        cursor.close()

def test_submit_study_session_review_requires_all_words(client, app):
    """Test that all words in a session must be reviewed together"""
    cursor = app.db.cursor()
    try:
        # Create test data
        cursor.execute('''
            INSERT INTO groups (name, created_at) 
            VALUES ('Test Group', datetime('now'))
        ''')
        group_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO study_activities (name, created_at) 
            VALUES ('Test Activity', datetime('now'))
        ''')
        activity_id = cursor.lastrowid

        # Create test words
        cursor.execute('''
            INSERT INTO words (kanji, romaji, english, created_at) 
            VALUES 
                ('犬', 'inu', 'dog', datetime('now')),
                ('猫', 'neko', 'cat', datetime('now'))
        ''')
        word1_id = cursor.lastrowid
        word2_id = cursor.lastrowid - 1

        # Create study session
        cursor.execute('''
            INSERT INTO study_sessions (
                group_id, 
                study_activity_id, 
                created_at,
                completed
            ) VALUES (?, ?, datetime('now'), 0)
        ''', (group_id, activity_id))
        session_id = cursor.lastrowid

        # Add word review items for both words
        for word_id in [word1_id, word2_id]:
            cursor.execute('''
                INSERT INTO word_review_items (
                    study_session_id, 
                    word_id, 
                    correct, 
                    created_at
                ) VALUES (?, ?, 0, datetime('now'))
            ''', (session_id, word_id))

        app.db.commit()

        # Attempt to submit review for only one word
        response = client.post(f'/api/study-sessions/{session_id}/review', json={
            'reviews': [
                {'word_id': word1_id, 'is_correct': True}
            ]
        })

        assert response.status_code == 400
        assert 'All words in the session must be reviewed' in response.get_json()['error']

    finally:
        cursor.close() 