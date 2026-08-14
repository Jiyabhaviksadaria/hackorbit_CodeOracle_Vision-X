import os
import time
import logging
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger("codeoracle.gemini_client")
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

class GeminiTelemetry:
    def __init__(self):
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.retries = 0
        self.total_processing_time = 0.0

    def reset(self):
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.retries = 0
        self.total_processing_time = 0.0

    def to_dict(self):
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "retries": self.retries,
            "total_processing_time": round(self.total_processing_time, 3)
        }

# Global singleton telemetry instance
telemetry = GeminiTelemetry()

_configured = False

def configure_client():
    global _configured
    # Try loading GEMINI_API_KEY from environment or dotenv
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        # Prevent key leakage in logs
        logger.info("Configuring google-generativeai client with GEMINI_API_KEY (from env)")
        genai.configure(api_key=api_key)
        _configured = True
    else:
        logger.warning("GEMINI_API_KEY is not set in the environment.")

# Initial attempt
configure_client()

def call_gemini(
    prompt: str, 
    system_instruction: str = None, 
    json_mode: bool = False, 
    model_name: str = "gemini-flash-latest",
    timeout: float = 60.0
) -> str:
    """
    Executes a prompt via the Gemini API.
    Handles rate-limiting (ResourceExhausted), timeout configurations, and retries.
    Collects performance telemetry safely.
    """
    global _configured
    if not _configured:
        configure_client()
        
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing. Please set it in your .env file.")

    generation_config = {}
    if json_mode:
        generation_config["response_mime_type"] = "application/json"

    # Set up the model
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_instruction,
        generation_config=generation_config
    )

    max_retries = 3
    base_delay = 2.0
    
    start_time = time.time()
    telemetry.total_calls += 1

    for attempt in range(max_retries):
        try:
            # Set request-level timeout
            response = model.generate_content(
                prompt,
                request_options={"timeout": timeout}
            )
            
            if response and response.text:
                duration = time.time() - start_time
                telemetry.total_processing_time += duration
                telemetry.successful_calls += 1
                return response.text
            
            raise ValueError("Gemini API returned an empty response string.")

        except (ResourceExhausted, GoogleAPICallError) as api_err:
            telemetry.retries += 1
            if attempt == max_retries - 1:
                telemetry.failed_calls += 1
                telemetry.total_processing_time += (time.time() - start_time)
                logger.error(f"Gemini API error occurred on final attempt: {str(api_err)}")
                raise Exception(f"Gemini API call failed: {str(api_err)}")
            
            # Backoff is longer if rate-limited
            delay = base_delay * (2.0 ** attempt)
            if isinstance(api_err, ResourceExhausted):
                logger.warning(f"Rate limited (429 ResourceExhausted). Backing off for {delay + 2.0}s...")
                time.sleep(delay + 2.0)
            else:
                logger.warning(f"API Call Error. Retrying in {delay}s...")
                time.sleep(delay)
                
        except Exception as e:
            telemetry.retries += 1
            if attempt == max_retries - 1:
                telemetry.failed_calls += 1
                telemetry.total_processing_time += (time.time() - start_time)
                logger.error(f"Unexpected error occurred on final attempt: {str(e)}")
                raise Exception(f"Gemini API call failed with unexpected error: {str(e)}")
            
            delay = base_delay * (2.0 ** attempt)
            logger.warning(f"Unexpected error: {str(e)}. Retrying in {delay}s...")
            time.sleep(delay)
