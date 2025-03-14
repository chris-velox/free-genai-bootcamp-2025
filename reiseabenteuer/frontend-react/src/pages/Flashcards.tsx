import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Paper,
  Stack,
  SelectChangeEvent
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { ArrowBack, ArrowForward } from '@mui/icons-material';
import { IconButton } from '@mui/material';

interface FlashcardConfig {
  promptLanguage: 'english' | 'german';
  cardCount: number;
  level: string;
  partOfSpeech: string;
  practiceMode: 'identification' | 'pronunciation';
}

interface VocabularyWord {
  german_word: string;
  english_word: string;
  part_of_speech: string;
  gender?: string;
  present?: {
    ich?: string;
    du?: string;
    er?: string;
    wir?: string;
    ihr?: string;
    sie?: string;
  };
  cases?: {
    nominative?: {
      singular?: string;
      plural?: string;
    };
  };
}

interface FlashcardState {
  words: VocabularyWord[];
  currentIndex: number;
  isLoading: boolean;
  error: string | null;
}

interface FormattedWordState {
  text: string;
  associatedNoun?: VocabularyWord | null;
}

const defaultConfig: FlashcardConfig = {
  promptLanguage: 'german',
  cardCount: 10,
  level: '',
  partOfSpeech: '',
  practiceMode: 'identification'
};

const labels = {
  english: {
    title: 'Flashcards',
    cardCount: 'Number of Flashcards',
    level: 'CEFR Level',
    partOfSpeech: 'Part of Speech',
    reset: 'Reset',
    start: 'Start',
    nouns: 'Nouns (Nomen)',
    verbs: 'Verbs (Verben)',
    adjectives: 'Adjectives (Adjektive)',
    promptDirection: 'German → English',
    practiceMode: 'Practice Mode',
    identification: 'Word Identification',
    pronunciation: 'Pronunciation Practice'
  },
  german: {
    title: 'Karteikarten',
    cardCount: 'Anzahl der Karteikarten',
    level: 'CEFR-Stufe',
    partOfSpeech: 'Wortart',
    reset: 'Zurücksetzen',
    start: 'Beginnen',
    nouns: 'Nomen',
    verbs: 'Verben',
    adjectives: 'Adjektive',
    promptDirection: 'Deutsch → Englisch',
    practiceMode: 'Übungsmodus',
    identification: 'Wortidentifikation',
    pronunciation: 'Ausspracheübung'
  }
};

const getArticleForGender = (gender: string): string => {
  switch (gender?.toLowerCase()) {
    case 'm': return 'Der';
    case 'f': return 'Die';
    case 'n': return 'Das';
    default: return '';
  }
};

const getRandomPronoun = (): string => {
  const pronouns = ['ich', 'du', 'er', 'wir', 'ihr', 'sie'];
  return pronouns[Math.floor(Math.random() * pronouns.length)];
};

const getRandomBoolean = (): boolean => Math.random() < 0.5;

const fetchRandomNoun = async (level: string): Promise<VocabularyWord | null> => {
  try {
    const response = await fetch(
      `http://localhost:8000/vocabulary/words?cefr_level=${level}&part_of_speech=noun&limit=1`
    );
    
    if (!response.ok) {
      return null;
    }
    
    const data = await response.json();
    return data.vocabulary_words[0] || null;
  } catch (error) {
    console.error('Error fetching random noun:', error);
    return null;
  }
};

const formatWordForPronunciation = (
  word: VocabularyWord, 
  noun: VocabularyWord | null = null
): string => {
  switch (word.part_of_speech) {
    case 'noun':
      return `${getArticleForGender(word.gender || '')} ${word.german_word}`;
    case 'verb':
      const pronoun = getRandomPronoun();
      return `${pronoun} ${word.present?.[pronoun as keyof typeof word.present] || word.german_word}`;
    case 'adjective': {
      if (!noun) return word.german_word;

      const usePlural = getRandomBoolean();
      const article = usePlural ? 'Die' : getArticleForGender(noun.gender || '');
      const nounForm = usePlural 
        ? noun.cases?.nominative?.plural || noun.german_word
        : noun.german_word;

      return `${article} ${word.german_word} ${nounForm}`;
    }
    default:
      return word.german_word;
  }
};

