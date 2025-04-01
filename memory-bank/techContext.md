# Technical Context

## Technologies Used

### Backend
- Python (based on requirements.txt)
- OpenAI API integration
  - Whisper API for transcription
  - GPT API for fact checking
  - GPT-4o (chatgpt-4o-latest) as the fact checking model
  - GPT-4 Vision Preview for image analysis
- API-based architecture

### Frontend
- Web-based interface (likely JavaScript/React based on directory structure)

### Development Environment
- macOS (M4 Mac)
- MAMP for local development
- Python virtual environment (venv)
- Conda environment (based on environment.yml)

## Technical Constraints
- Maximum upload size: 2500MB (from .env)
- Allowed file types: mp4, mov, avi (from .env)
- API rate limits from OpenAI

## Dependencies
- See requirements.txt for Python dependencies
- OpenAI API access is required
- Google API (referenced in .env but usage unknown)

## API Integration
- OpenAI Whisper API for transcription
- OpenAI Chat Completions API for fact checking
- Possible Google API integration

## Authentication & Security
- API keys stored in environment variables
- CORS configuration to limit allowed origins
- Instagram credentials stored in environment (may be for testing/integration)

## Deployment
- Currently unknown, needs further investigation 