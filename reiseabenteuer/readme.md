# Reiseabenteuer (Travel Adventure)

A multi-modal language immersion system for German with two games:

- Travel adventure to learn about places in Germany
- Flashcards for testing vocabulary knowledge

The games will ask questions of the user (hopefully with audio) and ask for the student to say the words to the system and see if they say the right one.

## Research

OpenVino had a promising "stack" for the travel adventure, but Whisper would not run on my system.

### Using Whisper on a Mac:

**Requirements:** SoundDevice and Whisper modules

```sh
uv pip install sounddevice
uv pip install 'numpy<2'
uv pip install git+https://github.com/openai/whisper.git 
```

I managed to get whisper working on my Mac with the help of Cursor. OpenVino still throws all sorts of errors, but it actually isn't that hard.

[whisper_test.py](whisper_test.py) gave me a basic framework for recording audio and transcribing it.

## Building the backend

```text
You are a travel writer and junior developer. Write me a FastAPI backend that will accept a list of travel activities (examples: outdoor activities, site seeing, historical landmarks, skiing, biking, hiking, etc) and retrieve a list of 5 destinations in germany that provide those activities. There will be a limit of three activities.
```

```text
Modify the code to use DuckDuckGo to search for the destinations.
```

```text
The response should be in JSON format.
```



```sh
uv pip install fastapi pydantic uvicorn duckduckgo_search
```

[travel_api.py](travel_api.py) is the backend.

``sh
uv pip install deep_translator
```

[deep_translator](https://github.com/nidhaloff/deep-translator) is a library that allows you to translate text from English to German.

Modify the initial code to read the top 3 articles returned by duckduckgo.

```sh
uv pip install trafilatura beautifulsoup4
```

[trafilatura](https://github.com/adbar/trafilatura) is a library that allows you to extract text from HTML.

[beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) is a library that allows you to parse HTML.

## Add vector database using qdrant

```sh
uv pip install pydantic qdrant_client sentence_transformers numpy
```

[qdrant](https://qdrant.tech/) is a vector database.

[sentence_transformers](https://www.sbert.net/) is a library that allows you to transform text into vectors.

[numpy](https://numpy.org/) is a library that allows you to work with arrays.

## To get things working

I'm using Gemma2:2b on Ollama Server to perform vocabulary translation.

```sh
ollama serve
ollama run gemma2:2b
```

I had to separate the vector databases for destinations and vocabulary because I was running into issues with using local Qdrant storage. A container or cloud solution would be a better approach. I also got a warning for Qdrant having over 20,000 points (23,735) in the vocabulary database. In total, the vocabulary database for the flashcard game has 24,119 words from CEFR levels A1, A2, B1, B2, and C1.

Vocabulary word list from https://github.com/Nordsword3m/German-Words.

## Next steps

- Add a frontend
- Add a container or cloud solution for Qdrant
- Add a frontend

## Test Stable Diffusion locally

```sh
uv pip install diffusers transformers torch
```

## Added frontend for flashcards

Modified backend to return random words, not same words over and over.

Modified front end to display some words in context to reinforce verb conjugations, use of types of adjectives based on word singular/plural and proper articles for nouns.

### Adding sound recording

```sh
pip install whisper sounddevice numpy soundfile
npm install @mui/icons-material
```
