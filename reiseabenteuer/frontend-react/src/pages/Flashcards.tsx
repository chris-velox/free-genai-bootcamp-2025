import React, { useState } from 'react';
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

interface FlashcardConfig {
  promptLanguage: 'english' | 'german';
  cardCount: number;
  level: string;
  partOfSpeech: string;
  practiceMode: 'identification' | 'pronunciation';
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

const Flashcards = () => {
  const theme = useTheme();
  const [config, setConfig] = useState<FlashcardConfig>(defaultConfig);

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

  const handleSubmit = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/vocabulary/words?cefr_level=${config.level.toUpperCase()}&part_of_speech=${config.partOfSpeech}&limit=${config.cardCount}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch vocabulary words');
      }
      
      const data = await response.json();
      console.log('Fetched vocabulary:', data);
      // TODO: Handle the fetched vocabulary data
      
    } catch (error) {
      console.error('Error fetching vocabulary:', error);
      // TODO: Show error message to user
    }
  };

  const isFormValid = config.level && config.partOfSpeech && config.cardCount > 0;

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        {currentLabels.title}
      </Typography>
      
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
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
    </Box>
  );
};

export default Flashcards; 