import React from 'react';

interface LearnKanaProps {
    kanaType: 'Hiragana' | 'Katakana';
}

function LearnKana({ kanaType }: LearnKanaProps) {
    const imageSource = kanaType === 'Hiragana' ? '/img/Hiragana.jpg' : '/img/Katakana.jpg';

    return (
        <div>
            <h2>Learn {kanaType}</h2>
            <img src={imageSource} alt={`${kanaType} Chart`} />
        </div>
    );
}

export default LearnKana; 