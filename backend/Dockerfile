FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    libcurl4-openssl-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /backend

COPY requirements.txt /backend/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /backend/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
