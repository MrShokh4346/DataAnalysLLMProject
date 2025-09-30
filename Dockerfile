# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Pull Llama3 model with retry logic
RUN for attempt in $(seq 1 3); do \
        ollama pull llama3 && break || { echo "Pull attempt $attempt failed, retrying..."; sleep 5; }; \
    done

# Create startup script
RUN echo '#!/bin/bash\n\
ollama serve &\n\
sleep 10\n\
curl --fail --silent --show-error http://localhost:11434 || { echo "Ollama server failed to start"; exit 1; }\n\
streamlit run bank_analyst_assistant.py --server.port=8501 --server.address=0.0.0.0' > start.sh \
    && chmod +x start.sh

# Expose port for Streamlit
EXPOSE 8501

# Run startup script
CMD ["./start.sh"]