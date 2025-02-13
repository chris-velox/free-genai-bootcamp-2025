from flask import request, jsonify, g
from flask_cors import cross_origin
from datetime import datetime
import math
import logging

def load(app):
  @app.route('/api/study-sessions', methods=['POST'])
  @cross_origin()
  def create_study_session():
    try:
      # Log incoming request
      logging.info(f"Creating new study session. Request data: {request.get_json()}")

      # Validate request has JSON data
      if not request.is_json:
        logging.warning("Request missing JSON data")
        return jsonify({"error": "Request must be JSON"}), 400

      data = request.get_json()
      
      # Validate required fields
      required_fields = ['group_id', 'study_activity_id', 'word_ids']
      for field in required_fields:
        if field not in data:
          logging.warning(f"Request missing required field: {field}")
          return jsonify({"error": f"Missing required field: {field}"}), 400
      
      # Validate data types
      if not isinstance(data['group_id'], int):
        logging.warning(f"Invalid group_id type: {type(data['group_id'])}")
        return jsonify({"error": "group_id must be an integer"}), 400
      if not isinstance(data['study_activity_id'], int):
        logging.warning(f"Invalid study_activity_id type: {type(data['study_activity_id'])}")
        return jsonify({"error": "study_activity_id must be an integer"}), 400
      if not isinstance(data['word_ids'], list) or not all(isinstance(x, int) for x in data['word_ids']):
        logging.warning(f"Invalid word_ids format: {data['word_ids']}")
        return jsonify({"error": "word_ids must be an array of integers"}), 400
      if len(data['word_ids']) == 0:
        logging.warning("Empty word_ids array")
        return jsonify({"error": "word_ids cannot be empty"}), 400

      cursor = app.db.cursor()

      # Verify group and activity exist
      logging.info(f"Verifying group_id={data['group_id']} and activity_id={data['study_activity_id']}")
      cursor.execute('''
        SELECT g.id, sa.id 
        FROM groups g, study_activities sa 
        WHERE g.id = ? AND sa.id = ?
      ''', (data['group_id'], data['study_activity_id']))
      
      if not cursor.fetchone():
        logging.warning(f"Invalid group_id={data['group_id']} or activity_id={data['study_activity_id']}")
        return jsonify({"error": "Invalid group_id or study_activity_id"}), 400

      # Verify all words exist
      logging.info(f"Verifying word_ids: {data['word_ids']}")
      word_ids_str = ','.join('?' * len(data['word_ids']))
      cursor.execute(f'''
        SELECT COUNT(*) as count 
        FROM words 
        WHERE id IN ({word_ids_str})
      ''', data['word_ids'])
      
      if cursor.fetchone()['count'] != len(data['word_ids']):
        logging.warning(f"One or more invalid word_ids in: {data['word_ids']}")
        return jsonify({"error": "One or more word_ids are invalid"}), 400

      # Create study session
      logging.info("Creating new study session record")
      cursor.execute('''
        INSERT INTO study_sessions (group_id, study_activity_id, created_at)
        VALUES (?, ?, datetime('now'))
      ''', (data['group_id'], data['study_activity_id']))
      
      session_id = cursor.lastrowid
      logging.info(f"Created study session with id={session_id}")

      # Create word review items
      logging.info(f"Creating {len(data['word_ids'])} word review items")
      for word_id in data['word_ids']:
        cursor.execute('''
          INSERT INTO word_review_items (study_session_id, word_id, correct, created_at)
          VALUES (?, ?, 0, datetime('now'))
        ''', (session_id, word_id))

      app.db.commit()
      logging.info("Successfully committed transaction")

      # Fetch the created session details
      cursor.execute('''
        SELECT 
          ss.id,
          ss.group_id,
          g.name as group_name,
          sa.id as activity_id,
          sa.name as activity_name,
          ss.created_at,
          COUNT(wri.id) as review_items_count
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
        WHERE ss.id = ?
        GROUP BY ss.id
      ''', (session_id,))
      
      session = cursor.fetchone()
      logging.info(f"Returning created session: {session}")

      return jsonify({
        'id': session['id'],
        'group_id': session['group_id'],
        'group_name': session['group_name'],
        'activity_id': session['activity_id'],
        'activity_name': session['activity_name'],
        'start_time': session['created_at'],
        'end_time': session['created_at'],
        'review_items_count': session['review_items_count']
      }), 201

    except Exception as e:
      logging.error(f"Error creating study session: {str(e)}", exc_info=True)
      app.db.rollback()
      return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions', methods=['GET'])
  @cross_origin()
  def get_study_sessions():
    try:
      cursor = app.db.cursor()
      
      # Get pagination parameters
      page = request.args.get('page', 1, type=int)
      per_page = request.args.get('per_page', 10, type=int)
      offset = (page - 1) * per_page

      # Get total count
      cursor.execute('''
        SELECT COUNT(*) as count 
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
      ''')
      total_count = cursor.fetchone()['count']

      # Get paginated sessions
      cursor.execute('''
        SELECT 
          ss.id,
          ss.group_id,
          g.name as group_name,
          sa.id as activity_id,
          sa.name as activity_name,
          ss.created_at,
          COUNT(wri.id) as review_items_count
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
        GROUP BY ss.id
        ORDER BY ss.created_at DESC
        LIMIT ? OFFSET ?
      ''', (per_page, offset))
      sessions = cursor.fetchall()

      return jsonify({
        'items': [{
          'id': session['id'],
          'group_id': session['group_id'],
          'group_name': session['group_name'],
          'activity_id': session['activity_id'],
          'activity_name': session['activity_name'],
          'start_time': session['created_at'],
          'end_time': session['created_at'],  # For now, just use the same time since we don't track end time
          'review_items_count': session['review_items_count']
        } for session in sessions],
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': math.ceil(total_count / per_page)
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions/<id>', methods=['GET'])
  @cross_origin()
  def get_study_session(id):
    try:
      cursor = app.db.cursor()
      
      # Get session details
      cursor.execute('''
        SELECT 
          ss.id,
          ss.group_id,
          g.name as group_name,
          sa.id as activity_id,
          sa.name as activity_name,
          ss.created_at,
          COUNT(wri.id) as review_items_count
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
        WHERE ss.id = ?
        GROUP BY ss.id
      ''', (id,))
      
      session = cursor.fetchone()
      if not session:
        return jsonify({"error": "Study session not found"}), 404

      # Get pagination parameters
      page = request.args.get('page', 1, type=int)
      per_page = request.args.get('per_page', 10, type=int)
      offset = (page - 1) * per_page

      # Get the words reviewed in this session with their review status
      cursor.execute('''
        SELECT 
          w.*,
          COALESCE(SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END), 0) as session_correct_count,
          COALESCE(SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END), 0) as session_wrong_count
        FROM words w
        JOIN word_review_items wri ON wri.word_id = w.id
        WHERE wri.study_session_id = ?
        GROUP BY w.id
        ORDER BY w.kanji
        LIMIT ? OFFSET ?
      ''', (id, per_page, offset))
      
      words = cursor.fetchall()

      # Get total count of words
      cursor.execute('''
        SELECT COUNT(DISTINCT w.id) as count
        FROM words w
        JOIN word_review_items wri ON wri.word_id = w.id
        WHERE wri.study_session_id = ?
      ''', (id,))
      
      total_count = cursor.fetchone()['count']

      return jsonify({
        'session': {
          'id': session['id'],
          'group_id': session['group_id'],
          'group_name': session['group_name'],
          'activity_id': session['activity_id'],
          'activity_name': session['activity_name'],
          'start_time': session['created_at'],
          'end_time': session['created_at'],  # For now, just use the same time
          'review_items_count': session['review_items_count']
        },
        'words': [{
          'id': word['id'],
          'kanji': word['kanji'],
          'romaji': word['romaji'],
          'english': word['english'],
          'correct_count': word['session_correct_count'],
          'wrong_count': word['session_wrong_count']
        } for word in words],
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': math.ceil(total_count / per_page)
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions/<id>/review', methods=['POST'])
  @cross_origin()
  def submit_study_session_review(id):
    try:
        # Validate JSON
        if not request.is_json:
            logging.warning("Request missing JSON data")
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()

        # Validate reviews array exists
        if 'reviews' not in data:
            logging.warning("Missing reviews array in request")
            return jsonify({"error": "Missing reviews array"}), 400

        reviews = data['reviews']

        # Validate reviews format
        if not isinstance(reviews, list):
            logging.warning(f"Invalid reviews format: {type(reviews)}")
            return jsonify({"error": "Reviews must be an array"}), 400

        # Validate each review item
        for review in reviews:
            if not isinstance(review, dict):
                logging.warning(f"Invalid review item format: {type(review)}")
                return jsonify({"error": "Each review must be an object"}), 400
            if 'word_id' not in review or 'is_correct' not in review:
                logging.warning(f"Missing required fields in review: {review}")
                return jsonify({"error": "Each review must have word_id and is_correct"}), 400
            if not isinstance(review['word_id'], int):
                logging.warning(f"Invalid word_id type: {type(review['word_id'])}")
                return jsonify({"error": "word_id must be an integer"}), 400
            if not isinstance(review['is_correct'], bool):
                logging.warning(f"Invalid is_correct type: {type(review['is_correct'])}")
                return jsonify({"error": "is_correct must be a boolean"}), 400

        cursor = app.db.cursor()

        # Check if study session exists and is not completed
        cursor.execute('''
            SELECT id, completed 
            FROM study_sessions 
            WHERE id = ?
        ''', (id,))
        
        session = cursor.fetchone()
        if not session:
            logging.warning(f"Study session not found: {id}")
            return jsonify({"error": "Study session not found"}), 404
            
        if session['completed']:
            logging.warning(f"Attempted to review completed session: {id}")
            return jsonify({"error": "Study session is already completed"}), 400

        # Get total number of words in session
        cursor.execute('''
            SELECT COUNT(*) as total_words
            FROM word_review_items
            WHERE study_session_id = ?
        ''', (id,))
        total_words = cursor.fetchone()['total_words']

        # Check if all words are being reviewed
        if len(reviews) != total_words:
            logging.warning(f"Incomplete review submission. Expected {total_words} words, got {len(reviews)}")
            return jsonify({
                "error": "All words in the session must be reviewed",
                "expected_words": total_words,
                "submitted_words": len(reviews)
            }), 400

        # Verify all words exist in the session
        word_ids = [review['word_id'] for review in reviews]
        word_ids_str = ','.join('?' * len(word_ids))

        cursor.execute(f'''
            SELECT COUNT(DISTINCT word_id) as count
            FROM word_review_items
            WHERE study_session_id = ? 
            AND word_id IN ({word_ids_str})
        ''', [id] + word_ids)

        if cursor.fetchone()['count'] != len(word_ids):
            logging.warning(f"Invalid word_ids for session {id}: {word_ids}")
            return jsonify({"error": "One or more word_ids are invalid for this session"}), 400

        # Update word review items and word stats
        for review in reviews:
            # Update the review item
            cursor.execute('''
                UPDATE word_review_items
                SET correct = ?
                WHERE study_session_id = ? 
                AND word_id = ?
            ''', (1 if review['is_correct'] else 0, id, review['word_id']))

            # Update the word's overall stats
            cursor.execute('''
                UPDATE words
                SET correct_count = correct_count + ?,
                    wrong_count = wrong_count + ?
                WHERE id = ?
            ''', (
                1 if review['is_correct'] else 0,
                0 if review['is_correct'] else 1,
                review['word_id']
            ))

        # Update study session completion time
        cursor.execute('''
            UPDATE study_sessions 
            SET updated_at = datetime('now'),
                completed = 1
            WHERE id = ?
        ''', (id,))

        # Get updated session stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_reviews,
                SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) as correct_count,
                SUM(CASE WHEN correct = 0 THEN 1 ELSE 0 END) as wrong_count
            FROM word_review_items
            WHERE study_session_id = ?
        ''', (id,))

        stats = cursor.fetchone()

        app.db.commit()

        return jsonify({
            "message": "Review submitted successfully",
            "stats": {
                "total_reviews": stats['total_reviews'],
                "correct_count": stats['correct_count'],
                "wrong_count": stats['wrong_count']
            }
        }), 200

    except Exception as e:
        logging.error(f"Error submitting review: {str(e)}", exc_info=True)
        app.db.rollback()
        return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions/reset', methods=['POST'])
  @cross_origin()
  def reset_study_sessions():
    try:
      cursor = app.db.cursor()
      
      # First delete all word review items since they have foreign key constraints
      cursor.execute('DELETE FROM word_review_items')
      
      # Then delete all study sessions
      cursor.execute('DELETE FROM study_sessions')
      
      app.db.commit()
      
      return jsonify({"message": "Study history cleared successfully"}), 200
    except Exception as e:
      return jsonify({"error": str(e)}), 500