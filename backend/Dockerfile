# Используем официальный образ Python
FROM python:3.10

# Отключаем запись байткода и включаем вывод в поток (не буферизуемый вывод)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app


# Копируем файлы проекта
COPY . /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --default-timeout=600 --no-cache-dir -r requirements.txt --index-url https://pypi.org/simple/



RUN apt-get update && \
    apt-get install -y wget xz-utils && \
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar -xf ffmpeg-release-amd64-static.tar.xz && \
    cp ffmpeg-*-static/ffmpeg ffmpeg-*-static/ffprobe /usr/local/bin/ && \
    rm -rf ffmpeg*


# Копируем оставшийся исходный код в контейнер
COPY . .

# Открываем порт для FastAPI
EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
