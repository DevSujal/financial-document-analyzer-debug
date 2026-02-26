FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create data directory for uploads
RUN mkdir -p data

EXPOSE 8000

CMD ["python", "main.py"]
