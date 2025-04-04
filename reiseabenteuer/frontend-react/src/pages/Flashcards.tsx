import React, { useState, useEffect, useRef } from 'react';
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
  SelectChangeEvent,
  IconButton
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { ArrowBack, ArrowForward, Mic, Stop, Refresh as RefreshIcon } from '@mui/icons-material';
import { CircularProgress } from '@mui/material';

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

interface PronunciationResult {
  isCorrect: boolean;
  transcribedText: string;
  confidence: number;
}

interface FormattedWordState {
  text: string;
  associatedNoun?: VocabularyWord | null;
  pronunciationResult?: PronunciationResult;
  imagePath?: string;
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

const formatWordForDisplay = (
  word: VocabularyWord, 
  noun: VocabularyWord | null = null,
  hideWord: boolean = false
): string => {
  const getUnderscores = (word: string) => '_'.repeat(word.length);

  switch (word.part_of_speech) {
    case 'noun':
      return `${getArticleForGender(word.gender || '')} ${hideWord ? getUnderscores(word.german_word) : word.german_word}`;
    case 'verb':
      const pronoun = getRandomPronoun();
      const verbForm = word.present?.[pronoun as keyof typeof word.present] || word.german_word;
      return `${pronoun} ${hideWord ? getUnderscores(verbForm) : verbForm}`;
    case 'adjective': {
      if (!noun) return hideWord ? getUnderscores(word.german_word) : word.german_word;

      const usePlural = getRandomBoolean();
      const article = usePlural ? 'Die' : getArticleForGender(noun.gender || '');
      const nounForm = usePlural 
        ? noun.cases?.nominative?.plural || noun.german_word
        : noun.german_word;

      return `${article} ${hideWord ? getUnderscores(word.german_word) : word.german_word} ${nounForm}`;
    }
    default:
      return hideWord ? getUnderscores(word.german_word) : word.german_word;
  }
};

const getEnglishPartOfSpeech = (germanPos: string): string => {
  const posMap: { [key: string]: string } = {
    'noun': 'noun',
    'verb': 'verb',
    'adjective': 'adjective'
  };
  return posMap[germanPos] || germanPos;
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
  const [isRecording, setIsRecording] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [isRevealed, setIsRevealed] = useState(false);
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [isTranslationVisible, setIsTranslationVisible] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

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
    setIsRevealed(false);
    setIsTranslationVisible(false);
  };

  const handleNext = () => {
    setFlashcardState(prev => ({
      ...prev,
      currentIndex: Math.min(prev.words.length - 1, prev.currentIndex + 1)
    }));
    setShouldRefreshNoun(prev => !prev);
    setIsRevealed(false);
    setIsTranslationVisible(false);
  };

  const handleReveal = () => {
    setIsRevealed(prev => !prev);
  };

