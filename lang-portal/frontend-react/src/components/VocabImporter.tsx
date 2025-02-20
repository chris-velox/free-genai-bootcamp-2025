import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2 } from "lucide-react";

interface Word {
  kanji: string;
  romaji: string;
  english: string;
  parts: { kanji: string; romaji: string; }[];
}

export default function VocabImporter() {
  const [wordCategory, setWordCategory] = useState("");
  const [words, setWords] = useState<Word[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGetWords = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/get_new_words", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ word_category: wordCategory }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      setWords(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!words) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/import_words", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ words }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      setWords(null);
      setWordCategory("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setWords(null);
    setWordCategory("");
    setError(null);
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Import Word Group</h2>
      
      <div className="space-y-4">
        <Input
          placeholder="Word Category"
          value={wordCategory}
          onChange={(e) => setWordCategory(e.target.value)}
          disabled={loading || words !== null}
        />
        
        {!words && (
          <Button 
            onClick={handleGetWords}
            disabled={!wordCategory || loading}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              'Get Words'
            )}
          </Button>
        )}
      </div>

      {error && (
        <p className="text-red-500">
          Error: {error}
        </p>
      )}

      {words && (
        <div className="p-4 border rounded-lg bg-card shadow-sm space-y-4">
          <h3 className="text-xl font-semibold">
            Generated Words:
          </h3>
          <pre className="bg-muted p-4 rounded-lg">
            {JSON.stringify(words, null, 2)}
          </pre>
          
          <div className="space-x-2">
            <Button 
              onClick={handleImport} 
              disabled={loading}
            >
              Import
            </Button>
            <Button 
              variant="outline"
              onClick={handleCancel}
              disabled={loading}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
} 