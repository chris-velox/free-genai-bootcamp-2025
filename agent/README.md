# Making an agent

I want to make an agent that can retrieve song lyrics for German songs from the internet, extract the lyrics, and then use the lyrics to generate a song.

I want to use CrewAI to make the agent.

## Tools

The steps can be done in any order, as determined by the agent.

- Tool: Retrieve song lyrics for a German song
- Tool: Extract vocabulary words
- Tool: Generate song
- Tool: Translate original song and new song to English
- Tool: Display results

## Development

1. Install CrewAI

```bash
uv pip install crewai crewai-tools
```

This installed 80 new packages.

2. Create a new CrewAI project

```bash
crewai create crew german_song_generator
```

```text
Creating folder german_song_generator...
Cache expired or not found. Fetching provider data from the web...
Downloading  [####################################]  346077/16612
Select a provider to set up:
1. openai
2. anthropic
3. gemini
4. nvidia_nim
5. groq
6. ollama
7. watson
8. bedrock
9. azure
10. cerebras
11. sambanova
12. other
q. Quit
Enter the number of your choice or 'q' to quit: 5
Select a model to use for Groq:
1. groq/llama-3.1-8b-instant
2. groq/llama-3.1-70b-versatile
3. groq/llama-3.1-405b-reasoning
4. groq/gemma2-9b-it
5. groq/gemma-7b-it
q. Quit
Enter the number of your choice or 'q' to quit: 4
Enter your GROQ API key (press Enter to skip): **********
API keys and model saved to .env file
Selected model: groq/gemma2-9b-it
  - Created german_song_generator/.gitignore
  - Created german_song_generator/pyproject.toml
  - Created german_song_generator/README.md
  - Created german_song_generator/knowledge/user_preference.txt
  - Created german_song_generator/src/german_song_generator/__init__.py
  - Created german_song_generator/src/german_song_generator/main.py
  - Created german_song_generator/src/german_song_generator/crew.py
  - Created german_song_generator/src/german_song_generator/tools/custom_tool.py
  - Created german_song_generator/src/german_song_generator/tools/__init__.py
  - Created german_song_generator/src/german_song_generator/config/agents.yaml
  - Created german_song_generator/src/german_song_generator/config/tasks.yaml
Crew german_song_generator created successfully!
```

This created a new directory called `german_song_generator` with a `crew.py` file.

3. Run the crew

```bash
crewai run crew.py
```

With UV, the command is:

```bash
uv run run_crew
```

I used Cursor to fill in the scaffolding created by CrewAI. It took a couple tries to get the errors resolved, but it does work. Not all that useful, but it works.

First prompt:

```text
In folder @german_song_generator  is the scaffolding for a crewAI agent to retrieve German song lyrics from the internet, extract vocabulary words from the lyrics and use the words to generate new song lyrics.
Here are the tools I want to use:
- Retrieve song lyrics for a German song
- Extract vocabulary words
- Generate song
- Translate original song and new song to English
- Display results

Fill in the scaffolding as necessary.
```

