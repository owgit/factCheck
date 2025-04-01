import os
import base64
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from moviepy.editor import VideoFileClip
from openai import OpenAI
from dotenv import load_dotenv
import instaloader
import glob
import shutil
from datetime import datetime, timedelta

# Load environment variables
env_path = os.getenv('ENV_FILE', os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv(dotenv_path=env_path)

# ... (other imports and setup code)

INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'https://fact.scdesign.eu').split(',')

# Get model names from environment variables with defaults
FACT_CHECK_MODEL = os.getenv('FACT_CHECK_MODEL', 'gpt-4o-mini')
IMAGE_ANALYSIS_MODEL = os.getenv('IMAGE_ANALYSIS_MODEL', 'gpt-4-vision-preview')
TRANSCRIPTION_MODEL = os.getenv('TRANSCRIPTION_MODEL', 'whisper-1')

app = FastAPI(root_path="/api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

UPLOAD_DIRECTORY = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.chmod(UPLOAD_DIRECTORY, 0o755)

def cleanup_old_files():
    current_time = datetime.now()
    for filename in os.listdir(UPLOAD_DIRECTORY):
        file_path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.isfile(file_path):
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            if current_time - file_modified > timedelta(hours=24):
                os.remove(file_path)
                logging.debug(f"Removed old file: {file_path}")

def perform_fact_check(text):
    prompt = f"""
    Perform a thorough fact-check on the following text. Follow these steps:
    1. Identify the main claims in the text.
    2. For each claim:
       a. Search for reliable sources to verify the claim.
       b. If no reliable sources are found, state "Unable to verify" for that claim.
       c. If reliable sources are found, assess the claim's accuracy.
       d. Provide a brief explanation for your assessment.
    3. Analyze the detailed accuracy of the text.
    4. If you're unsure about any aspect, clearly state "I don't know" for that part.

    IMPORTANT SOURCE GUIDELINES:
    - Only include source URLs that are from mainstream, established websites that are very likely to remain accessible.
    - Verify that the URLs you provide are the main domain or stable article links, not temporary search results or dynamic pages.
    - For news sources, prefer stable archive links or permalink URLs when available.
    - If you cannot find a reliably stable URL for a source, describe the source without including a URL.
    - Only include sources you're highly confident are legitimate, accessible, and will not lead to 404 errors.
    - Prefer widely recognized authoritative sources (government agencies, major news outlets, academic institutions).

    Text to check:
    <text_to_check>
    {text}
    </text_to_check>

    Respond with HTML in this format and language from the context:
    <div class="fact-check">
        <h2 class="result">[INCONCLUSIVE, MOSTLY ACCURATE, MOSTLY INACCURATE, or MIXED]</h2>
        <section class="analysis">
            <h3>Conclusion:</h3>
            <p>[Detailed summary of overall accuracy, including any uncertainties or limitations in the fact-checking process]</p>
        </section>
        <section class="sources">
            <h3>Sources:</h3>
            <ul>
                <li><a href="[STABLE_URL]">[Source 1 description]</a></li>
                <li><a href="[STABLE_URL]">[Source 2 description]</a></li>
                <li>[Source without URL - description only]</li>
            </ul>
        </section>
        <section class="findings">
            <h3>Findings:</h3>
            <ul>
                <li>
                    <strong>Claim 1:</strong>
                    <span class="claim-text">[Claim text]</span> -
                    <span class="accuracy">[Accurate, Inaccurate, Partly accurate, Unable to verify, or I don't know]</span>
                    <p class="explanation">[Detailed explanation with reference to sources]</p>
                </li>
            </ul>
        </section>
    </div>
    """

    try:
        response = client.chat.completions.create(
            model=FACT_CHECK_MODEL,
            messages=[
                {"role": "system", "content": "You are a meticulous fact-checker. Always prioritize accuracy over completeness. If you're unsure about any information, clearly state 'I don't know' or 'Unable to verify'. Use only highly reliable sources for verification. Be extremely careful with URLs - only include stable, permanent links from established websites, and avoid dynamic search results or temporary pages. When in doubt about a URL's permanence, provide the source description without a URL. Use same language as the content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error in perform_fact_check: {str(e)}")
        return None

def analyze_image(image_path):
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    prompt = f"""
    Analyze the given image with a focus on fact-checking and identifying potential misinformation. Follow these steps:
    1. Describe the main elements and context of the image briefly.
    2. Identify the main claims (textual or visual).
    3. For each claim:
       a. Search for reliable sources to verify the claim.
       b. If no reliable sources are found, state "Unable to verify" for that claim.
       c. If reliable sources are found, assess the claim's accuracy.
       d. Provide a brief explanation for your assessment.
    4. Analyze the detailed accuracy of the image.
    5. If you're unsure about any aspect, clearly state "I don't know" for that part.

    IMPORTANT SOURCE GUIDELINES:
    - Only include source URLs that are from mainstream, established websites that are very likely to remain accessible.
    - Verify that the URLs you provide are the main domain or stable article links, not temporary search results or dynamic pages.
    - For news sources, prefer stable archive links or permalink URLs when available.
    - If you cannot find a reliably stable URL for a source, describe the source without including a URL.
    - Only include sources you're highly confident are legitimate, accessible, and will not lead to 404 errors.
    - Prefer widely recognized authoritative sources (government agencies, major news outlets, academic institutions).

    Respond with HTML in this format and language from the context:
    <div class="fact-check">
        <h2 class="result">[INCONCLUSIVE, MOSTLY ACCURATE, MOSTLY INACCURATE, or MIXED]</h2>
        <section class="analysis">
            <h3>Conclusion:</h3>
            <p>[Detailed summary of overall accuracy, including any uncertainties or limitations in the fact-checking process]</p>
        </section>
        <section class="sources">
            <h3>Sources:</h3>
            <ul>
                <li><a href="[STABLE_URL]">[Source 1 description]</a></li>
                <li><a href="[STABLE_URL]">[Source 2 description]</a></li>
                <li>[Source without URL - description only]</li>
            </ul>
        </section>
        <section class="findings">
            <h3>Findings:</h3>
            <ul>
                <li>
                    <strong>Claim 1:</strong>
                    <span class="claim-text">[Claim text]</span> -
                    <span class="accuracy">[Accurate, Inaccurate, Partly accurate, Unable to verify, or I don't know]</span>
                    <p class="explanation">[Detailed explanation with reference to sources]</p>
                </li>
            </ul>
        </section>
    </div>
    """

    try:
        response = client.chat.completions.create(
            model=IMAGE_ANALYSIS_MODEL,
            messages=[
                {"role": "system", "content": "You are a meticulous image fact-checker. Analyze images for factual claims and potential misinformation. Prioritize accuracy over completeness. If you're unsure about any information, clearly state 'Unable to verify'. Be extremely careful with URLs - only include stable, permanent links from established websites, and avoid dynamic search results or temporary pages. When in doubt about a URL's permanence, provide the source description without a URL. Use same language as the content."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error in analyze_image: {str(e)}")
        return None

def process_video(video_path):
    try:
        audio_path = os.path.join(UPLOAD_DIRECTORY, "extracted_audio.wav")
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        video.close()

        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=TRANSCRIPTION_MODEL, 
                file=audio_file
            )

        fact_check_html = perform_fact_check(transcription.text)

        os.remove(video_path)
        os.remove(audio_path)

        return JSONResponse(content={
            "transcription": transcription.text,
            "fact_check_html": fact_check_html
        })
    except Exception as e:
        logging.error(f"Error processing video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

def download_instagram_video(url: str) -> str:
    try:
        cleanup_old_files()
        L = instaloader.Instaloader(dirname_pattern=UPLOAD_DIRECTORY)
        
        # First try to download without login (for public content)
        try:
            logging.debug("Attempting to download without login")
            post = instaloader.Post.from_shortcode(L.context, url.split("/")[-2])
            L.download_post(post, target=UPLOAD_DIRECTORY)
        except instaloader.exceptions.LoginRequiredException:
            # If login required, try to login
            logging.debug("Login required for this content")
            if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
                try:
                    L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                    logging.debug("Login successful")
                    # Download again with login
                    post = instaloader.Post.from_shortcode(L.context, url.split("/")[-2])
                    L.download_post(post, target=UPLOAD_DIRECTORY)
                except Exception as login_error:
                    logging.error(f"Login failed: {str(login_error)}")
                    raise HTTPException(status_code=401, detail="Instagram login failed. This content requires login, but login attempt was unsuccessful.")
            else:
                raise HTTPException(status_code=403, detail="Instagram login required but no credentials provided")
        
        media_files = [f for f in glob.glob(os.path.join(UPLOAD_DIRECTORY, "*")) 
                       if f.lower().endswith(('.mp4', '.jpg', '.jpeg', '.png'))]
        
        if not media_files:
            raise FileNotFoundError(f"No media files found in {UPLOAD_DIRECTORY}")
        
        latest_media_file = max(media_files, key=os.path.getctime)
        logging.debug(f"Latest media file found: {latest_media_file}")
        
        return latest_media_file
    except Exception as e:
        logging.error(f"Error downloading Instagram content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading Instagram content: {str(e)}")

@app.post("/upload")
async def upload_file(file: UploadFile = File(None), url: str = Form(None)):
    try:
        cleanup_old_files()
        
        if url:
            media_path = download_instagram_video(url)
        elif file:
            media_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
            with open(media_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        else:
            raise HTTPException(status_code=400, detail="No file or URL provided.")

        if not os.path.exists(media_path):
            raise HTTPException(status_code=404, detail=f"Media file not found: {media_path}")

        if media_path.lower().endswith(('.mp4', '.mov', '.avi')):
            return process_video(media_path)
        elif media_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            image_analysis = analyze_image(media_path)
            return JSONResponse(content={"image_analysis": image_analysis})
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported media type: {media_path}")

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)