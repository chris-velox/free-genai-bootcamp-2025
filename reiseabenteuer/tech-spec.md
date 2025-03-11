# Reiseabenteur (Travel Adventure)

Reiseabenteur is an immersive language learning tool that uses descriptions of locations to learn the German language.

## Structure

The application will have a React.js front-end using typescript and a fastAPI backend. It will use various AI tools to retrieve descriptions of cities where the student might want to visit, play the descriptions using TTS and create questions to ask the student about what they just heard. The solution is for a single user.

## Technology

```yaml
Front-end: 
  - Framework: React.js
  - Folder: frontend-react
  - API calls: JSON
Back-end:
  - Framework: FastAPI
  - Folder: backend-fastapi
  - API: JSON
GenAI:
  - Groq for place descriptions
  - Qdrant for vector embedding
  - DuckDuckGo for internet searches
  - TTS?...maybe later, $$
```

## Solution

### Front-end

The front-end will provide the user interface. It will make calls to the back-end via API calls to execute logic.

The front-end will:

- When the user accesses the web app, it will ask the user to make up to three selections about what the user would like to see on their travels. These will be in English.
  - Interests:
    - Outdoor activities
    - Site seeing
    - Historical landmarks
    - Archaeological landmarks
    - Museums
    - Local culture
    - Nature sites
- The front-end sends the selections to the backend for the backend to retrieve and return a list of 5 possible locations in Germany that match the user's selections. The list will be returned in German.

```json
"activities": [
    "activity 1",
    "activity 2",
    ...
]
```

- The front-end will display the list of locations and prompt the user either confirm their itinerary or retrieve another list. The language of the buttons should be German.

```json
"destinations" : [
    "destination 1",
    "destination 2",
    ...
]
```

- If the users starts their itinerary, the front-end will send the list of destinations to the backend, which will generate descriptions for each location.

```json
"destinations" : [
    {
      "destination_name": "name",
      "state": "state",
      "activities": [
        "activity 1",
        "activity 2",
        ...
      ],
      "description": "text description"
      },
    ...
]
```

- The backend will generate questions and answers and return each description and related questions one at a time

```json
"itinerary": [
    "destination 1": {
        "description": "text description",
        "questions": [
            "question1":
                {
                    "question": "text",
                    "choices": [
                        "choice1",
                        "choice2",
                        "choice3",
                        "choice4"
                    ],
                    "correct_choice": "choice label"
                }
        ]
    }
]
```

- The backend returns the first description for the user to practice. It will display/play the description, then on a new panel/page display the questions with answer choices.
- The front-end will accept chosen answers and tell user if their answer is correct or incorrect.
- The front-end will move through each subsequent description and question/answer sets until complete.

### Back-end

The backend will receive API calls from the front-end via endpoints that accept JSON.

- POST "/api/get_destinations"
  When the backend receives the list of activities in JSON, it will initiate a duckduckgo search for the top locations in Germany that provide the activities selected by the user. It will look pull a list of destinations from the top 3 articles returned by duckduckgo. It will then return a JSON list of destinations with the following structure:
  
```json
"destinations" : [
    {
      "destination_name": "name",
      "state": "state",
      "activities": [
        "activity 1",
        "activity 2",
        ...
      ],
      "description": "text description"
      },
    ...
]
```

- GET "/api/get_description
  The backend should gather information from each link such that:
  - It can create three points of interest for each location
  - There should be at least one point of interest for each activity. If the user didn't select three, find multiple points of interest for one of the selected interests. There should always be three points of interest for each destination.
  Generate a text description in German for each point of interest and combine them into a single multi-paragraph text description to return in the "description" key in the JSON structure.
  - The back-end returns the information for the itinerary to the front-end in JSON

