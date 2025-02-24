import { useState, useEffect, ChangeEvent, KeyboardEvent } from 'react';
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface KanaToRomajiProps {
    kanaType: 'Hiragana' | 'Katakana';
}

function KanaToRomaji({ kanaType }: KanaToRomajiProps) {
    const [currentKana, setCurrentKana] = useState<string>('');
    const [expectedRomaji, setExpectedRomaji] = useState<string>('');
    const [userInput, setUserInput] = useState<string>('');
    const [result, setResult] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedType, setSelectedType] = useState<'hiragana' | 'katakana'>(kanaType.toLowerCase() as 'hiragana' | 'katakana');

    const fetchRandomKana = async () => {
        try {
            setLoading(true);
            console.log('Fetching random kana for type:', selectedType);
            const response = await fetch(`http://localhost:5000/writing-practice/random-kana?type=${selectedType}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('Received kana data:', data);
            
            if (!data.kana || !data.romaji) {
                throw new Error('Invalid response format from server');
            }
            
            setCurrentKana(data.kana);
            setExpectedRomaji(data.romaji);
            setUserInput('');
            setResult(null);
        } catch (error) {
            console.error('Error fetching kana:', error);
            setCurrentKana('Error loading kana');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        console.log('KanaType changed to:', kanaType);
        setSelectedType(kanaType.toLowerCase() as 'hiragana' | 'katakana');
    }, [kanaType]);

    useEffect(() => {
        console.log('Selected type changed to:', selectedType);
        fetchRandomKana();
    }, [selectedType]);

    useEffect(() => {
        console.log('Current kana updated:', currentKana);
    }, [currentKana]);

    useEffect(() => {
        console.log('Expected romaji updated:', expectedRomaji);
    }, [expectedRomaji]);

    const handleSubmit = async () => {
        if (!userInput.trim()) return;
        
        try {
            // Compare user input with expected romaji
            const isCorrect = userInput.toLowerCase() === expectedRomaji.toLowerCase();
            setResult(isCorrect ? 'correct' : 'incorrect');

            // Wait a moment before fetching the next kana
            setTimeout(() => {
                fetchRandomKana();
            }, 1500);
        } catch (error) {
            console.error('Error submitting answer:', error);
        }
    };

    const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
        setUserInput(e.target.value);
    };

    const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            handleSubmit();
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col items-center space-y-4">
                {loading ? (
                    <div className="text-lg">Loading...</div>
                ) : (
                    <>
                        <div className="text-6xl font-bold mb-4">
                            {currentKana}
                        </div>
                        
                        <div className="w-full max-w-sm space-y-4">
                            <Input
                                type="text"
                                placeholder="Enter Romaji"
                                value={userInput}
                                onChange={handleInputChange}
                                onKeyPress={handleKeyPress}
                                autoFocus
                            />

                            <Button 
                                className="w-full"
                                onClick={handleSubmit}
                                disabled={!userInput.trim()}
                            >
                                Submit
                            </Button>

                            {result && (
                                <div className={`p-4 rounded-md text-center ${
                                    result === 'correct' 
                                        ? 'bg-green-100 text-green-700' 
                                        : 'bg-red-100 text-red-700'
                                }`}>
                                    {result === 'correct' 
                                        ? 'Correct!' 
                                        : `Incorrect. The correct answer was: ${expectedRomaji}`}
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}

export default KanaToRomaji; 