# Vocab Importer

Create a front-end/back-end app that will:

1. Take a word category (noun, verb, adjective) from user
1. Query an LLM to generate a list of words (at least 5)
1. Return the list of words in a JSON format compatible with the lang-portal seed files

```json
[
  {
    "kanji": "いい",
    "romaji": "ii",
    "english": "good",
    "parts": [
      { "kanji": "い", "romaji": ["i"] },
      { "kanji": "い", "romaji": ["i"] }
    ]
  }
]
```  

1. Import the returned JSON into the langage database

## Preliminary Investigation

**Q: Will gemma:2b be able to generate Japanese words and return Kanji, Romaji, English and word parts?**

A: Using my WebUI-Ollama containers, I was able to query (though it was slow) gemma:2b to provide a list of 5 Japanese nouns. It returned a list:

> 1. **山** (Yama) - mountain
> 2. **川** (Kawaii) - river
> 3. **森** (Mori) - forest
> 4. **海** (Kai) - sea
> 5. **tree** (Bō) - tree

I'm not sure why `tree` came back in English instead of Kanji. Maybe a limit of the model?

**Q: Can gemma:2b convert the word list to JSON format?**

A: Ollama/gemma:2b was able to convert the reply into JSON:

```json
[
  {
    "kanji": "山",
    "romaji": "Yama",
    "english": "mountain",
    "parts": [
      {
        "kanji": "い",
        "romaji": "i"
      },
      {
        "kanji": "山",
        "romaji": "Yama"
      }
    ]
  },
  {
    "kanji": "川",
    "romaji": "Kawaii",
    "english": "river",
    "parts": [
      {
        "kanji": "かわ",
        "romaji": "kawa"
      },
      {
        "kanji": "川",
        "romaji": "Kawaii"
      }
    ]
  },
  {
    "kanji": "森",
    "romaji": "Mori",
    "english": "forest",
    "parts": [
      {
        "kanji": "もり",
        "romaji": "mora"
      },
      {
        "kanji": "森",
        "romaji": "Mori"
      }
    ]
  },
  {
    "kanji": "海",
    "romaji": "Kai",
    "english": "sea",
    "parts": [
      {
        "kanji": "海の",
        "romaji": "kai"
      },
      {
        "kanji": "海",
        "romaji": "Kai"
      }
    ]
  },
  {
    "kanji": "木",
    "romaji": "Bō",
    "english": "tree",
    "parts": [
      {
        "kanji": "木の",
        "romaji": "moko"
      },
      {
        "kanji": "木",
        "romaji": "Bō"
      }
    ]
  }
]
```

It seems to have fixed the `tree` Kanji that came back wrong. Possible output conversion issue.

## Approach

I would like to add this feature directly into the lang-portal app.

The backend can handle the database import and LLM query. The frontend will simply handle the user input.

### Front-end

Add a navigation item to the navigation menu: "Import Word Group"

"Import Word Group" will open a page with an input field {word_category} for the word category and a button to "Get Words".

The "Get Words" button will trigger an API call to the backend (/get_new_words).

When /get_new_words returns the JSON, it will display the JSON on the screen for the user to review and the front-end will display an "Import" and "Cancel" buttons. The "Cancel" button will reset the page to a blank input field and "Get Words" button.

The "Import" button will call the /import_words route. This route will import the JSON response into the database.

### Back-end

The route /get_new_words will trigger a query to the LLM running on [Ollama locally](http://localhost:8008), which uses an OpenAI compliant API structure.

The system prompt will need to be:

```text
Create a list of 5 Japanese {word_category}. Return the Kanji, Romaji, English and word parts. The list should be returned to the front-end in JSON in the following format:
[
  {
    "kanji": "山",
    "romaji": "Yama",
    "english": "mountain",
    "parts": [
      {
        "kanji": "い",
        "romaji": "i"
      },
      {
        "kanji": "山",
        "romaji": "Yama"
      }
    ]
  },
  {
    "kanji": "川",
    "romaji": "Kawaii",
    "english": "river",
    "parts": [
      {
        "kanji": "かわ",
        "romaji": "kawa"
      },
      {
        "kanji": "川",
        "romaji": "Kawaii"
      }
    ]
  }
]
```

The /import_words route will import the JSON response into the database.

### Results

It took a while, but I was able to integrate the word importer into the Lang-Portal app.

I had to replace going to Ollama-server because Gemma:2b was not replying with five of the same word, or with Kanji in place of Romaji.

I ended up replacing Ollama with Groq, which returned the JSON format I wanted.
