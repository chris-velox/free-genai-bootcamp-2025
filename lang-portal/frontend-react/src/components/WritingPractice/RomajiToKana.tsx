import { useEffect, useRef, useState } from 'react'
import { Button } from "@/components/ui/button"

interface RomajiToKanaProps {
    kanaType: 'Hiragana' | 'Katakana'
}

interface KanaResponse {
    kana: string
    romaji: string
}

export default function RomajiToKana({ kanaType }: RomajiToKanaProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const [context, setContext] = useState<CanvasRenderingContext2D | null>(null)
    const [isDrawing, setIsDrawing] = useState(false)
    const [currentKana, setCurrentKana] = useState<KanaResponse | null>(null)
    const [result, setResult] = useState<'success' | 'failure' | null>(null)
    const [error, setError] = useState<string | null>(null)

    // Initialize canvas context
    useEffect(() => {
        if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d')
            if (ctx) {
                // Set white background
                ctx.fillStyle = 'white'
                ctx.fillRect(0, 0, canvasRef.current.width, canvasRef.current.height)
                
                // Set drawing style for better character recognition
                ctx.strokeStyle = 'black'
                ctx.lineWidth = 20  // Thicker lines
                ctx.lineCap = 'round'
                ctx.lineJoin = 'round'
                setContext(ctx)
            }
        }
    }, [])

    // Fetch random kana on mount and kanaType change
    useEffect(() => {
        fetchRandomKana()
    }, [kanaType])

    const fetchRandomKana = async () => {
        try {
            setError(null)
            const response = await fetch(`/api/writing-practice/random-kana?type=${kanaType.toLowerCase()}`)
            if (!response.ok) {
                throw new Error('Failed to fetch kana')
            }
            const data: KanaResponse = await response.json()
            console.log('Received kana data:', data) // Debug log
            setCurrentKana(data)
            setResult(null)
            clearCanvas()
        } catch (error) {
            console.error('Error fetching random kana:', error)
            setError(error instanceof Error ? error.message : 'Failed to fetch kana')
            setCurrentKana(null)
        }
    }

    const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
        if (!context) return
        setIsDrawing(true)
        const { offsetX, offsetY } = e.nativeEvent
        context.beginPath()
        context.moveTo(offsetX, offsetY)
    }

    const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
        if (!isDrawing || !context) return
        const { offsetX, offsetY } = e.nativeEvent
        context.lineTo(offsetX, offsetY)
        context.stroke()
    }

    const stopDrawing = () => {
        if (!context) return
        setIsDrawing(false)
        context.closePath()
    }

    const clearCanvas = () => {
        if (!context || !canvasRef.current) return
        // Clear with white background
        context.fillStyle = 'white'
        context.fillRect(0, 0, canvasRef.current.width, canvasRef.current.height)
        context.strokeStyle = 'black'
        setResult(null)
    }

    const submitDrawing = async () => {
        if (!canvasRef.current || !currentKana) return

        try {
            const imageData = canvasRef.current.toDataURL('image/png')
            
            const response = await fetch('/api/writing-practice/verify-kana', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: imageData,
                    expectedKana: currentKana.kana,
                    expectedRomaji: currentKana.romaji,
                    kanaType: kanaType.toLowerCase(),
                }),
            })

            if (!response.ok) {
                throw new Error('Failed to verify kana')
            }

            const data = await response.json()
            setResult(data.success ? 'success' : 'failure')
        } catch (error) {
            console.error('Error submitting drawing:', error)
            setError(error instanceof Error ? error.message : 'Failed to verify kana')
        }
    }

    return (
        <div className="space-y-6">
            <div className="text-center">
                <h2 className="text-xl font-semibold mb-4">Draw the {kanaType} character for:</h2>
                {error ? (
                    <p className="text-red-500">{error}</p>
                ) : currentKana ? (
                    <p className="text-3xl font-bold mb-4">{currentKana.romaji}</p>
                ) : (
                    <p className="text-lg text-gray-500">Loading...</p>
                )}
            </div>

            <div className="flex justify-center">
                <canvas
                    ref={canvasRef}
                    width={300}
                    height={300}
                    className="border border-gray-300 rounded-lg bg-white"
                    onMouseDown={startDrawing}
                    onMouseMove={draw}
                    onMouseUp={stopDrawing}
                    onMouseLeave={stopDrawing}
                />
            </div>

            <div className="flex justify-center space-x-4">
                <Button onClick={clearCanvas} variant="outline">
                    Clear
                </Button>
                <Button 
                    onClick={submitDrawing}
                    disabled={!currentKana}
                >
                    Submit
                </Button>
                <Button 
                    onClick={fetchRandomKana} 
                    variant="outline"
                    disabled={!currentKana}
                >
                    Next
                </Button>
            </div>

            {result && (
                <div className={`text-center text-lg font-semibold ${result === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                    {result === 'success' ? 'Correct!' : 'Incorrect, try again!'}
                </div>
            )}
        </div>
    )
} 