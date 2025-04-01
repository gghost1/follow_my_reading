import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

import { fetchPdfData } from '../api';
import AudioPlayer from '../components/AudioPlayer';
import Loading from '../components/Loading';

export default function TextDetail() {
    const { id: pdfId } = useParams();
    const [data, setData] = useState(null);

    useEffect(() => {
        if (!pdfId) return;
        fetchPdfData(pdfId).then(setData);
    }, [pdfId]);

    if (!data) return <Loading />;

    const recordings = Object.values(data.audio_recordings || {});

    return (
        <div style={{ padding: '20px' }}>
            <h2>📄   Оригинальный текст</h2>
            <p className='origText'>{data.text}</p>

            <h3 id='audios__title'>{`🎧 Озвучки`}</h3>
            {recordings.length === 0 ? (
                <p>Нет доступных аудио.</p>
            ) : (
                recordings.map((rec, i) => (
                    <AudioPlayer
                        key={i}
                        base64={rec.audio_file_base64}
                        chunks={rec.chunks}
                        text={data.text}
                    />
                ))
            )}
        </div>
    );
}
