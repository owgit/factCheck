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

![2](https://github.com/user-attachments/assets/b9df478c-ab60-44ef-9b99-9a73de056c68)
![1](https://github.com/user-attachments/assets/1d76a336-938b-46e4-89ee-a02856efe8f9)


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

# Debug Docker issues
./docker-debug.sh
```

## Troubleshooting

### Docker Issues

If you encounter issues with the Docker setup:

1. Run the debugging script: `./docker-debug.sh`
2. Check container logs: `docker-compose logs`
3. Verify file permissions in containers
4. Ensure your `.env` file is correctly set up
5. If necessary, rebuild containers: `docker-compose up -d --build`

- **Error: No such file or directory**: Ensure all paths in docker-compose.yml are correct and that you've created any required directories.
- **Backend can't connect to OpenAI API**: Verify your API key in the .env file is correct and that you have sufficient credits.
- **Frontend not connecting to backend**: Check the REACT_APP_API_URL in your environment variables and ensure the backend service is running.

### Instagram Integration Issues

The Instagram integration uses third-party libraries to download content from Instagram for fact-checking. Due to Instagram's measures against automated access, you may encounter the following issues:

#### Common Errors

1. **401 Unauthorized Error**: Instagram is actively blocking the connection.
   - **Solution**: Try using different Instagram credentials in your .env file.
   - **Alternative**: Download the video manually and upload it directly.

2. **"Could not find window._sharedData" Error**: Instagram has changed their page structure.
   - **Solution**: Wait for a library update or use the manual upload option.

3. **No media found after download**: The content might be private or not accessible.
   - **Solution**: Ensure you're using credentials that have access to the content.

#### Mitigation Strategies

- Increase `INSTAGRAM_MAX_RETRIES` and `INSTAGRAM_RETRY_DELAY` in your .env file
- Use an Instagram account with fewer restrictions
- If Instagram integration is critical, consider implementing a browser automation solution (like Selenium)

#### Note on Instagram's Policies

Instagram actively works to prevent automated access to their platform. The application's ability to download content may be affected by:
- Instagram's frequent API and website changes
- Rate limiting and blocking of automated requests
- Login challenges and captchas when using automated tools

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
| `INSTAGRAM_USERNAME` | Instagram username for downloading content | optional |
| `INSTAGRAM_PASSWORD` | Instagram password for downloading content | optional |
| `INSTAGRAM_MAX_RETRIES` | Maximum number of retry attempts for Instagram | 3 |
| `INSTAGRAM_RETRY_DELAY` | Delay between retry attempts in seconds | 2 |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed origins for CORS | * |
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
