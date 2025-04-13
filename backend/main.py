import os
import time
import uuid
import base64
import logging
from io import BytesIO
from typing import Optional, List, Dict, Any
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
from reportlab.pdfgen import canvas
import whisper
from pydub import AudioSegment
import firebase_admin
from firebase_admin import credentials, db
import torch
import torchaudio
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# AudioSegment.converter = r"C:\Users\zkauk\Downloads\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
# AudioSegment.ffprobe = r"C:\Users\zkauk\Downloads\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin\ffprobe.exe"


class FirebaseService:
    """Service for Firebase Realtime Database operations"""

    def __init__(self):
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase app with credentials"""
        try:
            FIREBASE_CRED_PATH = "pdf-audio-creds.json"
            DATABASE_URL = "https://follow-my-reading-31353-default-rtdb.firebaseio.com"

            if not firebase_admin._apps:
                cred = credentials.Certificate(FIREBASE_CRED_PATH)
                firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

            self.pdf_db_ref = db.reference("pdf_files")
        except Exception as e:
            logger.error(f"Firebase initialization failed: {str(e)}")
            raise

    def save_pdf_data(self, data: Dict, pdf_id: str) -> None:
        """Save PDF data to database"""
        try:
            self.pdf_db_ref.child(pdf_id).set(data)
        except Exception as e:
            logger.error(f"Failed to save PDF data: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save PDF data")

    def save_audio_data(self, pdf_id: str, audio_data: Dict) -> str:
        """Save audio data to database"""
        try:
            audio_id = str(uuid.uuid4())
            self.pdf_db_ref.child(pdf_id).child("audio_recordings").child(audio_id).set(audio_data)
            return audio_id
        except Exception as e:
            logger.error(f"Failed to save audio data: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save audio data")

    def get_pdf(self, pdf_id: str) -> Dict:
        """Retrieve PDF data from database"""
        try:
            data = self.pdf_db_ref.child(pdf_id).get()
            if not data:
                raise HTTPException(status_code=404, detail="PDF not found")
            return data
        except Exception as e:
            logger.error(f"Failed to get PDF data: {str(e)}")
            raise

class FileService:
    """Service for file processing operations"""

    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes"""
        try:
            text = ""
            with BytesIO(pdf_bytes) as pdf_stream:
                reader = PyPDF2.PdfReader(pdf_stream)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            return text.strip()
        except PyPDF2.errors.PdfReadError as e:
            logger.error(f"Invalid PDF file: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid PDF file format")
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail="PDF processing error")

    @staticmethod
    def convert_text_to_pdf(text: str) -> bytes:
        """Convert text to PDF bytes"""
        try:
            buffer = BytesIO()
            c = canvas.Canvas(buffer)
            lines = text.splitlines()
            y = 800
            for line in lines:
                c.drawString(50, y, line)
                y -= 15
                if y < 50:
                    c.showPage()
                    y = 800
            c.save()
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail="PDF generation error")

    @staticmethod
    def encode_to_base64(file_bytes: bytes) -> str:
        """Encode bytes to base64 string"""
        return base64.b64encode(file_bytes).decode("utf-8")

