import os
import base64
import logging
import time
import random
import requests
import traceback
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from moviepy.editor import VideoFileClip
from openai import OpenAI
from dotenv import load_dotenv
import instaloader
import glob
import shutil
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.getenv('ENV_FILE', os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
load_dotenv(dotenv_path=env_path)

# ... (other imports and setup code)

INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

# Get CORS settings from env with fallback to allow all origins in development
ALLOWED_ORIGINS_ENV = os.getenv('ALLOWED_ORIGINS', '*')
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_ENV.split(',')] if ALLOWED_ORIGINS_ENV != '*' else ['*']

# Max retries for Instagram downloads
INSTAGRAM_MAX_RETRIES = int(os.getenv('INSTAGRAM_MAX_RETRIES', '3'))
INSTAGRAM_RETRY_DELAY = int(os.getenv('INSTAGRAM_RETRY_DELAY', '2'))

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
    """Download video from Instagram with better error handling and fallback mechanism"""
    is_docker = os.path.exists('/.dockerenv')  # Check if running in Docker
    
    if is_docker:
        logger.info("Running in Docker environment - using adapted Instagram download approach")
    
    for attempt in range(INSTAGRAM_MAX_RETRIES):
        try:
            cleanup_old_files()
            logger.info(f"Instagram download attempt {attempt+1}/{INSTAGRAM_MAX_RETRIES} for URL: {url}")
            
            # Improved URL parsing to extract shortcode/post ID
            shortcode = None
            if '/p/' in url:
                shortcode = url.split('/p/')[1].split('/')[0].split('?')[0]
            elif '/reel/' in url:
                shortcode = url.split('/reel/')[1].split('/')[0].split('?')[0]
            elif '/tv/' in url:
                shortcode = url.split('/tv/')[1].split('/')[0].split('?')[0]
            else:
                # Try to extract from end of URL
                path_parts = url.rstrip('/').split('/')
                if len(path_parts) > 0:
                    potential_code = path_parts[-1].split('?')[0]
                    if potential_code and not potential_code.startswith('http'):
                        shortcode = potential_code
            
            if not shortcode:
                logger.error("Could not extract shortcode from Instagram URL")
                raise ValueError("Invalid Instagram URL format")
                
            logger.info(f"Extracted Instagram shortcode: {shortcode}")
            
            # Add jitter to delay to appear more like human behavior
            delay = INSTAGRAM_RETRY_DELAY + random.uniform(0.5, 2.0)
            logger.info(f"Waiting {delay:.2f} seconds before Instagram request")
            time.sleep(delay)
            
            # Setup instaloader with specific settings for Docker environment
            L = instaloader.Instaloader(
                dirname_pattern=UPLOAD_DIRECTORY,
                download_videos=True,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False
            )
            
            # Improved login handling
            login_successful = False
            if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
                try:
                    logger.info(f"Logging in to Instagram as {INSTAGRAM_USERNAME}")
                    L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                    logger.info("Instagram login successful")
                    login_successful = True
                    # Add substantial delay after login to reduce suspicion
                    time.sleep(3 if is_docker else 1.5)
                except Exception as login_error:
                    logger.error(f"Instagram login failed: {str(login_error)}")
                    logger.error(traceback.format_exc())
                    # Don't abort on login failure, try anonymous download
                    
            # Try to download post
            try:
                logger.info(f"Downloading Instagram post with shortcode: {shortcode}")
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                L.download_post(post, target=UPLOAD_DIRECTORY)
                logger.info("Instagram download successful")
            except Exception as e:
                logger.error(f"Error downloading via Instaloader: {str(e)}")
                logger.error(traceback.format_exc())
                
                # More specific error details for debugging
                if "401" in str(e):
                    logger.error("Instagram 401 error: Authentication required or rate limited")
                elif "429" in str(e):
                    logger.error("Instagram 429 error: Too many requests, rate limited")
                elif "Login required" in str(e):
                    logger.error("Instagram requires login for this content")
                elif "window._sharedData" in str(e):
                    logger.error("Instagram page structure changed - parser needs updating")
                
                raise e
            
            # Find downloaded media files
            media_files = [f for f in glob.glob(os.path.join(UPLOAD_DIRECTORY, "*")) 
                          if f.lower().endswith(('.mp4', '.jpg', '.jpeg', '.png')) and 
                          os.path.getmtime(f) > time.time() - 60]  # Only consider recent files
            
            if not media_files:
                logger.warning("No media files found after download")
                raise FileNotFoundError("No media files downloaded")
            
            latest_media_file = max(media_files, key=os.path.getctime)
            logger.info(f"Found media file: {latest_media_file}")
            return latest_media_file
            
        except Exception as e:
            logger.error(f"Instagram download attempt {attempt+1} failed: {str(e)}")
            
            # If we've tried all attempts, try the direct fallback approach
            if attempt == INSTAGRAM_MAX_RETRIES - 1:
                logger.warning("All Instagram download attempts failed, using fallback")
                return handle_instagram_fallback(url)
            
            # Otherwise wait before retrying with increasing delay
            retry_delay = INSTAGRAM_RETRY_DELAY * (attempt + 1) + random.uniform(1, 3)
            logger.info(f"Waiting {retry_delay:.2f} seconds before retry #{attempt+2}")
            time.sleep(retry_delay)
    
    # This should not be reached due to the fallback, but just in case
    raise HTTPException(
        status_code=500,
        detail="Failed to download Instagram content after multiple attempts"
    )

def handle_instagram_fallback(url: str) -> str:
    """Fallback method when instaloader fails - returns error and suggests manual upload"""
    logger.info("Using Instagram fallback mechanism")
    
    # Create detailed error message
    error_message = (
        "Instagram download failed. Instagram's API is blocking automated access from our server. "
        "This is a common issue with Instagram's anti-scraping measures. "
        "Please download the video manually and upload it directly."
    )
    
    # Log the specific URL that failed
    logger.error(f"Instagram fallback triggered for URL: {url}")
    
    # Return a structured error response that the frontend can handle
    raise HTTPException(
        status_code=502,  # Bad Gateway
        detail={
            "error": "instagram_blocked",
            "message": error_message,
            "suggestion": "Please download the video manually and upload the file directly.",
            "url": url
        }
    )

@app.post("/upload")
async def upload_file(file: UploadFile = File(None), url: str = Form(None), background_tasks: BackgroundTasks = None):
    try:
        cleanup_old_files()
        
        if url:
            if "instagram.com" in url or "instagr.am" in url:
                try:
                    media_path = download_instagram_video(url)
                except HTTPException as e:
                    if e.status_code == 502 and isinstance(e.detail, dict) and e.detail.get("error") == "instagram_blocked":
                        # Return a more user-friendly error for frontend handling
                        return JSONResponse(
                            status_code=502,
                            content={
                                "error": "instagram_blocked",
                                "message": e.detail.get("message", "Instagram download failed"),
                                "suggestion": e.detail.get("suggestion", "Please upload the file directly"),
                                "url": e.detail.get("url", url)
                            }
                        )
                    else:
                        raise e
            else:
                # Handle other URLs if needed
                raise HTTPException(status_code=400, detail="Only Instagram URLs are currently supported")
        elif file:
            media_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
            with open(media_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        else:
            raise HTTPException(status_code=400, detail="No file or URL provided")

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
        logger.error(f"Error processing upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)