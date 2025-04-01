# Fact Check App

A powerful video and image fact-checking application that uses AI to analyze content for accuracy and misinformation.

## Features

- **Instagram Video Downloads**: Automatically download videos from Instagram for fact-checking
- **Video Transcription**: Convert video audio to text using OpenAI's Whisper model
- **Fact Checking**: Analyze transcribed content for factual accuracy using AI
- **Image Analysis**: Examine images for misinformation and verify visual claims
- **Direct File Upload**: Support for direct video and image file uploads
- **Detailed Reports**: Generate comprehensive HTML reports on fact-checking results

## Supported Media Types

- **Videos**: MP4, MOV, AVI
- **Images**: JPG, JPEG, PNG, GIF
- **Sources**: Instagram links, direct file uploads

## Technologies Used

- **Backend**: FastAPI (Python)
- **Frontend**: React
- **AI Models**:
  - OpenAI GPT models for fact-checking
  - OpenAI Whisper for transcription
  - OpenAI Vision model for image analysis
- **Media Processing**: MoviePy, FFmpeg
- **Social Media Integration**: Instaloader for Instagram downloads

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js and npm
- FFmpeg installed on your system

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
FACT_CHECK_MODEL=gpt-4o-mini
IMAGE_ANALYSIS_MODEL=gpt-4-vision-preview
TRANSCRIPTION_MODEL=whisper-1
INSTAGRAM_MAX_RETRIES=3
INSTAGRAM_RETRY_DELAY=2
```

### Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/factCheck.git
cd factCheck
```

2. Set up the Python backend:
```
cd video-upload-app
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the React frontend:
```
npm install
```

4. Start the backend server:
```
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

5. In a separate terminal, start the frontend:
```
npm start
```

6. Open your browser to http://localhost:3000

## Usage

1. Enter an Instagram URL or upload a video/image file
2. The app will download the content (if from Instagram)
3. For videos, audio will be extracted and transcribed
4. The AI will analyze the content for factual accuracy
5. A detailed fact-checking report will be generated

## Notes

- Instagram's anti-scraping measures may occasionally block automated downloads. In these cases, you can download the video manually and upload it directly.
- The accuracy of fact-checking depends on the AI models and the available information at the time of analysis.
