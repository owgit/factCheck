#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define variables
CONDA_ENV_NAME="video_transcription_env"
BACKEND_DIR="video-upload-app"
FRONTEND_DIR="video-transcription-frontend"

# Create Conda environment
echo "Creating Conda environment: $CONDA_ENV_NAME"
conda create -n $CONDA_ENV_NAME python=3.11 -y

# Activate Conda environment
echo "Activating Conda environment"
source activate $CONDA_ENV_NAME

# Install Python dependencies
echo "Installing Python dependencies"
cd $BACKEND_DIR
pip install fastapi uvicorn python-multipart python-dotenv openai moviepy requests
pip install yt-dlp ffmpeg-python gunicorn

# Create requirements.txt
pip freeze > requirements.txt

# Setup frontend
echo "Setting up frontend"
cd ../$FRONTEND_DIR
npm install

# Install specific React dependencies
npm install axios framer-motion @heroicons/react dompurify

# Build frontend
echo "Building frontend"
npm run build

# Create necessary directories
echo "Creating necessary directories"
mkdir -p ../deploy/backend
mkdir -p ../deploy/frontend

# Copy backend files
echo "Copying backend files"
cp -r ../$BACKEND_DIR/* ../deploy/backend/

# Copy frontend build
echo "Copying frontend build"
cp -r build/* ../deploy/frontend/

# Ensure uploads directory exists
echo "Creating uploads directory"
mkdir -p ../deploy/uploads

# Create a .env file for backend
echo "Creating .env file for backend"
echo "OPENAI_API_KEY=your_openai_api_key_here" > ../deploy/backend/.env

echo "Installation and setup complete!"
echo "Next steps:"
echo "1. Add your OpenAI API key to /deploy/backend/.env"
echo "2. Review and adjust configurations"
echo "3. Set up Nginx or Apache"
echo "4. Configure SSL/TLS"
echo "5. Start your application"