import os
import sys
import sqlite3
import json
from flask import Flask

class Db:
    def __init__(self, database='words.db'):
        self.database = database
        self.connection = None

    def get(self):
        if not hasattr(self, '_connection'):
            self._connection = sqlite3.connect(self.database)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def commit(self):
        self.get().commit()

    def cursor(self):
        return self.get().cursor()

    def sql(self, filepath):
        with open(os.path.join('sql', filepath), 'r') as file:
            return file.read()

    def load_json(self, filepath):
        with open(filepath, 'r') as file:
            return json.load(file)

    def setup_tables(self, cursor):
        cursor.execute(self.sql('setup/create_table_words.sql'))
        self.commit()

        cursor.execute(self.sql('setup/create_table_word_reviews.sql'))
        self.commit()

        cursor.execute(self.sql('setup/create_table_word_review_items.sql'))
        self.commit()

        cursor.execute(self.sql('setup/create_table_groups.sql'))
        self.commit()

        cursor.execute(self.sql('setup/create_table_word_groups.sql'))
        self.commit()

        cursor.execute(self.sql('setup/create_table_study_activities.sql'))
        self.commit()

        cursor.execute(self.sql('setup/create_table_study_sessions.sql'))
        self.commit()

    def import_study_activities_json(self, cursor, data_json_path):
        study_activities = self.load_json(data_json_path)
        for activity in study_activities:
            cursor.execute('''
            INSERT INTO study_activities (name, url, preview_url) VALUES (?, ?, ?)
            ''', (activity['name'], activity['url'], activity['preview_url']))
        self.commit()

    def import_word_json(self, cursor, group_name, data_json_path):
        cursor.execute('INSERT INTO groups (name) VALUES (?)', (group_name,))
        self.commit()

        cursor.execute('SELECT id FROM groups WHERE name = ?', (group_name,))
        group_id = cursor.fetchone()[0]

        words = self.load_json(data_json_path)

        for word in words:
            cursor.execute('''
                INSERT INTO words (kanji, romaji, english, parts) VALUES (?, ?, ?, ?)
            ''', (word['kanji'], word['romaji'], word['english'], json.dumps(word['parts'])))
            
            word_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO word_groups (word_id, group_id) VALUES (?, ?)
            ''', (word_id, group_id))
        self.commit()

        cursor.execute('''
            UPDATE groups
            SET words_count = (
                SELECT COUNT(*) FROM word_groups WHERE group_id = ?
            )
            WHERE id = ?
        ''', (group_id, group_id))

        self.commit()
        print(f"Successfully added {len(words)} words to the '{group_name}' group.")

    def init(self, app):
        cursor = self.cursor()
        self.setup_tables(cursor)
        self.import_word_json(
            cursor=cursor,
            group_name='Core Verbs',
            data_json_path='seed/data_verbs.json'
        )
        self.import_word_json(
            cursor=cursor,
            group_name='Core Adjectives',
            data_json_path='seed/data_adjectives.json'
        )
        self.import_study_activities_json(
            cursor=cursor,
            data_json_path='seed/study_activities.json'
        )

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__)
    db = Db()
    db.init(app)
    print("Database initialized successfully.") 