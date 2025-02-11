import pytest
from datetime import datetime
import logging

@pytest.fixture(autouse=True)
def setup_logging():
    logging.basicConfig(level=logging.INFO)

def test_create_study_session_success(client, app):
    logging.info("Starting test_create_study_session_success")
    # Insert test data
    with app.db.cursor() as cursor:
        logging.info("Creating test data")
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

    # Create valid group and activity but test invalid word_ids
    with app.db.cursor() as cursor:
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

    response = client.post('/api/study-sessions', json={
        'group_id': group_id,
        'study_activity_id': activity_id,
        'word_ids': [99999]
    })
    assert response.status_code == 400
    assert 'One or more word_ids are invalid' in response.get_json()['error'] 