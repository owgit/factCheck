# AI-Powered Fact Check Tool

![2](https://github.com/user-attachments/assets/b9df478c-ab60-44ef-9b99-9a73de056c68)
![1](https://github.com/user-attachments/assets/1d76a336-938b-46e4-89ee-a02856efe8f9)

## Overview

An AI-powered fact-checking application that automatically transcribes, analyzes, and verifies claims from videos, Instagram content, and text. This tool helps combat misinformation by providing evidence-based verification with accurate source references.

**Repository**: [https://github.com/owgit/factCheck](https://github.com/owgit/factCheck)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-green)](https://openai.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)](https://www.docker.com/)

## Features

- **Multi-Source Verification**: Process videos, Instagram posts, and free text input
- **AI Transcription**: Convert speech to text using OpenAI's Whisper model
- **Advanced Fact Checking**: Verify claims using OpenAI's GPT-4o with web search capabilities
- **Claim Detection**: Automatically extract and analyze factual statements
- **Image Analysis**: Extract and analyze visual content from videos and images
- **Detailed Reports**: Get comprehensive fact-check reports with sources and reliability scores
- **Multilingual Support**: Automatically detects input language and responds accordingly
- **Web Search Integration**: Enhances verification accuracy with real-time web information
- **User API Keys**: Users can provide their own OpenAI API key to use their own credits
- **Monetization Ready**: Built-in ad placeholders with skyscraper ads on both sides
- **Responsive Design**: Optimized for all screen sizes with a wider content area on large screens

## Screenshots

<div align="center">
  <img src="https://github.com/user-attachments/assets/b9df478c-ab60-44ef-9b99-9a73de056c68" width="48%" />
  <img src="https://github.com/user-attachments/assets/1d76a336-938b-46e4-89ee-a02856efe8f9" width="48%" />
</div>

## Tech Stack

### Backend
- Python with FastAPI
- OpenAI API integration (GPT-4o, Whisper)
- MoviePy for video processing
- Instagram content extraction

### Frontend
- React with user-friendly tabbed interface
- Tailwind CSS for styling
- Responsive design with skyscraper ad support
- User-provided API key management

### Infrastructure
- Docker and Docker Compose for containerization
- Environment-based configuration

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js and npm
- OpenAI API key
- FFmpeg (for video processing)
- Docker and Docker Compose (optional)

### Quick Setup

1. Clone the repository
   ```bash
   git clone https://github.com/owgit/factCheck.git
   cd factCheck
   ```

2. Copy `env.example` to `.env` and add your API keys
   ```bash
   cp env.example .env
   ```

3. Choose your setup method:

   **Docker Setup (Recommended)**
   ```bash
   docker-compose up -d
   ```
   Access at http://localhost

   **Manual Setup**
   ```bash
   # Install backend dependencies
   pip install -r requirements.txt
   
   # Start backend
   cd video-upload-app
   uvicorn app:app --reload
   
   # In another terminal, install and start frontend
   cd video-transcription-frontend
   npm install
   npm start
   ```
   Access at http://localhost:3000

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key (users can also input their own in the UI) | required for server |
| `FACT_CHECK_MODEL` | OpenAI model for fact checking | chatgpt-4o-latest |
| `IMAGE_ANALYSIS_MODEL` | OpenAI model for image analysis | gpt-4o-mini |
| `TRANSCRIPTION_MODEL` | OpenAI model for transcription | whisper-1 |
| `WEB_SEARCH_MODEL` | Model used for web searches | gpt-4o-search-preview |
| `USE_WEB_SEARCH` | Enable web search during fact checking | true |
| `INSTAGRAM_USERNAME` | Instagram username for content extraction | optional |
| `INSTAGRAM_PASSWORD` | Instagram password for content extraction | optional |

See `.env.example` for all configuration options.

## Monetization

The application includes built-in ad placeholders for easy monetization:

- **Skyscraper Ads**: 160px × 600px ads on both sides of the content
- **Leaderboard Ads**: 728px × 90px ads at the top and bottom
- **In-Content Ads**: Banner ads (468px × 60px) between content sections

These placeholders can be easily replaced with actual ad code from ad networks like Google AdSense.

## User API Keys

Users can now provide their own OpenAI API key in the UI:

- Secure input with show/hide functionality
- Local storage to remember the key between sessions 
- Validation to ensure proper key format (must start with "sk-")
- Visual feedback for saved and invalid states
- All API requests include the user's key when provided

This feature allows users to use their own OpenAI credits instead of the server's.

## How It Works

1. **Input Processing**: Upload a video, provide an Instagram URL, or enter text
2. **Text Extraction**: For videos, speech is transcribed to text using Whisper
3. **Fact Identification**: The system identifies key factual claims in the content
4. **Verification**: Each claim is verified against reliable sources and web information
5. **Report Generation**: A comprehensive fact-check report is generated with sources and reliability ratings

## Troubleshooting

### Instagram Integration

Instagram integration may encounter issues due to Instagram's measures against automated access:

- **401 Unauthorized**: Try different credentials or manual upload
- **No media found**: Content might be private or inaccessible
- **Page structure errors**: Instagram may have changed their page structure

### Docker Issues

If you encounter Docker-related problems:
```bash
# Debug Docker setup
./docker-debug.sh

# Check logs
docker-compose logs -f

# Rebuild containers
docker-compose up -d --build
```

### Web Search Issues

If the web search functionality isn't working:
- Verify your OpenAI API key has access to search-enabled models
- Check that `WEB_SEARCH_MODEL` is set to a search-capable model (e.g., `gpt-4o-search-preview`)
- Ensure `USE_WEB_SEARCH` is set to `true` in your environment

### User API Key Issues

If the user API key functionality isn't working:
- Make sure your backend server is configured to accept the `X-OpenAI-Api-Key` header
- Verify that the OpenAI key format is correct (should start with "sk-")
- Try clearing browser storage and re-entering the key

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License, which allows you to use, modify, and distribute the code freely.

## Attribution

While not required by the license, if you use this repository, the author would appreciate:

1. Including a credit to Uygar Duzgun in your project
2. Adding a link back to https://uygarduzgun.com
3. Letting the author know how you're using the project

## Contact

- Uygar Duzgun - [uygarduzgun.com](https://uygarduzgun.com)
- GitHub: [owgit](https://github.com/owgit)
- Support: [Buy me a coffee](https://buymeacoffee.com/uygarduzgun)
