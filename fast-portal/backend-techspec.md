# Backend Server Technical Specs

## Business Goal

A German language teaching school wants to create a prototype teaching portal to enhance one-on-one and in-person teaching sessions. The system will include three things:
- Inventory of words that can be learned
- An activity record store for the student records of study sessions
    - words studied
    - correct/incorrect
- Links to start study activities as they are added

## Technical Requirements

The backend of the system:
- built using FastAPI to support API endpoints
- support interchangeable databases
    - sqlite3
    - mysql
    - mariadb
    - postgresql
- return JSON to all API calls
- prototype will support a single user

### Database Schema

Table: words - vocabulary words
- id: integer
- german: string
- english: string

Table: groups - groups of words
- id: integer
- group: string

Table: words_groups
- id: integer
- word_id: integer - foreign key to words table entry
- group_id: integer - foreign key to groups table entry

Table: study_sessions - records of student study sessions
- id: integer
- group_id: integer - foreign key to groups table entry
- created: datetime - when the record was created
- study_activity_id: integer - foreign key to study_activities table entry

Table: study_activities - records the activity that links a session to a group
- id: integer
- study_session_id: integer - foreign key to study_sessions table entry
- group_id: integer - foreign key to groups table entry
- created: datetime - when the record was created

Table: word_reviews - record of word practice with correct or incorrect
- id: integer
- word_id: integer - foreign key to words table entry
- study_session_id: integer - foreign key to study_sessions table entry
- correct: boolean - record if word was used correctly in study session
- created: datetime - when the record was created

### API Endpoints

GET /api/last_study_session
- returns
    - study_session_id as a link to the session
    - created date/time
    - group studied
    - number of words in the activity
    - number of words correct
- based on most recent (latest) study_session:created value

GET /api/study_progress
- returns
    - the total number of correct words reviewed
    - the total number of possible words

GET /api/stats
- returns
    - success rate as the number of correct words out of the total number of word review attempts
    - total number of study sessions completed
    - total number of groups attempted
    - study streak as the longest list of consecutive study session days
    