class AudioService:

    def __init__(self):
        try:
            # Загрузка процессора и модели Tarteel
            self.processor = AutoProcessor.from_pretrained("tarteel-ai/whisper-base-ar-quran")
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained("tarteel-ai/whisper-base-ar-quran")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
        except Exception as e:
            logger.error(f"Не удалось загрузить модель Tarteel: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка загрузки модели Tarteel")

    async def transcribe_audio(self, audio_bytes: bytes, filename: str) -> Dict:
        temp_audio_path = None
        wav_temp_audio_path = None

        try:
            temp_audio_path = f"temp_{uuid.uuid4().hex}_{filename}"
            with open(temp_audio_path, "wb") as f:
                f.write(audio_bytes)

            time.sleep(1)

            transcribe_path = temp_audio_path

            waveform, sample_rate = self.load_audio_with_pydub(transcribe_path)


            target_rate = 16000
            if sample_rate != target_rate:
                resample_transform = torchaudio.transforms.Resample(sample_rate, target_rate)
                waveform = resample_transform(waveform)
                sample_rate = target_rate


            waveform_np = waveform.numpy()


            input_features = self.processor(waveform_np, sampling_rate=sample_rate, return_tensors="pt").input_features
            input_features = input_features.to(self.device)


            predicted_ids = self.model.generate(input_features)
            predicted_ids = predicted_ids.to("cpu")
            transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)

            result = {
                "text": transcription[0],
                "segments": []
            }
            return result
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Audio processing error")
        finally:
            self._cleanup_temp_files(temp_audio_path, wav_temp_audio_path)

    @staticmethod
    def _convert_to_wav(input_path: str, output_path: str) -> None:
        try:
            audio = AudioSegment.from_file(input_path)
        except Exception as e:
            logger.error(f"Audio conversion failed (autodetect) : {e}")
            raise HTTPException(status_code=400, detail="Unsupported or corrupted audio format")

        audio.export(output_path, format="wav")

    @staticmethod
    def load_audio_with_pydub(input_path: str):
        audio = AudioSegment.from_file(input_path)
        samples = np.array(audio.get_array_of_samples())
        waveform = torch.from_numpy(samples.astype(np.float32))
        if audio.channels > 1:
            waveform = waveform.view(-1, audio.channels).mean(dim=1, keepdim=True)
        sample_rate = audio.frame_rate
        return waveform, sample_rate
    @staticmethod
    def _cleanup_temp_files(*file_paths) -> None:
        """Cleanup temporary files"""
        for path in file_paths:
            if path and os.path.exists(path):
                try:
                    time.sleep(1)
                    os.remove(path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {path}: {str(e)}")

class ValidationService:
    """Service for data validation"""

    @staticmethod
    def validate_text(text: str) -> List[str]:
        """Validate input text"""
        errors = []
        if not text.strip():
            errors.append("Text cannot be empty")
        return errors

    @staticmethod
    def check_semantic(corrected_text: str, reference_text: str) -> bool:
        """Check semantic similarity between texts"""
        return reference_text.strip().lower() in corrected_text.strip().lower()

# Initialize services
firebase_service = FirebaseService()
file_service = FileService()
audio_service = AudioService()
validation_service = ValidationService()



# FastAPI app setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload_pdf")
async def upload_pdf(
        file: Optional[UploadFile] = File(None),
        text: Optional[str] = Form(None),
        user_id: str = Form(...)
):
    """Endpoint for uploading PDF or text"""
    try:
        # Validate input
        if not file and not text:
            raise HTTPException(status_code=400, detail="No file or text provided")

        pdf_id = str(uuid.uuid4())

        # Process input
        if text:
            errors = validation_service.validate_text(text)
            pdf_bytes = file_service.convert_text_to_pdf(text)
            extracted_text = text
        else:
            file_bytes = await file.read()
            extracted_text = file_service.extract_text_from_pdf(file_bytes)
            errors = validation_service.validate_text(extracted_text)
            pdf_bytes = file_bytes

        # Prepare data
        data = {
            "pdf_file_base64": file_service.encode_to_base64(pdf_bytes),
            "text": extracted_text,
            "errors": errors,
            "user_id": user_id,
            "audio_recordings": {}
        }

        # Save to database
        firebase_service.save_pdf_data(data, pdf_id)
        return {"pdf_id": pdf_id, "errors": errors}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload PDF failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/pdfs")
def list_pdfs(
        page: int = 1,
        page_size: int = 10,
        user_id: Optional[str] = None,
        only_mine: bool = False
):
    """Endpoint for listing PDFs"""
    try:
        all_pdfs = firebase_service.pdf_db_ref.get() or {}
        items = []

        for pdf_id, data in all_pdfs.items():
            if only_mine and user_id and data.get("user_id") != user_id:
                continue
            data["pdf_id"] = pdf_id
            items.append(data)

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": items[start:end]
        }
    except Exception as e:
        logger.error(f"List PDFs failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve PDF list")

@app.post("/upload_audio/{pdf_id}")
async def upload_audio(
        pdf_id: str,
        audio: UploadFile = File(...),
        uploader_id: str = Form(...)
):
    """Endpoint for uploading audio"""
    try:
        # Validate PDF exists
        pdf_data = firebase_service.get_pdf(pdf_id)
        reference_text = pdf_data.get("text", "")

        # Process audio
        audio_bytes = await audio.read()
        print("Длина загруженного аудио:", len(audio_bytes))
        transcription = await audio_service.transcribe_audio(audio_bytes, audio.filename)

        # Prepare chunks
        chunks = []
        for segment in transcription["segments"]:
            for word in segment.get("words", []):
                chunks.append({
                    "text": word["word"],
                    "start": word["start"],
                    "end": word["end"]
                })

        # Process results
        recognized_text = transcription["text"]
        semantic_ok = validation_service.check_semantic(recognized_text, reference_text)

        # Prepare audio data
        audio_data = {
            "audio_file_base64": file_service.encode_to_base64(audio_bytes),
            "uploader_id": uploader_id,
            "recognized_text": recognized_text,
            "corrected_text": recognized_text,  # Placeholder for future correction
            "chunks": chunks,
            "semantic_ok": semantic_ok
        }

        # Save to database
        audio_id = firebase_service.save_audio_data(pdf_id, audio_data)
        return {"pdf_id": pdf_id, "audio_id": audio_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload audio failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/pdf_data/{pdf_id}")
def get_pdf_data(pdf_id: str):
    """Endpoint for retrieving PDF data"""
    try:
        data = firebase_service.get_pdf(pdf_id)
        data["pdf_id"] = pdf_id
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get PDF data failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve PDF data")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
