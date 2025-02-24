import React from 'react';

interface KanaToRomajiProps {
    kanaType: 'Hiragana' | 'Katakana';
}

function KanaToRomaji({ kanaType }: KanaToRomajiProps) {
    return (
        <div>
            <h2>Kana to Romaji</h2>
            {/* Implement Kana to Romaji logic here */}
        </div>
    );
}

export default KanaToRomaji; 