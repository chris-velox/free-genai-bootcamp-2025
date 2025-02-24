# Writing Practice Study Activity

Create a new Study Activity called "Writing Practice" within the `lang-portal` application.

The Writing Practice activity will appear on the existing Study Activity page of the app.

Writing Practice will use the same approaches, structure and languages as the current lang-portal application (eg, .tsx components for the frontend, .py for the backend)

Writing Practice will work as follows:

## Frontend

Writing Practice activity will have 3 pages:

- "Learn Kana" which will display an image of the Japanese Kana characters
- "Romaji to kana" which will display the Romaji for a Japanese Kana and provide a graphical space for drawn input
- "Kana to romaji" which will display a Japanese Kana and ask for the romaji input

The frontend will retrieve the kana dictionaries from the backend via an API call. The dictionaries are stored in kana_dictionaries.py.

### Learn Kana

- The frontend will ask "What type of kana do you want to learn?"
- The user will select either Hiragana or Katakana on the page using a radio button.
- Upon selection, the app will display a graphic for that particular kana group.
  - The graphic should be preloaded by the front-end component
  - Hiragana file will be img/Hiragana.jpg
  - Katakana file will be img/Katakana.jpg

### Romaji to kana

- The frontend will ask "What type of kana do you want to practice?"
- The user will select either Hiragana or Katakana on the page using a radio button.
- The frontend will display a random romaji kana from the appropriate Hiragana or Katakana dictionary retrieved from the backend via an API call.
- The frontend will present a drawable area where the user can draw a kana and submit it.
- The frontend will pass the submitted kana graphic as a png file to a backend api.
- The backend api will use manga_ocr to try to recognize the user input and match it to the prompted kana. The backend will return success or failure.
- The frontend will report the user's success or failure.

### Kana to romaji

- The frontend will ask "What type of kana do you want to practice?"
- The user will select either Hiragana or Katakana on the page using a radio button.
- The frontend will display a random kana from the selected dictonary in Japanese.
- The user will be asked to input the Romaji
- The submission will go to the backend to be checked that the Romaji matches the selected Kana using an API.
- The backend will return correct if the user entered the correct Romaji, or incorrect if not
- The frontend will display the results as a correct or incorrect attempt.