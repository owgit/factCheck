import os
import base64
import logging
import time
import random
import requests
import traceback
import re  # Ensure re is imported at the module level
import json  # Add json import at the module level
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
import langdetect

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
logger.info(f"Loading environment from: {env_path}")

# Load the API key separately to guarantee we have the correct one
api_key = None
try:
    with open(env_path, 'r') as env_file:
        for line in env_file:
            if line.startswith('OPENAI_API_KEY='):
                api_key = line.strip().split('=', 1)[1]
                # Remove any quotes if present
                api_key = api_key.strip('\'"')
                break
    
    if api_key:
        masked_key = api_key[:10] + "..." + api_key[-5:]
        logger.info(f"Using API key from .env file: {masked_key}")
        # Set the environment variable explicitly
        os.environ['OPENAI_API_KEY'] = api_key
    else:
        logger.error("No OpenAI API key found in .env file!")
except Exception as e:
    logger.error(f"Error reading API key from .env file: {str(e)}")

# Now load the rest of the environment variables
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
IMAGE_ANALYSIS_MODEL = os.getenv('IMAGE_ANALYSIS_MODEL', 'gpt-4o-mini')
TRANSCRIPTION_MODEL = os.getenv('TRANSCRIPTION_MODEL', 'whisper-1')

# Fact checking reliability settings
FACT_CHECK_MAX_RETRIES = int(os.getenv('FACT_CHECK_MAX_RETRIES', '3'))
FACT_CHECK_RETRY_DELAY = int(os.getenv('FACT_CHECK_RETRY_DELAY', '2'))
FACT_CHECK_TEMPERATURE = float(os.getenv('FACT_CHECK_TEMPERATURE', '0.2'))

# Web search configuration for fact checking
USE_WEB_SEARCH = os.getenv('USE_WEB_SEARCH', 'true').lower() in ('true', 'yes', '1')
WEB_SEARCH_MODEL = os.getenv('WEB_SEARCH_MODEL', 'gpt-4o-search-preview')
WEB_SEARCH_CONTEXT_SIZE = os.getenv('WEB_SEARCH_CONTEXT_SIZE', 'medium')

# Instagram download method configuration
USE_YTDLP = os.getenv('USE_YTDLP', 'true').lower() in ('true', 'yes', '1')
USE_DIRECT_DOWNLOAD = os.getenv('USE_DIRECT_DOWNLOAD', 'true').lower() in ('true', 'yes', '1')
INSTAGRAM_DEBUG = os.getenv('INSTAGRAM_DEBUG', 'false').lower() in ('true', 'yes', '1')

