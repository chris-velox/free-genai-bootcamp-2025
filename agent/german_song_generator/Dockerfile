FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/
COPY knowledge/ ./knowledge/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Set environment variables
ENV MODEL=groq/gemma2-9b-it
ENV GROQ_API_KEY=""

# Set the default command
CMD ["german_song_generator"] 