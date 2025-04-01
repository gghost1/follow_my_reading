# Follow my reading

## Description
This service processes PDF and audio files. It allows:
- Uploading PDFs or text to be converted into PDFs.
- Extracting text from PDFs.
- Transcribing audio files using the Whisper model and splitting them into segments.
- Storing PDF and audio data in Firebase Realtime Database.

## Requirements
- Linux server with Docker and Docker Compose installed.
- LLM may use a lot of memory and CPU resources. (small model ~ 3GB RAM, large model ~ 6GB RAM)
- Firebase credentials file (e.g., `pdf-audio-creds.json`) located in the project root.
- Environment variables for:
    - `DATABASE_URL` – Firebase Realtime Database URL.
    - `FIREBASE_CRED_PATH` – Path to the Firebase credentials file.

## Setup and Run Using Docker on Linux

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gghost1/follow_my_reading.git
   cd follow_my_reading
   ```
2. **Place the Firebase credentials file in the project root.** Ensure the file name matches the one specified in [docker-compose.yml](docker-compose.yml).
3. **Build and run the Docker containers:**
   ```bash
   docker-compose up --build -d
   ```
4. **Service will be available at http://<your ip>:8000**
5. **Stop the containers:**
   ```bash
   docker-compose down
   ```
   
## API usage

### PDF/text upload
```bash
curl -X POST "http://localhost:8000/upload_pdf" \
  -H "Content-Type: multipart/form-data" \
  -F "user_id=user123" \
  -F "text=Пример текста для конвертации"
```

### Audio upload
```bash
curl -X POST "http://localhost:8000/upload_audio/pdf_id" \
  -H "Content-Type: multipart/form-data" \
  -F "audio=@recording.ogg" \
  -F "uploader_id=user456"
```

### Get all PDFs
```bash
curl "http://localhost:8000/pdfs?page=1&page_size=10&only_mine=true&user_id=user123"
```
