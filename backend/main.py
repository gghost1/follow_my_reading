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

async def detect_text_from_audio(audio_bytes, audio):
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

@app.post("/upload_pdf")
async def upload_pdf(
        file: Optional[UploadFile] = File(None),
        text: Optional[str] = Form(None),
        user_id: str = Form(...)
):
    if not file and not text:
        raise HTTPException(status_code=400, detail="Не передан ни файл, ни текст.")

    pdf_id = str(uuid.uuid4())

    if text:
        data_from = create_data_from_text(text)
    else:
        file_bytes = await file.read()
        data_from = create_data_from_pdf(file_bytes)

    pdf_base64 = encode_file_to_base64(data_from["pdf_bytes"])

    data = {
        "pdf_file_base64": pdf_base64,
        "text": data_from["extracted_text"],
        "errors": data_from["errors"],
        "user_id": user_id,
        "audio_recordings": {}
    }

    save_pdf_data(data, pdf_id)
    return {"pdf_id": pdf_id, "errors": data_from["errors"]}

@app.get("/pdfs")
def list_pdfs(page: int = 1, page_size: int = 10, user_id: Optional[str] = None, only_mine: bool = False):
    all_pdfs = pdf_db_ref.get() or {}
    items = []
    for key, d in all_pdfs.items():
        d["pdf_id"] = key
        if only_mine and user_id:
            if d.get("user_id") == user_id:
                items.append(d)
        else:
            items.append(d)
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paged_items = items[start:end]
    return {"page": page, "page_size": page_size, "total": total, "items": paged_items}

@app.post("/upload_audio/{pdf_id}")
async def upload_audio(
        pdf_id: str,
        audio: UploadFile = File(...),
        uploader_id: str = Form(...)
):
    pdf_snapshot = pdf_db_ref.child(pdf_id).get()
    if not pdf_snapshot:
        raise HTTPException(status_code=404, detail="PDF не найден.")

    audio_bytes = await audio.read()
    result = await detect_text_from_audio(audio_bytes, audio)

    chunks = []
    for segment in result["segments"]:
        for word in segment["words"]:
            chunks.append({
                "text": word["word"],
                "start": word["start"],
                "end": word["end"]
            })

    recognized_text = result["text"]
    reference_text = pdf_snapshot.get("text", "")

    corrected_text = recognized_text #correct_text(recognized_text, reference_text)
    semantic_ok = check_semantic(corrected_text, reference_text)

    audio_base64 = encode_file_to_base64(audio_bytes)

    audio_recording = {
        "audio_file_base64": audio_base64,
        "uploader_id": uploader_id,
        "recognized_text": recognized_text,
        "corrected_text": corrected_text,
        "chunks": chunks,
        "semantic_ok": semantic_ok
    }

    audio_id = str(uuid.uuid4())
    pdf_db_ref.child(pdf_id).child("audio_recordings").child(audio_id).set(audio_recording)

    return {"pdf_id": pdf_id, "audio_recording": audio_recording}

@app.get("/pdf_data/{pdf_id}")
def get_pdf_data(pdf_id: str):
    data = pdf_db_ref.child(pdf_id).get()
    if not data:
        raise HTTPException(status_code=404, detail="PDF не найден.")
    data["pdf_id"] = pdf_id
    return data


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)