const Flashcards = () => {
  const theme = useTheme();
  const [config, setConfig] = useState<FlashcardConfig>(defaultConfig);
  const [flashcardState, setFlashcardState] = useState<FlashcardState>({
    words: [],
    currentIndex: 0,
    isLoading: false,
    error: null
  });
  const [formattedWord, setFormattedWord] = useState<FormattedWordState>({ text: '' });
  const [shouldRefreshNoun, setShouldRefreshNoun] = useState<boolean>(false);

  const levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
  const partsOfSpeech = [
    { value: 'noun', labelKey: 'nouns' },
    { value: 'verb', labelKey: 'verbs' },
    { value: 'adjective', labelKey: 'adjectives' }
  ];

  // Get current language labels
  const currentLabels = config.promptLanguage === 'german' ? labels.german : labels.english;

  const handleLanguageToggle = () => {
    setConfig(prev => ({
      ...prev,
      promptLanguage: prev.promptLanguage === 'german' ? 'english' : 'german'
    }));
  };

  const handleCardCountChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = Math.max(1, Math.min(50, Number(event.target.value)));
    setConfig(prev => ({ ...prev, cardCount: value }));
  };

  const handleLevelChange = (event: SelectChangeEvent) => {
    setConfig(prev => ({ ...prev, level: event.target.value }));
  };

  const handlePartOfSpeechChange = (event: SelectChangeEvent) => {
    setConfig(prev => ({ ...prev, partOfSpeech: event.target.value }));
  };

  const handlePracticeModeChange = () => {
    setConfig(prev => ({
      ...prev,
      practiceMode: prev.practiceMode === 'identification' ? 'pronunciation' : 'identification'
    }));
  };

  const handleReset = () => {
    setConfig(defaultConfig);
  };

  const handlePrevious = () => {
    setFlashcardState(prev => ({
      ...prev,
      currentIndex: Math.max(0, prev.currentIndex - 1)
    }));
    setShouldRefreshNoun(prev => !prev);
  };

  const handleNext = () => {
    setFlashcardState(prev => ({
      ...prev,
      currentIndex: Math.min(prev.words.length - 1, prev.currentIndex + 1)
    }));
    setShouldRefreshNoun(prev => !prev);
  };

  const handleSubmit = async () => {
    setFlashcardState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const response = await fetch(
        `http://localhost:8000/vocabulary/words?cefr_level=${config.level.toUpperCase()}&part_of_speech=${config.partOfSpeech}&limit=${config.cardCount}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch vocabulary words');
      }
      
      const data = await response.json();
      setFlashcardState({
        words: data.vocabulary_words,
        currentIndex: 0,
        isLoading: false,
        error: null
      });
      
    } catch (error) {
      setFlashcardState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'An error occurred'
      }));
    }
  };

  const isFormValid = config.level && config.partOfSpeech && config.cardCount > 0;

  // Update the effect to handle noun fetching
  useEffect(() => {
    const formatWord = async () => {
      if (flashcardState.words.length > 0) {
        const currentWord = flashcardState.words[flashcardState.currentIndex];
        
        // For adjectives, fetch a new random noun each time
        if (currentWord.part_of_speech === 'adjective') {
          const noun = await fetchRandomNoun(config.level);
          const formatted = formatWordForPronunciation(currentWord, noun);
          setFormattedWord({ text: formatted, associatedNoun: noun });
        } else {
          const formatted = formatWordForPronunciation(currentWord);
          setFormattedWord({ text: formatted });
        }
      }
    };
    formatWord();
  }, [flashcardState.currentIndex, flashcardState.words, config.level, shouldRefreshNoun]);

  const renderFlashcard = () => {
    const { words, currentIndex, isLoading, error } = flashcardState;

    if (isLoading) {
      return (
        <Box sx={{ textAlign: 'center' }}>
          <Typography>Loading...</Typography>
        </Box>
      );
    }

    if (error) {
      return (
        <Box sx={{ textAlign: 'center' }}>
          <Typography color="error">{error}</Typography>
        </Box>
      );
    }

    if (words.length === 0) {
      return null;
    }

    return (
      <>
        <Typography variant="h2" gutterBottom align="center" sx={{ mb: 4 }}>
          {formattedWord.text}
        </Typography>
        
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          gap: 2, 
          mt: 'auto'
        }}>
          <IconButton 
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            size="large"
          >
            <ArrowBack />
          </IconButton>
          <Typography variant="body1" sx={{ alignSelf: 'center' }}>
            {currentIndex + 1} / {words.length}
          </Typography>
          <IconButton 
            onClick={handleNext}
            disabled={currentIndex === words.length - 1}
            size="large"
          >
            <ArrowForward />
          </IconButton>
        </Box>
      </>
    );
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        {currentLabels.title}
      </Typography>
      
      <Box sx={{ display: 'flex', gap: 3, alignItems: 'flex-start' }}>
        {/* Configuration Panel - Left Side */}
        <Paper elevation={3} sx={{ p: 3, flex: '0 0 400px' }}>
          <Stack spacing={3}>
            {/* Language Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={config.promptLanguage === 'german'}
                  onChange={handleLanguageToggle}
                  color="primary"
                />
              }
              label={currentLabels.promptDirection}
            />

            {/* Practice Mode Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={config.practiceMode === 'pronunciation'}
                  onChange={handlePracticeModeChange}
                  color="secondary"
                />
              }
              label={
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography>
                    {currentLabels.identification}
                  </Typography>
                  <Typography color="text.secondary">|</Typography>
                  <Typography>
                    {currentLabels.pronunciation}
                  </Typography>
                </Stack>
              }
            />

            {/* Card Count */}
            <TextField
              label={currentLabels.cardCount}
              type="number"
              value={config.cardCount}
              onChange={handleCardCountChange}
              inputProps={{ min: 1, max: 50 }}
              fullWidth
            />

            {/* Language Level */}
            <FormControl fullWidth>
              <InputLabel>{currentLabels.level}</InputLabel>
              <Select
                value={config.level}
                label={currentLabels.level}
                onChange={handleLevelChange}
              >
                {levels.map(level => (
                  <MenuItem key={level} value={level}>
                    {level}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Part of Speech */}
            <FormControl fullWidth>
              <InputLabel>{currentLabels.partOfSpeech}</InputLabel>
              <Select
                value={config.partOfSpeech}
                label={currentLabels.partOfSpeech}
                onChange={handlePartOfSpeechChange}
              >
                {partsOfSpeech.map(pos => (
                  <MenuItem key={pos.value} value={pos.value}>
                    {currentLabels[pos.labelKey as keyof typeof currentLabels]}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                onClick={handleReset}
                sx={{ minWidth: 100 }}
              >
                {currentLabels.reset}
              </Button>
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={!isFormValid}
                sx={{ minWidth: 100 }}
              >
                {currentLabels.start}
              </Button>
            </Box>
          </Stack>
        </Paper>

        {/* Flashcard Display - Right Side */}
        <Box sx={{ flex: 1 }}>
          {flashcardState.words.length > 0 && config.practiceMode === 'pronunciation' && (
            <Paper elevation={3} sx={{ 
              p: 3, 
              minHeight: '400px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center'
            }}>
              {renderFlashcard()}
            </Paper>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default Flashcards; 