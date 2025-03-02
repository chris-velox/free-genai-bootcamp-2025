from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LyricsSearchInput(BaseModel):
    """Input schema for LyricsSearchTool."""
    song_title: str = Field(..., description="Title of the German song to search for")

class LyricsSearchTool(BaseTool):
    name: str = "GERMAN LYRICS SEARCH"
    description: str = "Searches and retrieves lyrics for German songs using DuckDuckGo search"
    args_schema: Type[BaseModel] = LyricsSearchInput

    def _get_mock_lyrics(self, song_title: str) -> dict:
        """Fallback method for well-known songs."""
        if song_title.lower() == "rock me amadeus":
            return {
                "lyrics": """Er war ein Punker
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
Amadeus Amadeus - oh oh oh Amadeus""",
                "artist": "Falco",
                "year": "1985"
            }
        return None

    def _run(self, song_title: str) -> str:
        try:
            # First try mock lyrics for well-known songs
            mock_result = self._get_mock_lyrics(song_title)
            if mock_result:
                logger.info(f"Using mock lyrics for {song_title}")
                return f"""
Found lyrics for: {song_title}

Original German Lyrics:
----------------------
{mock_result['lyrics']}

Song Information:
----------------
Artist: {mock_result['artist']}
Year: {mock_result['year']}
Source: Mock Database
"""

            # Search for lyrics using DuckDuckGo
            search_query = f"{song_title} lyrics german songtext"
            logger.info(f"Searching DuckDuckGo for: {search_query}")
            
            with DDGS() as ddgs:
                search_results = list(ddgs.text(search_query, max_results=5))
            
            logger.info(f"Found {len(search_results)} search results")

            if not search_results:
                return f"No lyrics found for: {song_title}"

            # Try to find lyrics in the search results
            lyrics = ""
            artist = "Unknown"
            
            for i, result in enumerate(search_results):
                try:
                    url = result.get('link', '')
                    if not url:
                        logger.info(f"Result {i}: No URL found")
                        continue

                    logger.info(f"Processing result {i}: {url}")
                    
                    # Get the webpage content
                    response = requests.get(url, timeout=10, 
                                         headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove script, style, and other non-content elements
                    for element in soup(['script', 'style', 'meta', 'link', 'header', 'footer', 'nav']):
                        element.decompose()

                    # Try multiple approaches to find lyrics
                    lyrics_candidates = []
                    
                    # 1. Look for elements with lyrics-related classes
                    lyrics_candidates.extend(soup.find_all(['div', 'p', 'pre'], 
                        class_=lambda x: x and any(term in str(x).lower() 
                            for term in ['lyrics', 'text', 'songtext', 'letra'])))
                    
                    # 2. Look for elements with lyrics-related IDs
                    lyrics_candidates.extend(soup.find_all(['div', 'p', 'pre'], 
                        id=lambda x: x and any(term in str(x).lower() 
                            for term in ['lyrics', 'text', 'songtext', 'letra'])))
                    
                    # 3. Look for elements containing the song title
                    lyrics_candidates.extend(soup.find_all(['div', 'p', 'pre'], 
                        string=lambda x: x and song_title.lower() in str(x).lower()))

                    logger.info(f"Found {len(lyrics_candidates)} potential lyrics containers")

                    for element in lyrics_candidates:
                        text = element.get_text(strip=True, separator="\n")
                        # Basic validation of lyrics content
                        if len(text) > 100 and "\n" in text:  # Lyrics should be reasonably long and have line breaks
                            lyrics = text
                            break

                    if lyrics:
                        # Try to find artist information
                        artist_candidates = soup.find_all(['h1', 'h2', 'div', 'span'], 
                            class_=lambda x: x and any(term in str(x).lower() 
                                for term in ['artist', 'singer', 'author', 'interpret']))
                        
                        for artist_elem in artist_candidates:
                            artist_text = artist_elem.get_text(strip=True)
                            if artist_text and len(artist_text) < 100:  # Basic validation
                                artist = artist_text
                                break
                        
                        break  # Found valid lyrics, exit the search loop

                except Exception as e:
                    logger.error(f"Error processing result {i}: {str(e)}")
                    continue

            if not lyrics:
                return f"Could not extract lyrics for: {song_title}"

            # Format the output nicely
            output = f"""
Found lyrics for: {song_title}

Original German Lyrics:
----------------------
{lyrics}

Song Information:
----------------
Artist: {artist}
Source: DuckDuckGo Search
"""
            return output
            
        except Exception as e:
            logger.error(f"Error retrieving lyrics: {str(e)}")
            return f"Error retrieving lyrics: {str(e)}"

class VocabularyExtractorInput(BaseModel):
    """Input schema for VocabularyExtractorTool."""
    lyrics: str = Field(..., description="German lyrics to analyze")

class VocabularyExtractorTool(BaseTool):
    name: str = "German Vocabulary Extractor"
    description: str = "Extracts vocabulary words from German lyrics with meanings and context"
    args_schema: Type[BaseModel] = VocabularyExtractorInput

    def _run(self, lyrics: str) -> str:
        # Implementation would include NLP processing
        # This is a placeholder implementation
        return "List of extracted vocabulary words with meanings"

class SongGeneratorInput(BaseModel):
    """Input schema for SongGeneratorTool."""
    vocabulary: str = Field(..., description="Vocabulary words to incorporate")
    style: str = Field(default="modern", description="Style of the song to generate")

class SongGeneratorTool(BaseTool):
    name: str = "German Song Generator"
    description: str = "Generates new German song lyrics using provided vocabulary"
    args_schema: Type[BaseModel] = SongGeneratorInput

    def _run(self, vocabulary: str, style: str) -> str:
        # Implementation would include LLM-based generation
        # This is a placeholder implementation
        return "Generated German song lyrics"

class TranslatorInput(BaseModel):
    """Input schema for TranslatorTool."""
    text: str = Field(..., description="German text to translate to English")

class TranslatorTool(BaseTool):
    name: str = "German-English Translator"
    description: str = "Translates German text to English while preserving artistic meaning"
    args_schema: Type[BaseModel] = TranslatorInput

    def _run(self, text: str) -> str:
        # Implementation would include translation API calls
        # This is a placeholder implementation
        return "English translation of the text"