  const handleTranslationToggle = () => {
    setIsTranslationVisible(prev => !prev);
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

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000
        } 
      });

      // Check supported MIME types
      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4';

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: mimeType
      });
      
      const audioChunks: BlobPart[] = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        try {
          const audioBlob = new Blob(audioChunks, { type: mimeType });
          await checkPronunciation(audioBlob);
        } catch (error) {
          console.error('Error processing recording:', error);
          setFormattedWord(prev => ({
            ...prev,
            pronunciationResult: {
              isCorrect: false,
              transcribedText: 'Error processing audio. Please try again.',
              confidence: 0
            }
          }));
        } finally {
          stream.getTracks().forEach(track => track.stop());
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100); // Record in 100ms chunks
      setIsRecording(true);

      // Stop recording after 5 seconds
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop();
          setIsRecording(false);
        }
      }, 5000);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      setIsRecording(false);
      setFormattedWord(prev => ({
        ...prev,
        pronunciationResult: {
          isCorrect: false,
          transcribedText: 'Error accessing microphone. Please check permissions.',
          confidence: 0
        }
      }));
    }
  };

  const checkPronunciation = async (audioBlob: Blob) => {
    setIsChecking(true);
    try {
      const base64Audio = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          if (typeof reader.result === 'string') {
            const base64Data = reader.result.split(',')[1];
            resolve(base64Data);
          } else {
            reject(new Error('Failed to convert audio to base64'));
          }
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(audioBlob);
      });

      const fullPhrase = formatWordForDisplay(
        flashcardState.words[flashcardState.currentIndex],
        formattedWord.associatedNoun,
        false
      );

      const response = await fetch('http://localhost:8000/check_recording', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          audio_data: base64Audio,
          expected_text: fullPhrase
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to check pronunciation: ${response.statusText}`);
      }

      const result = await response.json();
      setFormattedWord(prev => ({
        ...prev,
        pronunciationResult: {
          isCorrect: result.is_correct,
          transcribedText: result.transcribed_text,
          confidence: result.confidence
        }
      }));
    } catch (error) {
      console.error('Error checking pronunciation:', error);
      setFormattedWord(prev => ({
        ...prev,
        pronunciationResult: {
          isCorrect: false,
          transcribedText: 'Error processing audio',
          confidence: 0
        }
      }));
    } finally {
      setIsChecking(false);
    }
  };

  const handleRegenerateImage = async () => {
    if (flashcardState.words.length === 0) return;

    const currentWord = flashcardState.words[flashcardState.currentIndex];
    setIsGeneratingImage(true);
    setFormattedWord(prev => ({
      ...prev,
      imagePath: undefined
    }));
    
    try {
      const englishPhrase = formatEnglishTranslation(currentWord, formattedWord.associatedNoun);
      const response = await fetch('http://localhost:8000/images/generate_image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phrase: englishPhrase,
          cefr_level: config.level,
          part_of_speech: getEnglishPartOfSpeech(currentWord.part_of_speech),
          force_regenerate: true
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to regenerate image');
      }

      const data = await response.json();
      const imagePath = data.image_path.startsWith('/') ? data.image_path : `/${data.image_path}`;
      
      setFormattedWord(prev => ({
        ...prev,
        imagePath: imagePath
      }));
    } catch (error) {
      console.error('Error regenerating image:', error);
    } finally {
      setIsGeneratingImage(false);
    }
  };

  const formatEnglishTranslation = (
    word: VocabularyWord,
    noun: VocabularyWord | null = null
  ): string => {
    switch (word.part_of_speech) {
      case 'noun':
        return `the ${word.english_word}`;
      case 'verb': {
        const pronoun = getRandomPronoun();
        const pronounMap: { [key: string]: string } = {
          'ich': 'I',
          'du': 'you',
          'er': 'he',
          'wir': 'we',
          'ihr': 'you all'
        };
        // Special handling for 'sie' - randomly choose between 'she' and 'they'
        if (pronoun === 'sie') {
          return `${Math.random() < 0.5 ? 'she' : 'they'} ${word.english_word}`;
        }
        return `${pronounMap[pronoun]} ${word.english_word}`;
      }
      case 'adjective': {
        if (!noun) return word.english_word;
        return `the ${word.english_word} ${noun.english_word}`;
      }
      default:
        return word.english_word;
    }
  };

  const isFormValid = config.level && config.partOfSpeech && config.cardCount > 0;

  // Update the effect to handle both pronunciation formatting and image generation
  useEffect(() => {
    const formatWord = async () => {
      if (flashcardState.words.length > 0) {
        const currentWord = flashcardState.words[flashcardState.currentIndex];
        
        let formattedPhrase: string;
        let associatedNoun: VocabularyWord | null = null;

        if (currentWord.part_of_speech === 'adjective') {
          associatedNoun = await fetchRandomNoun(config.level);
        }

        formattedPhrase = formatWordForDisplay(
          currentWord, 
          associatedNoun, 
          config.practiceMode === 'identification'
        );

        if (config.practiceMode === 'pronunciation') {
          setFormattedWord({ 
            text: formattedPhrase, 
            associatedNoun 
          });
        } else {
          setIsGeneratingImage(true);
          try {
            const englishPhrase = formatEnglishTranslation(currentWord, associatedNoun);
            const response = await fetch('http://localhost:8000/images/generate_image', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                phrase: englishPhrase,
                cefr_level: config.level,
                part_of_speech: getEnglishPartOfSpeech(currentWord.part_of_speech)
              }),
            });

            if (!response.ok) {
              throw new Error('Failed to generate image');
            }

            const data = await response.json();
            const imagePath = data.image_path.startsWith('/') ? data.image_path : `/${data.image_path}`;
            
            setFormattedWord({
              text: formattedPhrase,
              associatedNoun,
              imagePath: imagePath
            });
          } catch (error) {
            console.error('Error generating image:', error);
            setFormattedWord({
              text: formattedPhrase,
              associatedNoun,
              imagePath: undefined
            });
          } finally {
            setIsGeneratingImage(false);
          }
        }
      }
    };
    formatWord();
  }, [flashcardState.currentIndex, flashcardState.words, config.level, config.practiceMode, shouldRefreshNoun]);

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
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        {/* Main Content Area */}
        <Box sx={{ 
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          mb: 4
        }}>
          {/* Text display with reveal and translation buttons */}
          <Box sx={{ textAlign: 'center', mb: 2 }}>
            <Typography variant="h2" gutterBottom>
              {isRevealed 
                ? formatWordForDisplay(
                    words[currentIndex],
                    formattedWord.associatedNoun,
                    false
                  )
                : formattedWord.text
              }
            </Typography>
            {isTranslationVisible && (
              <Typography 
                variant="h4" 
                color="text.secondary"
                sx={{ mb: 2 }}
              >
                {formatEnglishTranslation(
                  words[currentIndex],
                  formattedWord.associatedNoun
                )}
              </Typography>
            )}
            <Stack 
              direction="row" 
              spacing={2} 
              justifyContent="center"
              sx={{ mt: 1 }}
            >
              <Button
                variant="outlined"
                onClick={handleReveal}
              >
                {isRevealed ? 'Hide' : 'Reveal'} Phrase
              </Button>
              <Button
                variant="outlined"
                onClick={handleTranslationToggle}
                color="secondary"
              >
                {isTranslationVisible ? 'Hide' : 'Show'} Translation
              </Button>
            </Stack>
          </Box>

          {/* Show image in identification mode */}
          {config.practiceMode === 'identification' && (
            <Box sx={{ 
              width: 300,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 2,
              mt: 2
            }}>
              <Box sx={{ 
                width: 300,
                height: 300,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative'
              }}>
                {formattedWord.imagePath ? (
                  <>
                    <Box
                      component="img"
                      src={`http://localhost:8000${formattedWord.imagePath}`}
                      alt="Word visualization"
                      sx={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'contain',
                        borderRadius: 2,
                        boxShadow: 3,
                        opacity: isGeneratingImage ? 0.3 : 1,
                        transition: 'opacity 0.3s'
                      }}
                    />
                    {isGeneratingImage && (
                      <CircularProgress
                        sx={{
                          position: 'absolute',
                          top: '50%',
                          left: '50%',
                          transform: 'translate(-50%, -50%)'
                        }}
                      />
                    )}
                  </>
                ) : (
                  <CircularProgress />
                )}
              </Box>
              <Button
                variant="outlined"
                onClick={handleRegenerateImage}
                startIcon={<RefreshIcon />}
                size="small"
                disabled={isGeneratingImage}
              >
                {isGeneratingImage ? 'Generating...' : 'Generate New Image'}
              </Button>
            </Box>
          )}
        </Box>

        {/* Recording Controls - now shown in both modes */}
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
          <IconButton
            onClick={startRecording}
            disabled={isRecording || isChecking}
            color={isRecording ? 'error' : 'primary'}
            size="large"
          >
            {isRecording ? <Stop /> : <Mic />}
          </IconButton>
        </Box>

        {/* Recording Status */}
        {isRecording && (
          <Typography align="center" color="primary" sx={{ mb: 2 }}>
            Recording...
          </Typography>
        )}

        {/* Checking Status */}
        {isChecking && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}

        {/* Pronunciation Results */}
        {formattedWord.pronunciationResult && (
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <Typography
              color={formattedWord.pronunciationResult.isCorrect ? 'success.main' : 'error.main'}
              variant="h6"
              gutterBottom
            >
              {formattedWord.pronunciationResult.isCorrect ? 'Correct!' : 'Try Again'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Heard: {formattedWord.pronunciationResult.transcribedText}
            </Typography>
          </Box>
        )}

        {/* Navigation Controls */}
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
      </Box>
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
          {flashcardState.words.length > 0 && (
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