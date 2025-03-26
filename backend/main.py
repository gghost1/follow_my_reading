import os
import uuid
import base64
from io import BytesIO
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware


import PyPDF2
from reportlab.pdfgen import canvas

import whisper
from pydub import AudioSegment

FIREBASE_CRED_PATH = "pdf-audio-creds.json"
DATABASE_URL = "https://pdf-audio-25e17-default-rtdb.firebaseio.com"

cred = credentials.Certificate(FIREBASE_CRED_PATH)
firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Firebase Realtime Database folder
pdf_db_ref = db.reference("pdf_files")

# Simple check if text is empty
def check_text_errors(text: str) -> List[str]:
    errors = []
    if not text.strip():
        errors.append("Текст пустой.")
    return errors


# Extract text from PDF
def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    text = ""
    pdf_stream = BytesIO(pdf_bytes)
    reader = PyPDF2.PdfReader(pdf_stream)
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

# Convert text to PDF
def convert_text_to_pdf_bytes(text: str) -> bytes:
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

# Encode file to base64
def encode_file_to_base64(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode("utf-8")

# Base semantic check (text and audio)
def check_semantic(corrected_text: str, reference_text: str) -> bool:
    return reference_text.strip().lower() in corrected_text.strip().lower()

def create_data_from_text(text):
    errors = check_text_errors(text)
    pdf_bytes = convert_text_to_pdf_bytes(text)
    extracted_text = text
    return {
        "errors": errors,
        "pdf_bytes": pdf_bytes,
        "extracted_text": extracted_text
    }

def create_data_from_pdf(file_bytes):
    pdf_bytes = file_bytes
    extracted_text = extract_text_from_pdf_bytes(file_bytes)
    errors = check_text_errors(extracted_text)
    return {
        "errors": errors,
        "pdf_bytes": pdf_bytes,
        "extracted_text": extracted_text
    }

def save_pdf_data(data, pdf_id):
    pdf_db_ref.child(pdf_id).set(data)

def save_audio_data(pdf_id, audio_recording):
    audio_id = str(uuid.uuid4())
    pdf_db_ref.child(pdf_id).child("audio_recordings").child(audio_id).set(audio_recording)

async def detect_text_from_audio(audio):
    audio_bytes = await audio.read()
    temp_audio_path = f"temp_{uuid.uuid4().hex}_{audio.filename}"
    with open(temp_audio_path, "wb") as f:
        f.write(audio_bytes)

    if audio.filename.lower().endswith(".ogg"):
        wav_temp_audio_path = temp_audio_path.replace(".ogg", ".wav")
        ogg_audio = AudioSegment.from_file(temp_audio_path, format="ogg")
        ogg_audio.export(wav_temp_audio_path, format="wav")
        transcribe_path = wav_temp_audio_path
    else:
        transcribe_path = temp_audio_path

    # Transcribe audio
    model = whisper.load_model("small", device="cpu", in_memory=False)
    result = model.transcribe(transcribe_path, word_timestamps=True, fp16=False)

    # Remove temporary audio file
    os.remove(temp_audio_path)
    if audio.filename.lower().endswith(".ogg"):
        os.remove(wav_temp_audio_path)

    return result

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)