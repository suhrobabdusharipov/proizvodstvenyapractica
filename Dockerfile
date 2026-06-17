FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r backend/requirements.txt

WORKDIR /app/backend

EXPOSE 5000

CMD ["python", "main.py"]