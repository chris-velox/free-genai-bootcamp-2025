FROM python:3.11

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for better PyTorch CPU performance
ENV MKL_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    MKL_SERVICE_FORCE_INTEL=1

# Install core Python packages first
RUN pip install --no-cache-dir \
    Pillow==9.5.0 \
    numpy==1.24.3 \
    python-dotenv==1.0.1

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend-flask/ .

# Create directory for SQLite database
RUN mkdir -p instance

# Initialize database using standalone script
RUN python init_db.py

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"] 