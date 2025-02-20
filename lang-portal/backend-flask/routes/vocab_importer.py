from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import requests
import json
import os


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv('GROQ_API_KEY')  # Add to .env file

def generate_llm_prompt(word_category):
    return {
        "model": "mixtral-8x7b-32768",  # Groq's Mixtral model
        "messages": [{
            "role": "system",
            "content": "You are a Japanese language expert. Return responses in JSON format only."
        }, {
            "role": "user",
            "content": f"""Create a list of 5 Japanese {word_category}. Return the Kanji, Romaji, English and Japaneseword parts in this exact JSON format:
            [
            {{
                "kanji": "山",
                "romaji": "yama",
                "english": "mountain",
                "parts": [
                {{
                    "kanji": "山",
                    "romaji": "yama"
                }}
                ]
            }}
            ]"""
        }]
    }

def load(app):
  @app.route('/get_new_words', methods=['POST'])
  @cross_origin()
  def get_new_words():
      word_category = request.json.get('word_category')
      if not word_category:
          return jsonify({"error": "Word category is required"}), 400
      
      try:
          response = requests.post(
              GROQ_API_URL,
              headers={
                  "Authorization": f"Bearer {GROQ_API_KEY}",
                  "Content-Type": "application/json"
              },
              json=generate_llm_prompt(word_category)
          )
          response.raise_for_status()
          
          data = response.json()
          content = data['choices'][0]['message']['content']
          words = json.loads(content)
          
          return jsonify(words)
          
      except Exception as e:
          return jsonify({"error": str(e)}), 500

  @app.route('/import_words', methods=['POST'])
  @cross_origin()
  def import_words():
      words = request.json.get('words')
      if not words:
          return jsonify({"error": "Words data is required"}), 400
      
      try:
          cursor = app.db.cursor()
          
          for word_data in words:
              # Convert parts array to JSON string
              parts_json = json.dumps(word_data['parts'])
              
              cursor.execute(
                  "SELECT id FROM words WHERE kanji = ? AND romaji = ?",
                  (word_data['kanji'], word_data['romaji'])
              )
              existing_word = cursor.fetchone()
              
              if not existing_word:
                  #print(f"Inserting word: {word_data['kanji']} {word_data['romaji']} {word_data['english']} {parts_json}")
                  cursor.execute(
                      "INSERT INTO words (kanji, romaji, english, parts) VALUES (?, ?, ?, ?)",
                      (word_data['kanji'], word_data['romaji'], word_data['english'], parts_json)
                  )
          
          app.db.commit()
          return jsonify({"message": f"Successfully imported {len(words)} words"})
          
      except Exception as e:
          print(f"Error importing words: {str(e)}")
          if 'app.db' in locals():
              app.db.rollback()
          return jsonify({"error": str(e)}), 500