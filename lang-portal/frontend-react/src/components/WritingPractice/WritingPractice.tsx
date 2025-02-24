import { useState } from 'react'
import { Button } from "@/components/ui/button"
import LearnKana from './LearnKana'
import RomajiToKana from './RomajiToKana'

type KanaType = 'Hiragana' | 'Katakana'
type PracticeMode = 'learn' | 'practice' | 'test'

export default function WritingPractice() {
  const [kanaType, setKanaType] = useState<KanaType>('Hiragana')
  const [mode, setMode] = useState<PracticeMode>('learn')

  return (
    <div className="space-y-6">
      <div className="flex flex-col space-y-4">
        <h1 className="text-2xl font-bold">Japanese Writing Practice</h1>
        
        {/* Kana Type Selection */}
        <div className="flex space-x-4">
          <Button 
            variant={kanaType === 'Hiragana' ? 'default' : 'outline'}
            onClick={() => setKanaType('Hiragana')}
          >
            Hiragana
          </Button>
          <Button
            variant={kanaType === 'Katakana' ? 'default' : 'outline'}
            onClick={() => setKanaType('Katakana')}
          >
            Katakana
          </Button>
        </div>

        {/* Mode Selection */}
        <div className="flex space-x-4">
          <Button
            variant={mode === 'learn' ? 'default' : 'outline'}
            onClick={() => setMode('learn')}
          >
            Learn
          </Button>
          <Button
            variant={mode === 'practice' ? 'default' : 'outline'}
            onClick={() => setMode('practice')}
          >
            Practice
          </Button>
          <Button
            variant={mode === 'test' ? 'default' : 'outline'}
            onClick={() => setMode('test')}
          >
            Test
          </Button>
        </div>
      </div>

      {/* Content Area */}
      <div className="mt-6 p-4 border rounded-lg">
        {mode === 'learn' && <LearnKana kanaType={kanaType} />}
        {mode === 'practice' && <RomajiToKana kanaType={kanaType} />}
        {mode === 'test' && (
          <div>
            <h2 className="text-xl font-semibold">Test Mode</h2>
            <p>Test mode coming soon...</p>
          </div>
        )}
      </div>
    </div>
  )
} 