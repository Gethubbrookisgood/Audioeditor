FROM python:3.10-slim

# تثبيت الاعتماديات الأساسية و ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ وتثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود البوت
COPY . .

# تشغيل البوت
CMD ["python", "main.py"]
