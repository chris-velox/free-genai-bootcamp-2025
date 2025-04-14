# German Sentence Constructor Prompts

This directory contains prompt engineering experiments for creating German language learning assistants using various Large Language Models (LLMs). The prompts are designed to create an interactive German language teacher that helps students construct and translate sentences from English to German.

## Directory Structure

- `claude/` - Prompts optimized for Anthropic's Claude models
- `meta-ai/` - Prompts designed for Meta's LLMs, including:
  - `prompt.md` - Basic teaching prompt
  - `structural-prompt.md` - Enhanced structural guidance prompt
- `microsoft-copilot/` - Prompts tailored for Microsoft's Copilot

## Teaching Methodology

The prompts follow a specific teaching methodology:

1. The AI takes on the role of a German language teacher
2. Students provide sentences in English for translation
3. The AI avoids giving immediate answers, instead:
   - Provides vocabulary hints
   - Asks guiding questions
   - Suggests better word choices
   - Explains grammar rules when relevant
4. Once the student provides the correct translation, the AI:
   - Confirms the answer
   - Breaks down why it's correct
   - Explains any relevant grammar rules or patterns
   - Offers to continue with another sentence

## Example Interaction

```
Student: "Where is the train station?"
AI: Let's work on translating this. Remember that in German:
- "where" is "wo"
- "is" is "ist"
- "train station" is "Bahnhof" (note: nouns are capitalized)
- You'll need the correct article (der/die/das)

Student: "Wo ist der Bahnhof?"
AI: Perfect! [Explains why it's correct and breaks down the grammar]
```

## Usage

Each prompt file contains:
1. The initial system prompt that sets up the AI's role
2. Example interactions demonstrating the expected behavior
3. Key teaching principles and methodologies

Choose the appropriate prompt file based on your target LLM platform. 