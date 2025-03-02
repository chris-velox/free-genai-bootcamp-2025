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

## Add DuckDuckGo as search engine

```bash
❯ uv run run_crew
warning: `VIRTUAL_ENV=/Users/chrisecks/code/free-genai-bootcamp-2025/.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
# Agent: German Song Lyrics Researcher
## Task: Search for and retrieve the lyrics of the German song: Rock me Amadeus. Include both the original German lyrics and any available metadata.



# Agent: German Song Lyrics Researcher
## Thought: Thought: I need to find the lyrics for "Rock me Amadeus"
## Using tool: GERMAN LYRICS SEARCH
## Tool Input: 
"{\"song_title\": \"Rock me Amadeus\"}"
## Tool Output: 

Found lyrics for: Rock me Amadeus

Original German Lyrics:
----------------------
Er war ein Punker
Und er lebte in der großen Stadt
Es war in Wien, war Vienna
Wo er alles tat
Er hatte Schulden denn er trank
Doch ihn liebten alle Frauen
Und jede rief
Come and rock me Amadeus

Er war Superstar
Er war populär
Er war so exaltiert
Because er hatte Flair
Er war ein Virtuose
War ein Rockidol
Und alles rief
Come and rock me Amadeus
Amadeus Amadeus, Amadeus
Amadeus Amadeus, Amadeus
Amadeus Amadeus - oh oh oh Amadeus

Song Information:
----------------
Artist: Falco
Year: 1985
Source: Mock Database



# Agent: German Song Lyrics Researcher
## Final Answer: 
Er war ein Punker
Und er lebte in der großen Stadt
Es war in Wien, war Vienna
Wo er alles tat
Er hatte Schulden denn er trank
Doch ihn liebten alle Frauen
Und jede rief
Come and rock me Amadeus

Er war Superstar
Er war populär
Er war so exaltiert
Because er hatte Flair
Er war ein Virtuose
War ein Rockidol
Und alles rief
Come and rock me Amadeus
Amadeus Amadeus, Amadeus
Amadeus Amadeus, Amadeus
Amadeus Amadeus - oh oh oh Amadeus


# Agent: German Language Vocabulary Analyst
## Task: Analyze the provided German lyrics and extract key vocabulary words. Include their meanings and usage context.



# Agent: German Language Vocabulary Analyst
## Using tool: German Vocabulary Extractor
## Tool Input: 
"{\"lyrics\": \"Er war ein Punker\\nUnd er lebte in der gro\\u00dfen Stadt\\nEs war in Wien, war Vienna\\nWo er alles tat\\nEr hatte Schulden denn er trank\\nDoch ihn liebten alle Frauen\\nUnd jede rief\\nCome and rock me Amadeus\\n\\nEr war Superstar\\nEr war popul\\u00e4r\\nEr war so exaltiert\\nBecause er hatte Flair\\nEr war ein Virtuose\\nWar ein Rockidol\\nUnd alles rief\\nCome and rock me Amadeus\\nAmadeus Amadeus, Amadeus\\nAmadeus Amadeus, Amadeus\\nAmadeus Amadeus - oh oh oh Amadeus\"}"
## Tool Output: 
List of extracted vocabulary words with meanings


# Agent: German Language Vocabulary Analyst
## Final Answer: 
* **Punker:** Punks often subvert social norms and have a rebellious outlook. _Context:_ The song describes a person ("Er war ein Punker") who lived in a big city.
* **Großstadt:** City. _Context:_ The song describes a person ("Und er lebte in der großen Stadt") who lived in a large city.
* **Wien:** Vienna, the capital of Austria. _Context:_ The song specifies the city where this person lived ("Es war in Wien, war Vienna").
* **Schulden:** Debts. _Context:_ The phrase "Er hatte Schulden denn er trank" suggests that he drank excessively and accumulated debts.
* **Trank:** Drank, specifically alcoholic beverages.  _Context:_  ("Er hatte Schulden denn er trank") implies he drank heavily, leading to financial problems.
* **Liebeten:** Loved.  _Context:_ "Doch ihn liebten alle Frauen" indicates that despite his issues, he was popular with women.
* **Populär:** Popular, well-liked. _Context:_ Describing him as "Er war Superstar, Er war populär" paints him as a beloved celebrity.
* **Exaltiert:** Exalted, euphoric, elevated.  _Context:_ The word suggests extreme excitement and happiness ("Er war so exaltiert").
* **Flair:** Charisma, a natural talent or gift. _Context:_ "Because er hatte Flair" emphasizes that his success stemmed in part from his charisma.
* **Virtuose:** Virtuoso, someone exceptionally skilled in a performing art. _Context:_  This reinforces his talent and mastery as a musician ("Er war ein Virtuose"). 
* **Rockidol:** Rock idol, a celebrity musician revered by fans. _Context:_ This emphasizes his status as a musician admired by many ("War ein Rockidol").


# Agent: German Song Lyricist
## Task: Create new German song lyrics using the provided vocabulary words. The song should be creative while incorporating the specified vocabulary naturally.



# Agent: German Song Lyricist
## Using tool: German Song Generator
## Tool Input: 
"{\"vocabulary\": \"\\\"Punker\\\", \\\"Gro\\u00dfstadt\\\", \\\"Wien\\\", \\\"Schulden\\\", \\\"Trank\\\", \\\"Liebeten\\\", \\\"Popul\\u00e4r\\\", \\\"Exaltiert\\\", \\\"Flair\\\", \\\"Virtuose\\\", \\\"Rockidol\\\"\", \"style\": \"\\\"Rock\\\"}\"}"
## Tool Output: 
Generated German song lyrics


# Agent: German Song Lyricist
## Final Answer: 

In der Großstadt Wien, 
Wo der Asphalt glüht,
Ein Punker, wild und frei,
Mit Gitarre und Wut.

Schulden häufte er, 
Denn er trank zu viel,
Doch die Frauen liebten ihn, 
Sein Flair war unverbesserlich.

Er war populär, 
Ein Rockidol so grandios,
Exaltiert, auf der Bühne, 
Virtuose seiner Melodien.

Come and rock me,
Rock me like a Punker,
In Wien, in der Großstadt,
Feuer färbt den Schatten.

# Agent: German-English Translator
## Task: Translate both the original and newly generated German songs to English, maintaining the artistic meaning and style.



# Agent: German-English Translator
## Using tool: German-English Translator
## Tool Input: 
"{\"text\": \"In der Gro\\u00dfstadt Wien,\\nWo der Asphalt gl\\u00fcht,\\nEin Punker, wild und frei,\\nMit Gitarre und Wut.\\n\\nSchulden h\\u00e4ufte er, \\nDenn er trank zu viel,\\nDoch die Frauen liebten ihn, \\nSein Flair war unverbesserlich.\\n\\nEr war popul\\u00e4r, \\nEin Rockidol so grandios,\\nExaltiert, auf der B\\u00fchne, \\nVirtuose seiner Melodien.\\n\\nCome and rock me,\\nRock me like a Punker,\\nIn Wien, in der Gro\\u00dfstadt,\\nFeuer f\\u00e4rbt den Schatten.\"}"
## Tool Output: 
English translation of the text


# Agent: German-English Translator
## Final Answer: 
In the big city of Vienna,
Where the asphalt glows,
A punk, wild and free,
With guitar and wrath.

He accumulated debts,
Because he drank too much,
But the women loved him,
His charisma was irreplaceable. 

He was popular,
Such a grandiose rock idol,
Exalted, on stage,
Virtuoso of his melodies. 


Come and rock me,
Rock me like a punk,
In Vienna, in the big city,
Fire colors the shadows.

```