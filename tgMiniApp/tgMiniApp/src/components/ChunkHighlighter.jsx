import React, { useMemo } from 'react';

// Функция для токенизации текста с сохранением пробелов
const tokenize = (text) => {
    const tokens = [];
    const regex = /(\S+)(\s*)/g;
    let match;
    while ((match = regex.exec(text)) !== null) {
        tokens.push({
            word: match[1],
            space: match[2],
            normalized: match[1].toLowerCase().replace(/[.,!?;:()«»"“”]/g, ''),
        });
    }
    return tokens;
};

export default function ChunkHighlighter({ text, currentTime, chunks }) {
    // Токенизируем исходный текст
    const tokens = useMemo(() => tokenize(text), [text]);

    // Находим максимальное значение end среди всех чанков — это приблизительно конец аудио
    const maxEnd = useMemo(() => {
        if (!chunks || chunks.length === 0) return 0;
        return Math.max(...chunks.map((c) => c.end));
    }, [chunks]);

    // Массив для сопоставления каждого токена с временным интервалом чанка, если он найден
    const tokenChunks = useMemo(() => {
        let pointer = 0;
        const mapping = new Array(tokens.length).fill(null);
        if (!chunks || !chunks.length) return mapping;

        chunks.forEach((chunk) => {
            const chunkText = chunk.text.trim();
            const chunkTokens = chunkText
                .split(/\s+/)
                .map((w) => w.toLowerCase().replace(/[.,!?;:()«»"“”]/g, ''));

            // Ищем последовательное совпадение токенов начиная с pointer
            for (let i = pointer; i <= tokens.length - chunkTokens.length; i++) {
                let match = true;
                for (let j = 0; j < chunkTokens.length; j++) {
                    if (tokens[i + j].normalized !== chunkTokens[j]) {
                        match = false;
                        break;
                    }
                }
                if (match) {
                    // Присваиваем найденным токенам интервал чанка
                    for (let j = 0; j < chunkTokens.length; j++) {
                        mapping[i + j] = { start: chunk.start, end: chunk.end };
                    }
                    pointer = i + chunkTokens.length;
                    break;
                }
            }
        });
        return mapping;
    }, [tokens, chunks]);

    // Группируем токены в сегменты
    const segments = useMemo(() => {
        const segs = [];
        let i = 0;
        while (i < tokens.length) {
            // Если токен сопоставлен — группируем подряд идущие токены с одинаковым интервалом
            if (tokenChunks[i] !== null) {
                const mapping = tokenChunks[i];
                let segText = tokens[i].word + tokens[i].space;
                let j = i + 1;
                // Собираем подряд идущие токены с таким же интервалом
                while (
                    j < tokens.length &&
                    tokenChunks[j] !== null &&
                    tokenChunks[j].start === mapping.start &&
                    tokenChunks[j].end === mapping.end
                ) {
                    segText += tokens[j].word + tokens[j].space;
                    j++;
                }
                segs.push({
                    text: segText,
                    start: mapping.start,
                    end: mapping.end,
                    isMatched: true,
                });
                i = j;
            } else {
                // Несопоставленные токены
                let segText = tokens[i].word + tokens[i].space;
                // Определяем начало: ищем ближайший сопоставленный слева
                let prev = 0;
                let k = i - 1;
                while (k >= 0 && tokenChunks[k] === null) k--;
                if (k >= 0 && tokenChunks[k] !== null) {
                    prev = tokenChunks[k].end;
                }

                let j = i + 1;
                while (j < tokens.length && tokenChunks[j] === null) {
                    segText += tokens[j].word + tokens[j].space;
                    j++;
                }

                // Определяем конец: ищем ближайший сопоставленный справа
                let next = maxEnd;
                if (j < tokens.length && tokenChunks[j] !== null) {
                    next = tokenChunks[j].start;
                }

                segs.push({
                    text: segText,
                    start: prev,
                    end: next,
                    isMatched: false,
                });
                i = j;
            }
        }
        return segs;
    }, [tokens, tokenChunks, maxEnd]);

    return (
        <div style={{ lineHeight: '1.6em', marginTop: '10px' }}>
            {segments.map((seg, idx) => {
                let backgroundColor = 'transparent';
                // Подсветка только в интервале сегмента
                if (currentTime >= seg.start && currentTime <= seg.end) {
                    backgroundColor = seg.isMatched ? 'yellow' : 'red';
                }
                return (
                    <>
                        <span
                            key={idx}
                            style={{
                                background: backgroundColor,
                                transition: 'background 0.2s',
                            }}
                        >
                            {seg.text.replace(' ', '')}
                        </span>
                        <span>{` `}</span>
                    </>
                );
            })}
        </div>
    );
}
