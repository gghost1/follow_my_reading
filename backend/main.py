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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Ссылка на корневой узел в Realtime Database для PDF-файлов
pdf_db_ref = db.reference("pdf_files")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)