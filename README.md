# Fact Check

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-green)](https://openai.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)](https://www.docker.com/)

A video fact-checking application that automatically transcribes and verifies factual claims in uploaded videos using OpenAI's advanced AI models.

## Features

- 🎬 **Video Upload**: Support for various video formats (mp4, mov, avi)
- 🔊 **Automatic Transcription**: Convert speech to text using OpenAI's Whisper model
- ✅ **AI Fact Checking**: Verify claims using OpenAI's GPT-4o
- 🔍 **Image Analysis**: Extract and analyze visual content from videos
- 📱 **Responsive UI**: User-friendly interface for uploading and reviewing results
- 📊 **Detailed Reports**: Get comprehensive fact-check reports with sources

## Tech Stack

### Backend
- Python with FastAPI
- OpenAI API integration
- MoviePy for video processing
- Instagram API integration (optional)

### Frontend
- React-based web interface
- Tailwind CSS for styling
- Framer Motion for animations

### Infrastructure
- File system storage for uploads
- Environment-based configuration
- CORS support for secure API access

## Screenshots

_[Add screenshots here]_

## Installation

### Prerequisites
- Python 3.9+
- Node.js and npm
- OpenAI API key
- FFmpeg (for video processing)
- Docker and Docker Compose (optional, for containerized setup)

### Setup

#### Option 1: Traditional Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/fact-check.git
   cd fact-check
   ```

2. Copy `env.example` to `.env` and fill in your credentials
   ```bash
   cp env.example .env
   ```

3. Install backend dependencies
   ```bash
   pip install -r requirements.txt
   ```
   or with conda:
   ```bash
   conda env create -f environment.yml
   ```

4. Install frontend dependencies
   ```bash
   cd video-transcription-frontend
   npm install
   ```

#### Option 2: Docker Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/fact-check.git
   cd fact-check
   ```

2. Copy `env.example` to `.env` and fill in your credentials
   ```bash
   cp env.example .env
   ```

3. Build and start the Docker containers
   ```bash
   docker-compose up -d
   ```

   This will:
   - Build the backend container with Python and FastAPI
   - Build the frontend container with Node.js and React
   - Configure Nginx for serving the frontend and proxying API requests
   - Set up volume mapping for uploads and environment variables

4. Access the application at http://localhost

## Usage

### Running with Docker

```bash
# Start the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the services
docker-compose down

# Rebuild and start the services (after making changes)
docker-compose up -d --build
```

### Running the Backend Server (without Docker)

```bash
cd video-upload-app
uvicorn app:app --reload
```

### Running the Frontend Development Server (without Docker)

```bash
cd video-transcription-frontend
npm start
```

### Building for Production

```bash
cd video-transcription-frontend
npm run build
```

## Environment Variables

Set the following environment variables in your `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | required |
| `GOOGLE_API_KEY` | Your Google API key (if applicable) | optional |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed origins for CORS | https://fact.scdesign.eu,http://localhost:3000 |
| `FACT_CHECK_MODEL` | OpenAI model for fact checking | chatgpt-4o-latest |
| `IMAGE_ANALYSIS_MODEL` | OpenAI model for image analysis | gpt-4-vision-preview |
| `TRANSCRIPTION_MODEL` | OpenAI model for transcription | whisper-1 |
| `REACT_APP_MAX_UPLOAD_SIZE` | Maximum upload size in MB | 2500 |
| `ALLOWED_FILE_TYPES` | Comma-separated list of allowed file extensions | mp4,mov,avi |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload a video for processing |
| `/transcribe` | POST | Transcribe an already uploaded video |
| `/fact-check` | POST | Perform fact-checking on a transcription |
| _[Add more endpoints as needed]_ |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the AI models
- All contributors who have helped with the project

## Contact

- Uygar Duzgun - [uygarduzgun.com](https://uygarduzgun.com)
- GitHub: [owgit](https://github.com/owgit)
- Support: [Buy me a coffee](https://buymeacoffee.com/uygarduzgun) 