# Language Learning Portal

A web application for learning Japanese vocabulary with flashcards and word management features.

## Features and Development History

### Initial Setup
- Basic Flask backend with SQLite database
- React frontend with basic routing
- Vocabulary flashcard system

### Added Features
- Word category management (nouns, verbs, adjectives)
- Database seeding system with initial vocabulary
- Testing infrastructure with pytest

### Word Importer Integration
- Added word import functionality using LLM (initially Gemma2:2b, later switched to Groq)
- Capability to generate Japanese words with Kanji, Romaji, and English translations
- Word parts breakdown for better learning
- Frontend interface for word import management
- [Vocab Importer](Readme-vocab-importer.md)

### Writing Practice Integration
- [Writing Practice](Readme-writing-practice.md)

## Running with Docker (Recommended)

### Prerequisites
- Docker
- Docker Compose

### Running the Application

1. Clone the repository
2. Navigate to the project directory
3. Build and start the containers:

```sh
docker-compose up --build
```

This will:
- Build and start the Flask backend API on http://localhost:5000
- Build and start the React frontend on http://localhost:3000
- Initialize the SQLite database with seed data

To stop the application:

```sh
docker-compose down
```

### Persistent Data
The SQLite database is persisted in the `backend-flask/instance` directory.

## Manual Installation (Alternative)

### Install Dependencies

```sh
pip install -r requirements.txt
```

### Setup Database

```sh
invoke init-db
```

### Run Application

#### Backend

```sh
cd backend-flask
python app.py
```

#### Frontend

```sh
cd frontend-react
npm install
npm run dev
```

## Development

The application uses:
- Flask for the backend API
- SQLite for data storage
- React with Vite for the frontend
- pytest for backend testing
- LLM integration for word generation
