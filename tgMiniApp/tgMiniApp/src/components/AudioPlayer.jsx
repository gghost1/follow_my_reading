import React, { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import ChunkHighlighter from './ChunkHighlighter';

export default function AudioPlayer({ base64, chunks, text }) {
    const containerRef = useRef(null);
    const waveRef = useRef(null);

    const [isReady, setIsReady] = useState(false);
    const [isInitialized, setIsInitialized] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [error, setError] = useState(null);

    // Конвертация base64 → Blob
    const base64ToBlob = (b64) => {
        const byteString = atob(b64);
        const arrayBuffer = new ArrayBuffer(byteString.length);
        const intArray = new Uint8Array(arrayBuffer);
        for (let i = 0; i < byteString.length; i++) {
            intArray[i] = byteString.charCodeAt(i);
        }
        return new Blob([intArray], { type: 'audio/ogg' });
    };

    const initWaveSurfer = () => {
        if (!containerRef.current || isInitialized) return;

        const wave = WaveSurfer.create({
            container: containerRef.current,
            waveColor: '#ccc',
            progressColor: '#535bf2',
            height: 80,
        });

        waveRef.current = wave;
        setIsInitialized(true);

        try {
            const blob = base64ToBlob(base64);
            const url = URL.createObjectURL(blob);
            wave.load(url);
        } catch (e) {
            console.error('Ошибка при создании Blob:', e);
            setError('Ошибка при декодировании аудио.');
        }

        wave.on('error', (e) => {
            console.error('WaveSurfer error:', e);
            setError('Ошибка воспроизведения: ' + e.toString());
        });

        wave.on('ready', () => {
            console.log('WaveSurfer готов');
            setIsReady(true);
        });

        wave.on('audioprocess', () => {
            setCurrentTime(wave.getCurrentTime());
        });
    };

    const handlePlayPause = () => {
        if (waveRef.current && isReady) {
            waveRef.current.playPause();
        }
    };

    useEffect(() => {
        return () => {
            if (waveRef.current) {
                waveRef.current.destroy();
                waveRef.current = null;
            }
        };
    }, []);
    

    return (
        <div style={{ marginBottom: '30px' }}>
            <div ref={containerRef} style={{width: '100%', height: '100px' }} />

            {!isInitialized && (
                <button onClick={initWaveSurfer} style={{ marginTop: '20px' }}>
                    Инициализировать аудиоплеер 
                </button>
            )}

            {error && <p style={{ color: 'red' }}>Ошибка: {error}</p>}

            <button onClick={handlePlayPause} disabled={!isReady} style={{ marginTop: '20px' }}>
                {isReady ? 'Play' : 'Загрузка...'}
            </button>

            
            <p style={{marginTop: '35px'}}>Синхронизированный текст:</p>
            <ChunkHighlighter text={text} currentTime={currentTime} chunks={chunks} />

            <hr />
        </div>
    );
}
