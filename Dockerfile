# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port for Streamlit
EXPOSE 8501

# Run database init and Streamlit
CMD ["sh", "-c", "python bank_analyst_assistant.py && streamlit run bank_analyst_assistant.py --server.port=8501 --server.address=0.0.0.0"]