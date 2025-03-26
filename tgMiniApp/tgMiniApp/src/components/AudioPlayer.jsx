import React, { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import ChunkHighlighter from './ChunkHighlighter';

export default function AudioPlayer({ base64, chunks, text }) {
    const containerRef = useRef(null);
    const waveRef = useRef(null);
    const [isReady, setIsReady] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);

    // Преобразование base64 → blob
    const base64ToBlob = (b64) => {
        const byteString = atob(b64);
        const arrayBuffer = new ArrayBuffer(byteString.length);
        const intArray = new Uint8Array(arrayBuffer);
        for (let i = 0; i < byteString.length; i++) {
            intArray[i] = byteString.charCodeAt(i);
        }
        return new Blob([intArray], { type: 'audio/ogg' });
    };

    useEffect(() => {
        if (!containerRef.current) return;

        const blob = base64ToBlob(base64);
        const url = URL.createObjectURL(blob);

        const wave = WaveSurfer.create({
            container: containerRef.current,
            waveColor: '#ccc',
            progressColor: '#007aff',
            height: 80,
        });

        waveRef.current = wave;

        wave.load(url);

        wave.on('ready', () => {
            setIsReady(true);
        });

        wave.on('audioprocess', () => {
            setCurrentTime(wave.getCurrentTime());
        });

        return () => {
            wave.destroy();
            waveRef.current = null;
        };
    }, [base64]);

    const handlePlayPause = () => {
        if (waveRef.current && isReady) {
            waveRef.current.playPause();
        }
    };

    return (
        <div style={{ marginBottom: '30px' }}>
            <div ref={containerRef} style={{ width: '100%', height: '100px' }} />
            <button onClick={handlePlayPause} disabled={!isReady} style={{ marginTop: '20px' }}>
                ▶️ {isReady ? 'Play/Pause' : 'Loading...'}
            </button>
            <hr />
            <p>🧠 Синхронизированный текст:</p>
            <ChunkHighlighter text={text} currentTime={currentTime} chunks={chunks} />
        </div>
    );
}
