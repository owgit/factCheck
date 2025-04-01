# Fact Check

A video fact-checking application that automatically transcribes and verifies factual claims in uploaded videos.

## Features

- Video upload and processing
- Automatic transcription using OpenAI's Whisper model
- Fact checking using OpenAI's GPT-4o
- User-friendly interface
- Support for various video formats (mp4, mov, avi)

## Tech Stack

- Backend: Python
- Frontend: Web-based interface
- OpenAI API for transcription and fact checking
- File system storage for uploads

## Setup

1. Clone the repository
2. Copy `env.example` to `.env` and fill in your credentials:
   ```
   cp env.example .env
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   or with conda:
   ```
   conda env create -f environment.yml
   ```
4. Run the application (instructions may vary based on deployment method)

## Environment Variables

Set the following environment variables in your `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key
- `GOOGLE_API_KEY`: Your Google API key (if applicable)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins for CORS
- Other variables as shown in the env.example file

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Specify your license here]

## Contact

- Uygar Duzgun - [uygarduzgun.com](https://uygarduzgun.com)
- GitHub: [owgit](https://github.com/owgit) 