app = FastAPI(root_path="/api", debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create OpenAI client with the correct API key
client = OpenAI(api_key=api_key)

# Log API key (redacted) for debugging
if api_key:
    masked_key = api_key[:10] + "..." + api_key[-5:]
    logger.info(f"Using OpenAI API key: {masked_key}")
else:
    logger.error("No OpenAI API key found in environment variables or .env file!")

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

def perform_fact_check(text, detected_language=None, should_use_web_search=True, context='video'):
    language_instruction = ""
    if detected_language:
        language_instruction = f"The detected language is {detected_language}. Your entire response MUST be in {detected_language}."
    
    prompt = f"""
    Perform a thorough fact-check on the following text. Follow these steps:
    1. First, identify the language of the input text and ensure your response is in that same language.
    {language_instruction}
    2. Identify the main claims in the text (maximum 5 most significant claims).
    3. For each claim:
       a. Search for reliable sources to verify the claim.
       b. If no reliable sources are found, state "Unable to verify" for that claim.
       c. If reliable sources are found, assess the claim's accuracy using specific criteria.
       d. Provide a brief explanation for your assessment with direct references to sources.
    4. For each claim, rate accuracy on this scale: 
       - Accurate (claim fully supported by reliable sources)
       - Mostly Accurate (claim mostly supported but with minor inaccuracies)
       - Partly Accurate (claim contains a mix of accurate and inaccurate elements)
       - Mostly Inaccurate (claim contains more inaccuracies than accuracies)
       - Inaccurate (claim contradicted by reliable sources)
       - Unable to verify (insufficient reliable information available)
    5. Analyze the overall accuracy of the text based on the verified claims.
    6. If you're unsure about any aspect, clearly state "I don't know" for that part.

    IMPORTANT: Your entire response must be in the same language as the input text.

    IMPORTANT SOURCE GUIDELINES:
    - Only use authoritative, established sources (government agencies, major news outlets, academic journals, established fact-checking organizations).
    - Verify that URLs are stable, permanent links (not search results, temporary pages, or pages requiring login).
    - For news sources, prefer stable archive links or permalink URLs.
    - If you cannot find a reliably stable URL for a source, describe the source without including a URL.
    - Include at least the source name, publication date, and title when referring to sources.
    - Never fabricate sources - if you cannot find relevant reliable sources, state "Unable to verify".

    Text to check:
    <text_to_check>
    {text}
    </text_to_check>

    Respond with HTML in this format and in the same language as the input text:
    <div class="fact-check">
        <h2 class="result">[INCONCLUSIVE, MOSTLY ACCURATE, MOSTLY INACCURATE, or MIXED]</h2>
        <section class="analysis">
            <h3>Conclusion:</h3>
            <p>[Detailed summary of overall accuracy, including any uncertainties or limitations in the fact-checking process]</p>
        </section>
        <section class="sources">
            <h3>Sources:</h3>
            <ul>
                <li><a href="[STABLE_URL]">[Source name - Publication date - Title]</a></li>
                <li><a href="[STABLE_URL]">[Source name - Publication date - Title]</a></li>
                <li>[Source description without URL]</li>
            </ul>
        </section>
        <section class="findings">
            <h3>Findings:</h3>
            <ul>
                <li>
                    <strong>Claim 1:</strong>
                    <span class="claim-text">[Claim text]</span> -
                    <span class="accuracy">[Accurate, Mostly Accurate, Partly Accurate, Mostly Inaccurate, Inaccurate, or Unable to verify]</span>
                    <p class="explanation">[Detailed explanation with specific references to sources]</p>
                </li>
            </ul>
        </section>
    </div>
    """

    # Try up to defined number of times in case of API errors
    max_retries = FACT_CHECK_MAX_RETRIES
    retry_delay = FACT_CHECK_RETRY_DELAY
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=FACT_CHECK_MODEL,
                messages=[
                    {"role": "system", "content": "You are a meticulous fact-checker with expertise in verification and source evaluation. Always prioritize accuracy over completeness. If you're unsure about any information, clearly state 'I don't know' or 'Unable to verify'. Only use highly reliable sources for verification. Be extremely careful with URLs - only include stable, permanent links from established websites. When in doubt about a URL's permanence, provide the source description without a URL. Detect and respond in the same language as the input content. Your response language should match the language of the content you're fact-checking. Never fabricate sources or information - if information cannot be verified, admit this limitation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4096,
                temperature=FACT_CHECK_TEMPERATURE  # Use configurable temperature for factual, consistent responses
            )
            fact_check_result = response.choices[0].message.content.strip()
            
            # Basic validation of the result
            if not fact_check_result or "<div class=\"fact-check\">" not in fact_check_result:
                logger.warning(f"Invalid fact check result format on attempt {attempt+1}. Retrying...")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
            
            # Check if the result contains proper sections
            required_sections = ["<h2 class=\"result\">", "<section class=\"analysis\">", 
                                "<section class=\"findings\">"]
            missing_sections = [section for section in required_sections if section not in fact_check_result]
            
            if missing_sections:
                logger.warning(f"Fact check result missing sections: {missing_sections} on attempt {attempt+1}. Retrying...")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
            
            # Add AI model information to the fact-check result
            if "</div>" in fact_check_result:
                # Build models section based on context
                models_list = []
                if context == 'video':
                    models_list.append(f"<li><strong>Transcription:</strong> {TRANSCRIPTION_MODEL}</li>")
                models_list.append(f"<li><strong>Fact Checking:</strong> {FACT_CHECK_MODEL}</li>")
                if should_use_web_search:
                    models_list.append(f'<li><strong>Web Search:</strong> {WEB_SEARCH_MODEL}</li>')
                    
                models_section = f"""
                <section class="ai-models">
                    <h3>AI Models Used:</h3>
                    <ul>{"\n".join(models_list)}</ul>
                </section>
                """
                
                fact_check_result = fact_check_result.replace("</div>", f"{models_section}</div>")
            
            return fact_check_result
            
        except Exception as e:
            logger.error(f"Error in perform_fact_check (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                # Pass flag and context to error generator
                return generate_error_fact_check("An error occurred during fact-checking. Please try again later.", should_use_web_search, context)
    
    # Pass flag and context to error generator
    return generate_error_fact_check("Failed to complete fact-checking after multiple attempts.", should_use_web_search, context)

def generate_error_fact_check(error_message, should_use_web_search=True, context='unknown'):
    """Generate a properly formatted error message for fact check failures"""
    
    # Build models section based on context and flag
    models_list = []
    if context == 'video':
        models_list.append(f"<li><strong>Transcription:</strong> {TRANSCRIPTION_MODEL}</li>")
    elif context == 'image':
         models_list.append(f"<li><strong>Image Analysis:</strong> {IMAGE_ANALYSIS_MODEL}</li>")
    # Always show Fact Checking model if context is text or video
    if context in ['text', 'video']:
        models_list.append(f"<li><strong>Fact Checking:</strong> {FACT_CHECK_MODEL}</li>")
        
    if should_use_web_search:
        models_list.append(f'<li><strong>Web Search:</strong> {WEB_SEARCH_MODEL}</li>')
        
    models_section = f"""
    <section class="ai-models">
        <h3>AI Models Used (Attempted):</h3>
        <ul>{"\n".join(models_list)}</ul>
    </section>
    """
    
    return f"""
    <div class="fact-check">
        <h2 class="result">ERROR</h2>
        <section class="analysis">
            <h3>Conclusion:</h3>
            <p>{error_message}</p>
        </section>
        <section class="findings">
            <h3>Findings:</h3>
            <ul>
                <li>
                    <strong>Error:</strong>
                    <span class="claim-text">Fact-checking service unavailable</span> -
                    <span class="accuracy">Unable to verify</span>
                    <p class="explanation">The fact-checking system encountered a technical issue. Please try again later or verify the information manually using reliable sources.</p>
                </li>
            </ul>
        </section>
        {models_section}
    </div>
    """

def perform_web_search(search_query):
    """
    Perform a web search using OpenAI's web search capabilities.
    
    Args:
        search_query: The query to search for
        
    Returns:
        JSON response with search results
    """
    if not USE_WEB_SEARCH:
        logger.info("Web search is disabled")
        return None
    
    logger.info(f"Performing web search for: {search_query}")
    
    try:
        # Define a structured response prompt
        structured_prompt = f"""
        Search the web for information to answer this question:

        "{search_query}"

        Provide a concise but informative answer with specific facts. Include at least 2-3 reputable sources with links where the information was found.

        Format your response in this structure:
        1. Direct answer to the question (2-3 sentences)
        2. Key supporting facts (bullet points)
        3. Sources (numbered list with links)
        """
        
        # Use OpenAI's web search capabilities with the appropriate format for the model
        if WEB_SEARCH_MODEL == "gpt-4o-search-preview":
            # Format for gpt-4o-search-preview which has built-in web search
            response = client.chat.completions.create(
                model=WEB_SEARCH_MODEL,
                messages=[
                    {"role": "system", "content": "You are a skilled fact-checker and web researcher. Your role is to provide accurate, well-sourced answers to factual questions based on current web information. Always cite your sources with links and provide specific facts rather than general statements."},
                    {"role": "user", "content": structured_prompt}
                ]
            )
        else:
            # Format for models that use explicit function calling for web search
            response = client.chat.completions.create(
                model=WEB_SEARCH_MODEL,
                messages=[
                    {"role": "system", "content": "You are a skilled fact-checker and web researcher. Your role is to provide accurate, well-sourced answers to factual questions based on current web information. Always cite your sources with links and provide specific facts rather than general statements."},
                    {"role": "user", "content": structured_prompt}
                ],
                temperature=0.2,
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "search_web",
                        "description": "Search the web for real-time information",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }],
                tool_choice={"type": "function", "function": {"name": "search_web"}}
            )
        
        return {
            "question": search_query,
            "answer": response.choices[0].message.content,
            "model_used": WEB_SEARCH_MODEL,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in web search: {str(e)}")
        return {
            "question": search_query,
            "answer": f"Error performing web search: {str(e)}",
            "model_used": WEB_SEARCH_MODEL,
            "error": True,
            "timestamp": datetime.now().isoformat()
        }

def analyze_image(image_path, should_use_web_search=True):
    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Try to detect language from image text using OCR first (if available)
        detected_language = None
        try:
            # OCR could be added here in the future if needed
            # For now, we'll rely on the AI to detect language
            pass
        except Exception as e:
            logger.warning(f"Could not detect language from image: {str(e)}")
            
        prompt = f"""
        Analyze the given image with a focus on fact-checking and identifying potential misinformation. Follow these steps:
        1. First, identify the language of any text visible in the image. Your entire response should be in this language.
           If no text is visible, respond in the language of the accompanying query or default to English.
        2. Describe the main elements and context of the image briefly.
        3. Identify the main claims (textual or visual) - maximum 5 most significant claims.
        4. For each claim:
           a. Search for reliable sources to verify the claim.
           b. If no reliable sources are found, state "Unable to verify" for that claim.
           c. If reliable sources are found, assess the claim's accuracy using specific criteria.
           d. Provide a brief explanation for your assessment with direct references to sources.
        5. For each claim, rate accuracy on this scale: 
           - Accurate (claim fully supported by reliable sources)
           - Mostly Accurate (claim mostly supported but with minor inaccuracies)
           - Partly Accurate (claim contains a mix of accurate and inaccurate elements)
           - Mostly Inaccurate (claim contains more inaccuracies than accuracies)
           - Inaccurate (claim contradicted by reliable sources)
           - Unable to verify (insufficient reliable information available)
        6. If you're unsure about any aspect, clearly state "I don't know" for that part.
        7. Determine if image appears to be AI-generated or manipulated in any way.
        8. At the end of your analysis, add a special tag indicating the detected language in this format: <detected_language>LANGUAGE_CODE</detected_language>

        IMPORTANT: Your entire response MUST be in the same language as any text visible in the image. This is critical - I need to emphasize that your analysis MUST be written in the EXACT SAME LANGUAGE as the text in the image, even if that language is not English.

        IMPORTANT SOURCE GUIDELINES:
        - Only use authoritative, established sources (government agencies, major news outlets, academic journals, established fact-checking organizations).
        - Verify that URLs are stable, permanent links (not search results, temporary pages, or pages requiring login).
        - For news sources, prefer stable archive links or permalink URLs.
        - If you cannot find a reliably stable URL for a source, describe the source without including a URL.
        - Include at least the source name, publication date, and title when referring to sources.
        - Never fabricate sources - if you cannot find relevant reliable sources, state "Unable to verify".

        Respond with HTML in this format and in the same language as any text in the image:
        <div class="fact-check">
            <h2 class="result">[INCONCLUSIVE, MOSTLY ACCURATE, MOSTLY INACCURATE, MIXED, or AI-GENERATED]</h2>
            <section class="analysis">
                <h3>Conclusion:</h3>
                <p>[Detailed summary of overall accuracy, including any uncertainties or limitations in the fact-checking process]</p>
            </section>
            <section class="sources">
                <h3>Sources:</h3>
                <ul>
                    <li><a href="[STABLE_URL]">[Source name - Publication date - Title]</a></li>
                    <li><a href="[STABLE_URL]">[Source name - Publication date - Title]</a></li>
                    <li>[Source description without URL]</li>
                </ul>
            </section>
            <section class="findings">
                <h3>Findings:</h3>
                <ul>
                    <li>
                        <strong>Claim 1:</strong>
                        <span class="claim-text">[Claim text]</span> -
                        <span class="accuracy">[Accurate, Mostly Accurate, Partly Accurate, Mostly Inaccurate, Inaccurate, or Unable to verify]</span>
                        <p class="explanation">[Detailed explanation with specific references to sources]</p>
                    </li>
                </ul>
            </section>
            <detected_language>LANGUAGE_CODE</detected_language>
        </div>
        """

        # Try up to defined number of times in case of API errors
        max_retries = FACT_CHECK_MAX_RETRIES
        retry_delay = FACT_CHECK_RETRY_DELAY
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=IMAGE_ANALYSIS_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a meticulous image fact-checker with expertise in verification, digital forensics, and source evaluation. Analyze images for factual claims and potential misinformation. Prioritize accuracy over completeness. If you're unsure about any information, clearly state 'Unable to verify'. Be extremely careful with URLs - only include stable, permanent links from established websites. When in doubt about a URL's permanence, provide the source description without a URL. Detect and respond in the same language as the content shown in the image. If there is text in the image, your response language should match that language EXACTLY. If no text is visible, respond in the language of the accompanying query or default to English. Check for signs of AI-generation or manipulation in images. Never fabricate sources or information - if information cannot be verified, admit this limitation."},
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]}
                    ],
                    max_tokens=1000,
                    temperature=FACT_CHECK_TEMPERATURE  # Use configurable temperature for factual, consistent responses
                )
                analysis_result = response.choices[0].message.content.strip()
                
                # Basic validation of the result
                if not analysis_result or "<div class=\"fact-check\">" not in analysis_result:
                    logger.warning(f"Invalid image analysis result format on attempt {attempt+1}. Retrying...")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                
                # Check if the result contains proper sections
                required_sections = ["<h2 class=\"result\">", "<section class=\"analysis\">", 
                                    "<section class=\"findings\">"]
                missing_sections = [section for section in required_sections if section not in analysis_result]
                
                if missing_sections:
                    logger.warning(f"Image analysis result missing sections: {missing_sections} on attempt {attempt+1}. Retrying...")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                
                # Extract detected language if available
                detected_language = None
                language_match = re.search(r'<detected_language>(.*?)</detected_language>', analysis_result)
                if language_match:
                    detected_language = language_match.group(1)
                    # Remove the language tag from the HTML response
                    analysis_result = re.sub(r'<detected_language>.*?</detected_language>', '', analysis_result)
                    logger.info(f"Detected language in image: {detected_language}")
                    
                    # Verify if the response is actually in the detected language
                    if detected_language and detected_language.lower() not in ['en', 'eng', 'english']:
                        # Check if we need to rerun with stronger language enforcement
                        try:
                            # Use langdetect to check the actual language of the response
                            actual_language = langdetect.detect(analysis_result)
                            if actual_language != detected_language:
                                logger.warning(f"Response language mismatch: detected={detected_language}, actual={actual_language}. Will retry.")
                                if attempt < max_retries - 1:
                                    # Modify prompt to strongly enforce language
                                    prompt += f"\n\nCRITICAL: Your response MUST be in {detected_language} language, not in English or any other language!"
                                    time.sleep(retry_delay)
                                    continue
                        except Exception as lang_error:
                            logger.warning(f"Error checking response language: {str(lang_error)}")
                else:
                    logger.info("No language tag found in image analysis result. Using default.")
                    # Try to detect language from the analysis text as a fallback
                    try:
                        detected_language = langdetect.detect(analysis_result)
                        logger.info(f"Detected language from analysis text: {detected_language}")
                    except Exception as lang_error:
                        logger.warning(f"Could not detect language from analysis text: {str(lang_error)}")
                
                # Add AI model information to the image analysis result
                if "</div>" in analysis_result:
                    # Build models section based on context and flag
                    models_list = []
                    models_list.append(f"<li><strong>Image Analysis:</strong> {IMAGE_ANALYSIS_MODEL}</li>")
                    if should_use_web_search:
                        models_list.append(f'<li><strong>Web Search:</strong> {WEB_SEARCH_MODEL}</li>')
                        
                    models_section = f"""
                    <section class="ai-models">
                        <h3>AI Models Used:</h3>
                        <ul>{"\n".join(models_list)}</ul>
                    </section>
                    """
                    
                    analysis_result = analysis_result.replace("</div>", f"{models_section}</div>")
                
                # If web search is enabled, extract claims and perform web search
                web_search_results = None
                if should_use_web_search:
                    try:
                        # Extract key factual claims from the image
                        claims_prompt = """
                        Based on this image, identify 5 specific factual claims that can be directly verified through web searches.
                        Focus on extracting clear, concrete statements that appear in or can be inferred from the image.
                        
                        Format your response as a JSON object with a "claims" field containing an array of strings.
                        Example: {"claims": ["The Eiffel Tower is 330 meters tall", "Barack Obama was the 44th President of the United States", etc.]}
                        
                        Important: Formulate each claim as a direct statement (not a question) that can be fact-checked.
                        """
                        
                        claims_response = client.chat.completions.create(
                            model=IMAGE_ANALYSIS_MODEL,
                            messages=[
                                {"role": "system", "content": "You are a skilled fact-checker who can identify specific, verifiable factual claims in images. Extract only clear, concrete claims that can be verified through web searches."},
                                {"role": "user", "content": [
                                    {"type": "text", "text": claims_prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                ]}
                            ],
                            response_format={"type": "json_object"},
                            max_tokens=500
                        )
                        
                        claims_text = claims_response.choices[0].message.content.strip()
                        logger.info(f"Generated claims from image: {claims_text}")
                        
                        # Parse the JSON response
                        try:
                            claims_obj = json.loads(claims_text)
                            factual_claims = claims_obj.get("claims", [])
                            if not factual_claims:
                                logger.warning("No claims extracted from the response")
                                if isinstance(claims_obj, list):
                                    factual_claims = claims_obj
                        except json.JSONDecodeError as e:
                            # Fallback in case of non-JSON response
                            logger.warning(f"Failed to parse JSON response: {e}")
                            # Try to extract claims using text processing
                            claims_pattern = r'"([^"]+)"'
                            factual_claims = re.findall(claims_pattern, claims_text)
                            if not factual_claims:
                                # Another fallback method
                                claims_text = claims_text.replace("{", "").replace("}", "").replace("[", "").replace("]", "").replace("\"", "")
                                lines = [line.strip() for line in claims_text.split("\n") if line.strip() and not line.strip().startswith('{') and not line.strip().startswith('}')]
                                factual_claims = [line for line in lines if line]
                        
                        logger.info(f"Extracted {len(factual_claims)} claims for web search: {factual_claims}")
                        
                        # Perform web search for each claim
                        web_search_results = []
                        for claim in factual_claims[:5]:  # Limit to 5 claims
                            search_result = perform_web_search(claim)
                            if search_result:
                                web_search_results.append(search_result)
                        
                        logger.info(f"Completed {len(web_search_results)} web searches")
                    
                    except Exception as e:
                        logger.error(f"Error during web search extraction: {str(e)}")
                        web_search_results = [{"error": str(e), "search_query": "Error extracting search queries"}]
                
                # Return the analysis result with detected language
                return {
                    "analysis_result": analysis_result,
                    "web_search_results": web_search_results,
                    "detected_language": detected_language
                }
                
            except Exception as e:
                logger.error(f"Error analyzing image on attempt {attempt+1}: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    # Pass flag and context to error generator
                    return {
                        "analysis_result": generate_error_fact_check(f"Error analyzing image after {max_retries} attempts: {str(e)}", should_use_web_search, 'image'),
                        "detected_language": None,
                        "web_search_results": None
                    }
    except Exception as outer_e:
        logger.error(f"Outer error in analyze_image: {str(outer_e)}", exc_info=True)
        # Pass flag and context to error generator
        return {
            "analysis_result": generate_error_fact_check(f"Error processing image: {str(outer_e)}", should_use_web_search, 'image'),
            "detected_language": None,
            "web_search_results": None
        }
    
    # Pass flag and context to error generator
    return {
        "analysis_result": generate_error_fact_check("Failed to analyze image after maximum retries", should_use_web_search, 'image'),
        "detected_language": None,
        "web_search_results": None
    }

async def process_video(video_path, should_use_web_search=True):
    try:
        audio_path = os.path.join(UPLOAD_DIRECTORY, "extracted_audio.wav")
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        video.close()

        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=TRANSCRIPTION_MODEL, 
                file=audio_file,
                response_format="verbose_json"  # Get verbose response to access language info
            )

        # Log detected language
        detected_language = transcription.language
        logger.info(f"Detected language: {detected_language}")

        # Use text from transcription
        transcription_text = transcription.text

        # Pass flag and context ('video') to fact check
        fact_check_html = perform_fact_check(transcription_text, detected_language, should_use_web_search, context='video')
        
        # Perform web search if enabled
        web_search_results = None
        if should_use_web_search:
            try:
                # Extract key factual claims from the transcription
                claims_prompt = f"""
                Based on this transcription, identify 5 specific factual claims that can be directly verified through web searches.
                Focus on extracting clear, concrete statements that appear in the transcription.
                
                Format your response as a JSON object with a "claims" field containing an array of strings.
                Example: {{"claims": ["The Eiffel Tower is 330 meters tall", "Barack Obama was the 44th President of the United States", etc.]}}
                
                Important: Formulate each claim as a direct statement (not a question) that can be fact-checked.
                
                Transcription:
                {transcription_text[:2000]}  # Use first 2000 chars to keep context manageable
                """
                
                claims_response = client.chat.completions.create(
                    model=FACT_CHECK_MODEL,  # Use the same model as fact checking
                    messages=[
                        {"role": "system", "content": "You are a skilled fact-checker who can identify specific, verifiable factual claims in transcribed content. Extract only clear, concrete claims that can be verified through web searches."},
                        {"role": "user", "content": claims_prompt}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=500
                )
                
                claims_text = claims_response.choices[0].message.content.strip()
                logger.info(f"Generated claims from transcription: {claims_text}")
                
                # Parse the JSON response
                import json
                try:
                    claims_obj = json.loads(claims_text)
                    factual_claims = claims_obj.get("claims", [])
                    if not factual_claims:
                        logger.warning("No claims extracted from the response")
                        if isinstance(claims_obj, list):
                            factual_claims = claims_obj
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    factual_claims = []
                
                # Perform web search for each claim
                web_search_results = []
                for claim in factual_claims[:5]:  # Limit to 5 claims
                    search_result = perform_web_search(claim)
                    if search_result:
                        web_search_results.append(search_result)
                
                logger.info(f"Completed {len(web_search_results)} web searches")
            
            except Exception as e:
                logger.error(f"Error during web search extraction for video: {str(e)}")
                web_search_results = [{"error": str(e), "search_query": "Error extracting search queries"}]

        # Clean up files
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)

        # Include model information in the response
        return JSONResponse(content={
            "transcription": transcription_text,
            "fact_check_html": fact_check_html,
            "detected_language": detected_language,
            "web_search_results": web_search_results,
            "models": {
                "transcription": {"name": TRANSCRIPTION_MODEL},
                "fact_check": {"name": FACT_CHECK_MODEL},
                "web_search": WEB_SEARCH_MODEL if should_use_web_search and web_search_results else "Not used",
                "web_search_enabled": should_use_web_search
            }
        })
    except Exception as e:
        logging.error(f"Error processing video: {str(e)}")
        
        # Clean up files in case of error
        for path in [video_path, audio_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as cleanup_error:
                    logger.warning(f"Error cleaning up file {path}: {str(cleanup_error)}")
                    
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

def download_instagram_video(url: str) -> str:
    """Download video from Instagram with better error handling and fallback mechanism"""
    is_docker = os.path.exists('/.dockerenv')  # Check if running in Docker
    
    if is_docker:
        logger.info("Running in Docker environment - using adapted Instagram download approach")
    
    # Try to extract shortcode from URL first
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
    
    # First try direct method with yt-dlp if enabled and installed
    if USE_YTDLP and attempt_yt_dlp_download(url, shortcode):
        # Find downloaded media files
        media_files = find_media_files()
        
        if media_files:
            latest_media_file = max(media_files, key=os.path.getctime)
            logger.info(f"Found media file: {latest_media_file}")
            return latest_media_file
    
    # If yt-dlp fails or is disabled, fall back to instaloader with retries
    for attempt in range(INSTAGRAM_MAX_RETRIES):
        try:
            cleanup_old_files()
            logger.info(f"Instagram download attempt {attempt+1}/{INSTAGRAM_MAX_RETRIES} for URL: {url}")
            
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
            
            # Track files before download to compare after
            files_before = set(os.listdir(UPLOAD_DIRECTORY))
            
            # Try loading session from file first if it exists
            try:
                session_file = os.path.join(os.path.dirname(__file__), "instagram_session")
                if os.path.exists(session_file):
                    logger.info("Found Instagram session file, attempting to load")
                    L.load_session_from_file(INSTAGRAM_USERNAME, session_file)
                    logger.info("Instagram session loaded successfully")
                    login_successful = True
                else:
                    login_successful = False
            except Exception as e:
                logger.error(f"Error loading Instagram session: {str(e)}")
                login_successful = False
            
            # Attempt login if session load failed
            if not login_successful and INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
                try:
                    logger.info(f"Logging in to Instagram as {INSTAGRAM_USERNAME}")
                    L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                    logger.info("Instagram login successful")
                    # Save the session for future use
                    try:
                        L.save_session_to_file(session_file)
                        logger.info("Saved Instagram session for future use")
                    except Exception as e:
                        logger.error(f"Error saving Instagram session: {str(e)}")
                    login_successful = True
                    # Add substantial delay after login to reduce suspicion
                    time.sleep(3 if is_docker else 1.5)
                except Exception as login_error:
                    logger.error(f"Instagram login failed: {str(login_error)}")
                    logger.error(traceback.format_exc())
                    # Don't abort on login failure, try anonymous download or alternative method
            
            # Try to download post with instaloader
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
                
                # Try alternative download method if instaloader fails and direct download is enabled
                if USE_DIRECT_DOWNLOAD and attempt_alternative_download(url, shortcode):
                    logger.info("Alternative download method succeeded")
                else:
                    raise e
            
            # Find newly added files by comparing directories before and after
            files_after = set(os.listdir(UPLOAD_DIRECTORY))
            new_files = files_after - files_before
            logger.info(f"New files after download: {new_files}")
            
            # First check specifically for video files
            video_files = [os.path.join(UPLOAD_DIRECTORY, f) for f in new_files 
                          if f.lower().endswith(('.mp4', '.mov', '.avi'))]
            
            if video_files:
                latest_video_file = max(video_files, key=lambda f: os.path.getctime(os.path.join(UPLOAD_DIRECTORY, os.path.basename(f))))
                logger.info(f"Found video file: {latest_video_file}")
                return latest_video_file
            
            # If no video files found but other files were added, check for images
            image_files = [os.path.join(UPLOAD_DIRECTORY, f) for f in new_files 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            
            if image_files:
                latest_image_file = max(image_files, key=lambda f: os.path.getctime(os.path.join(UPLOAD_DIRECTORY, os.path.basename(f))))
                logger.info(f"Found image file: {latest_image_file}")
                return latest_image_file
                
            # If we've downloaded something but didn't catch it with the above logic, 
            # Try a broader media file search
            media_files = find_media_files()
            
            if media_files:
                latest_media_file = max(media_files, key=os.path.getctime)
                logger.info(f"Found media file through backup search: {latest_media_file}")
                return latest_media_file
            
            logger.warning("No media files found after download")
            raise FileNotFoundError("No media files downloaded")
            
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

def find_media_files():
    """Helper function to find media files in the upload directory with more robust patterns"""
    # Look for all media files
    media_files = []
    
    # Look for standard media files
    for extension in ('.mp4', '.mov', '.avi', '.jpg', '.jpeg', '.png', '.gif', '.webp'):
        files = glob.glob(os.path.join(UPLOAD_DIRECTORY, f"*{extension}"))
        media_files.extend(files)
    
    # Look for date-formatted Instagram videos (YYYY-MM-DD_HH-MM-SS_UTC.mp4)
    date_pattern_files = glob.glob(os.path.join(UPLOAD_DIRECTORY, "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_*.mp4"))
    media_files.extend(date_pattern_files)
    
    # Only return recent files (created in the last 5 minutes)
    recent_media_files = [f for f in media_files if os.path.exists(f) and os.path.getmtime(f) > time.time() - 300]
    
    logger.info(f"Found {len(recent_media_files)} recent media files in upload directory")
    return recent_media_files

def attempt_yt_dlp_download(url: str, shortcode: str) -> bool:
    """Attempt to download using yt-dlp if available"""
    try:
        import subprocess
        
        output_template = os.path.join(UPLOAD_DIRECTORY, f"instagram_{shortcode}")
        
        # Check if yt-dlp is installed
        try:
            subprocess.run(["yt-dlp", "--version"], check=True, capture_output=True)
            ytdlp_installed = True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("yt-dlp not installed, skipping this download method")
            return False
            
        if ytdlp_installed:
            logger.info("Attempting download with yt-dlp")
            
            # Run yt-dlp to download the video
            cmd = [
                "yt-dlp",
                "--no-warnings",
            ]
            
            # Add more verbose output if debug mode is enabled
            if INSTAGRAM_DEBUG:
                cmd.remove("--no-warnings")
                cmd.append("-v")
            else:
                cmd.append("--quiet")
                
            cmd.extend([
                "-o", f"{output_template}.%(ext)s",
                url
            ])
            
            logger.info(f"Running yt-dlp command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("yt-dlp download successful")
                if INSTAGRAM_DEBUG and result.stdout:
                    logger.debug(f"yt-dlp output: {result.stdout}")
                return True
            else:
                logger.warning(f"yt-dlp download failed with code {result.returncode}")
                if result.stderr:
                    logger.warning(f"yt-dlp error: {result.stderr}")
                return False
    except Exception as e:
        logger.error(f"Error in yt-dlp download attempt: {str(e)}")
        logger.error(traceback.format_exc())
        return False
        
    return False

def attempt_alternative_download(url: str, shortcode: str) -> bool:
    """Alternative download method using direct API/requests approach"""
    try:
        # Use requests to get the video URL directly
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }
        
        logger.info(f"Starting alternative download for Instagram URL: {url}")
        
        # Try to use session cookies from instaloader if available
        cookies = {}
        try:
            session_file = os.path.join(os.path.dirname(__file__), "instagram_session")
            if os.path.exists(session_file):
                logger.info("Attempting to extract cookies from Instagram session file")
                with open(session_file, 'r') as f:
                    session_content = f.read()
                    # Extract sessionid from session file
                    if 'sessionid' in session_content:
                        sessionid_match = re.search(r'"sessionid":\s*"([^"]+)"', session_content)
                        if sessionid_match:
                            cookies['sessionid'] = sessionid_match.group(1)
                            logger.info("Extracted sessionid from session file")
                    
                    # Extract csrf token from session file if available
                    if 'csrftoken' in session_content:
                        csrf_match = re.search(r'"csrftoken":\s*"([^"]+)"', session_content)
                        if csrf_match:
                            cookies['csrftoken'] = csrf_match.group(1)
                            headers['X-CSRFToken'] = csrf_match.group(1)
                            logger.info("Extracted csrftoken from session file")
                    
                    # Extract ds_user_id from session file if available
                    if 'ds_user_id' in session_content:
                        user_id_match = re.search(r'"ds_user_id":\s*"([^"]+)"', session_content)
                        if user_id_match:
                            cookies['ds_user_id'] = user_id_match.group(1)
                            logger.info("Extracted ds_user_id from session file")
        except Exception as e:
            logger.error(f"Error extracting cookies from session file: {str(e)}")
            # Continue without cookies
        
        # First try using embed URL which sometimes works without login
        embed_url = f"https://www.instagram.com/p/{shortcode}/embed/"
        logger.info(f"Attempting to fetch embed URL: {embed_url}")
        
        response = requests.get(embed_url, headers=headers, cookies=cookies, timeout=10)
        html_content = response.text
        
        if response.status_code != 200:
            # Fall back to original URL if embed fails
            logger.warning(f"Failed to get Instagram embed page: {response.status_code}")
            logger.info(f"Attempting to fetch main post URL: {url}")
            response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
            html_content = response.text
            
            if response.status_code != 200:
                logger.warning(f"Failed to get Instagram page: {response.status_code}")
                return False
        
        # Save HTML for debugging if enabled
        if INSTAGRAM_DEBUG:
            debug_html_path = os.path.join(UPLOAD_DIRECTORY, f"instagram_debug_{shortcode}.html")
            with open(debug_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.debug(f"Saved Instagram HTML for debugging to: {debug_html_path}")
        
        # Look for video URL patterns in the HTML
        video_url = extract_video_url(html_content)
                
        if not video_url:
            # If no video URL found, try using API if we have cookies
            if cookies and 'sessionid' in cookies:
                logger.info("Attempting to use Instagram API to get video URL")
                api_video_url = get_video_url_from_api(shortcode, cookies, headers)
                if api_video_url:
                    video_url = api_video_url
        
        if not video_url:
            # Final attempt - try the OEmbed API which sometimes works without auth
            oembed_url = f"https://api.instagram.com/oembed/?url=https://www.instagram.com/p/{shortcode}/"
            try:
                oembed_response = requests.get(oembed_url, headers=headers, timeout=10)
                if oembed_response.status_code == 200:
                    oembed_data = oembed_response.json()
                    # Extract URL from thumbnail URL by getting the post page
                    if 'thumbnail_url' in oembed_data:
                        logger.info(f"Found thumbnail URL in OEmbed response: {oembed_data['thumbnail_url']}")
                        # Use the thumbnail for now if we can't get the video
                        img_response = requests.get(oembed_data['thumbnail_url'], headers=headers, stream=True, timeout=30)
                        if img_response.status_code == 200:
                            output_path = os.path.join(UPLOAD_DIRECTORY, f"instagram_{shortcode}.jpg")
                            with open(output_path, 'wb') as f:
                                for chunk in img_response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            logger.info(f"Downloaded thumbnail image as fallback to: {output_path}")
                            return True
            except Exception as e:
                logger.error(f"Error fetching OEmbed data: {str(e)}")
        
        if not video_url:
            logger.warning("Could not extract video URL from Instagram page")
            return False
            
        # Download the video
        logger.info(f"Attempting to download video from URL: {video_url}")
        video_response = requests.get(video_url, headers=headers, stream=True, timeout=30)
        
        if video_response.status_code != 200:
            logger.warning(f"Failed to download video: {video_response.status_code}")
            return False
            
        # Save the video
        output_path = os.path.join(UPLOAD_DIRECTORY, f"instagram_{shortcode}.mp4")
        with open(output_path, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        logger.info(f"Video downloaded successfully to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Alternative download method failed: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def extract_video_url(html_content):
    """Extract video URL from HTML content using various patterns"""
    import re
    
    # Pattern for video URL in the JSON data
    patterns = [
        r'"video_url":"([^"]*)"',  # Standard pattern
        r'property="og:video" content="([^"]*)"',  # Open Graph pattern
        r'"contentUrl": "([^"]*)"',  # JSON-LD pattern
        r'"contentUrl":"([^"]*)"',  # Alternative JSON-LD format
        r'video_url=([^&]*)',  # URL parameter pattern
        r'"video_versions":\[{"type":([^}]*)"url":"([^"]*)"',  # API response pattern
        r'<source src="([^"]*)" type="video/mp4">',  # HTML5 video tag
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content)
        if matches:
            if isinstance(matches[0], tuple) and len(matches[0]) > 1:
                # Handle the case where the pattern has multiple capture groups
                video_url = matches[0][-1]  # Use the last group which should contain the URL
            else:
                video_url = matches[0]
                
            # Decode escaped JSON string
            video_url = video_url.replace('\\u0026', '&').replace('\\/', '/')
            logger.info(f"Found video URL using pattern: {pattern}")
            return video_url
            
    return None

def get_video_url_from_api(shortcode, cookies, headers):
    """Attempt to get video URL directly from Instagram API"""
    try:
        # First get the media ID from the shortcode
        media_id_url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"
        response = requests.get(media_id_url, headers=headers, cookies=cookies, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"Failed to get media ID: {response.status_code}")
            return None
            
        try:
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                media_id = data['items'][0].get('id')
                logger.info(f"Found media ID: {media_id}")
            else:
                # Try alternate JSON structure
                if 'graphql' in data and 'shortcode_media' in data['graphql']:
                    media_id = data['graphql']['shortcode_media'].get('id')
                    logger.info(f"Found media ID from graphql: {media_id}")
                else:
                    logger.warning("Could not find media ID in API response")
                    return None
        except Exception as e:
            logger.error(f"Error parsing media ID JSON: {str(e)}")
            return None
            
        # Now get the media info which includes video URLs
        info_url = f"https://i.instagram.com/api/v1/media/{media_id}/info/"
        info_response = requests.get(info_url, headers=headers, cookies=cookies, timeout=10)
        
        if info_response.status_code != 200:
            logger.warning(f"Failed to get media info: {info_response.status_code}")
            return None
            
        try:
            info_data = info_response.json()
            if 'items' in info_data and len(info_data['items']) > 0:
                item = info_data['items'][0]
                
                # Find video URL based on item type
                if 'video_versions' in item and len(item['video_versions']) > 0:
                    # Get the highest quality video
                    video_url = item['video_versions'][0]['url']
                    logger.info(f"Found video URL from API: {video_url}")
                    return video_url
                    
                # Check if this is a carousel and has videos
                if 'carousel_media' in item:
                    for carousel_item in item['carousel_media']:
                        if 'video_versions' in carousel_item and len(carousel_item['video_versions']) > 0:
                            video_url = carousel_item['video_versions'][0]['url']
                            logger.info(f"Found video URL from carousel: {video_url}")
                            return video_url
        except Exception as e:
            logger.error(f"Error parsing media info JSON: {str(e)}")
            
        return None
    except Exception as e:
        logger.error(f"Error getting video URL from API: {str(e)}")
        return None

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
async def upload_file(
    file: UploadFile = File(None), 
    url: str = Form(None), 
    use_web_search: str = Form('true'),
    background_tasks: BackgroundTasks = None
):
    try:
        # Convert string 'true'/'false' to boolean
        should_use_web_search = use_web_search.lower() == 'true'
        logger.info(f"Upload request - Use web search: {should_use_web_search}")
        
        if not file and not url:
            raise HTTPException(status_code=400, detail="Either file or URL is required")
        
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
        
        media_path = None
        is_instagram_url = False
        
        # Handle file upload
        if file:
            file_extension = os.path.splitext(file.filename)[1].lower()
            # Normalize extensions by removing the dot if present in the environment variable
            allowed_extensions_env = os.getenv('ALLOWED_FILE_TYPES', 'mp4,mov,avi,jpg,jpeg,png,gif')
            allowed_extensions = [ext.strip().lower() for ext in allowed_extensions_env.split(',')]
            allowed_extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in allowed_extensions]
            
            # Check if the file extension is allowed
            if file_extension not in allowed_extensions:
                raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed types: {', '.join(ext.lstrip('.') for ext in allowed_extensions)}")
            
            media_path = os.path.join(UPLOAD_DIRECTORY, f"upload_{int(time.time())}{file_extension}")
            
            with open(media_path, "wb") as buffer:
                buffer.write(await file.read())
            
            logger.info(f"File uploaded: {media_path}")
        
        # Handle Instagram URL
        elif url:
            if "instagram.com" in url:
                try:
                    media_path = download_instagram_video(url)
                    if not media_path:
                        raise HTTPException(status_code=400, detail="Failed to download media from Instagram")
                    logger.info(f"Instagram media downloaded: {media_path}")
                    is_instagram_url = True
                except Exception as e:
                    logger.error(f"Instagram download error: {str(e)}", exc_info=True)
                    raise HTTPException(status_code=400, detail=f"Error downloading from Instagram: {str(e)}")
            else:
                raise HTTPException(status_code=400, detail="Only Instagram URLs are supported")
        
        # Process the media file based on its type
        if media_path.lower().endswith(('.mp4', '.mov', '.avi')):
            logger.info(f"Processing video: {media_path}")
            # Pass should_use_web_search to process_video
            background_tasks.add_task(process_video, media_path, should_use_web_search)
            # Immediate response for background task
            return JSONResponse(content={"message": "Video processing started. Results will be available shortly.", "status": "processing"}, status_code=202)
        
        elif media_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            logger.info(f"Processing image: {media_path}")
            # Pass should_use_web_search to analyze_image
            image_analysis_results = analyze_image(media_path, should_use_web_search)
            
            # Extract the components from the analysis results
            analysis_result = image_analysis_results.get("analysis_result", "")
            detected_language = image_analysis_results.get("detected_language", "")
            web_search_results = image_analysis_results.get("web_search_results", None)
            
            # Cleanup the media file after processing
            if os.path.exists(media_path):
                os.remove(media_path)
            
            return JSONResponse(content={
                "image_analysis": analysis_result,
                "detected_language": detected_language,
                "web_search_results": web_search_results,
                "models": {
                    "image_analysis": {"name": IMAGE_ANALYSIS_MODEL},
                    "web_search": WEB_SEARCH_MODEL if should_use_web_search and web_search_results else "Not used", 
                    "web_search_enabled": should_use_web_search
                }
            })
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported media type: {media_path}")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_models():
    """Get information about the AI models being used by the application"""
    try:
        return JSONResponse(content={
            "models": {
                "transcription": {
                    "name": TRANSCRIPTION_MODEL,
                    "type": "Audio Transcription",
                    "description": "Used to convert speech to text in videos"
                },
                "fact_check": {
                    "name": FACT_CHECK_MODEL,
                    "type": "Text Analysis",
                    "description": "Used to fact-check transcribed content"
                },
                "image_analysis": {
                    "name": IMAGE_ANALYSIS_MODEL,
                    "type": "Vision",
                    "description": "Used to analyze images for factual claims"
                },
                "web_search": {
                    "name": WEB_SEARCH_MODEL,
                    "type": "Web Search",
                    "description": "Used for real-time web search to verify claims",
                    "enabled": USE_WEB_SEARCH,
                    "context_size": WEB_SEARCH_CONTEXT_SIZE
                }
            },
            "features": {
                "web_search": {
                    "enabled": USE_WEB_SEARCH,
                    "description": "Real-time web search for fact verification"
                }
            },
            "status": "active"
        })
    except Exception as e:
        logger.error(f"Error retrieving model information: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving model information")

@app.post("/fact-check-text")
async def fact_check_text(text: str = Form(...), use_web_search: str = Form('true')):
    try:
        # Convert string 'true'/'false' to boolean
        should_use_web_search = use_web_search.lower() == 'true'
        logger.info(f"Fact-check text request - Use web search: {should_use_web_search}")
        
        # Try to detect language using langdetect
        detected_language = None
        try:
            detected_language = langdetect.detect(text)
            logger.info(f"Detected language for text input: {detected_language}")
        except Exception as e:
            logger.warning(f"Could not detect language: {str(e)}")
            
        # Perform fact-checking on the text, pass flag and context ('text')
        fact_check_html = perform_fact_check(text, detected_language, should_use_web_search, context='text')
        
        # Perform web search if enabled for this request
        web_search_results = None
        if should_use_web_search:
            try:
                # Extract key factual claims from the text
                claims_prompt = f"""
                Based on this text, identify 5 specific factual claims that can be directly verified through web searches.
                Focus on extracting clear, concrete statements that appear in the text.
                
                Format your response as a JSON object with a "claims" field containing an array of strings.
                Example: {{"claims": ["The Eiffel Tower is 330 meters tall", "Barack Obama was the 44th President of the United States", etc.]}}
                
                Important: Formulate each claim as a direct statement (not a question) that can be fact-checked.
                
                Text:
                {text[:2000]}  # Use first 2000 chars to keep context manageable
                """
                
                claims_response = client.chat.completions.create(
                    model=FACT_CHECK_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a skilled fact-checker who can identify specific, verifiable factual claims in text. Extract only clear, concrete claims that can be verified through web searches."},
                        {"role": "user", "content": claims_prompt}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=500
                )
                
                claims_text = claims_response.choices[0].message.content.strip()
                logger.info(f"Generated claims from text: {claims_text}")
                
                # Parse the JSON response
                import json
                try:
                    claims_obj = json.loads(claims_text)
                    factual_claims = claims_obj.get("claims", [])
                    if not factual_claims:
                        logger.warning("No claims extracted from the response")
                        if isinstance(claims_obj, list):
                            factual_claims = claims_obj
                except json.JSONDecodeError as e:
                    # Fallback in case of non-JSON response
                    logger.warning(f"Failed to parse JSON response: {e}")
                    # Try to extract claims using text processing
                    import re
                    claims_pattern = r'"([^"]+)"'
                    factual_claims = re.findall(claims_pattern, claims_text)
                    if not factual_claims:
                        # Another fallback method
                        claims_text = claims_text.replace("{", "").replace("}", "").replace("[", "").replace("]", "").replace("\"", "")
                        lines = [line.strip() for line in claims_text.split("\n") if line.strip() and not line.strip().startswith('{') and not line.strip().startswith('}')]
                        factual_claims = [line for line in lines if line]
                
                logger.info(f"Extracted {len(factual_claims)} claims for web search: {factual_claims}")
                
                # Perform web search for each claim
                web_search_results = []
                for claim in factual_claims[:5]:  # Limit to 5 claims
                    search_result = perform_web_search(claim)
                    if search_result:
                        web_search_results.append(search_result)
                
                logger.info(f"Completed {len(web_search_results)} web searches")
            
            except Exception as e:
                logger.error(f"Error during web search extraction: {str(e)}")
                web_search_results = [{"error": str(e), "search_query": "Error extracting search queries"}]
        
        return JSONResponse(content={
            "fact_check_html": fact_check_html,
            "detected_language": detected_language,
            "web_search_results": web_search_results,
            "models": {
                "fact_check": {"name": FACT_CHECK_MODEL},
                "web_search": WEB_SEARCH_MODEL if should_use_web_search and web_search_results else "Not used",
                "web_search_enabled": should_use_web_search
            }
        })
    except Exception as e:
        logger.error(f"Error fact-checking text: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fact-checking text: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)