import os
import time
import logging
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError, NotFound
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
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        logger.info("Configuring google-generativeai client with API key (from env)")
        genai.configure(api_key=api_key)
        _configured = True
    else:
        logger.warning("GEMINI_API_KEY / GOOGLE_API_KEY is not set in the environment.")

# Initial attempt
configure_client()

def _call_groq_fallback(prompt: str, system_instruction: str = None, json_mode: bool = False) -> str:
    """
    Route the request through the Groq client.
    Adapts the call_gemini interface to groq_client.chat().
    """
    from .groq_client import chat as groq_chat

    sys_prompt = system_instruction or "You are a helpful coding assistant."
    if json_mode:
        sys_prompt += "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation, just JSON."

    logger.info("Routing AI request through Groq provider")
    return groq_chat(system_prompt=sys_prompt, user_prompt=prompt)


def call_gemini(
    prompt: str, 
    system_instruction: str = None, 
    json_mode: bool = False, 
    model_name: str = "gemini-flash-latest",
    timeout: float = 60.0
) -> str:
    """
    Executes a prompt via the configured AI provider.
    Routes to Groq when AI_PROVIDER=groq, otherwise uses Gemini with fallback to Groq.
    Handles rate-limiting (ResourceExhausted), timeout configurations, and retries.
    Collects performance telemetry safely.
    """
    # ── Check if Groq is the primary provider ──
    ai_provider = os.environ.get("AI_PROVIDER", "gemini").strip().lower()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()

    if ai_provider == "groq" and groq_key:
        telemetry.total_calls += 1
        start_time = time.time()
        try:
            result = _call_groq_fallback(prompt, system_instruction, json_mode)
            telemetry.successful_calls += 1
            telemetry.total_processing_time += (time.time() - start_time)
            return result
        except Exception as e:
            telemetry.failed_calls += 1
            telemetry.total_processing_time += (time.time() - start_time)
            logger.error(f"Groq provider failed: {e}")
            raise Exception(f"Groq AI call failed: {e}")

    # ── Gemini path (original) ──
    global _configured
    if not _configured:
        configure_client()
        
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        # No Gemini key — try Groq as last resort
        if groq_key:
            logger.warning("No Gemini API key found, falling back to Groq")
            telemetry.total_calls += 1
            start_time = time.time()
            try:
                result = _call_groq_fallback(prompt, system_instruction, json_mode)
                telemetry.successful_calls += 1
                telemetry.total_processing_time += (time.time() - start_time)
                return result
            except Exception as e:
                telemetry.failed_calls += 1
                telemetry.total_processing_time += (time.time() - start_time)
                raise Exception(f"Groq fallback failed: {e}")
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is missing.")

    generation_config = {}
    if json_mode:
        generation_config["response_mime_type"] = "application/json"

    active_model = os.environ.get("GEMINI_MODEL") or model_name
    candidate_models = [active_model]
    for fallback in ["gemini-flash-latest", "gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-pro"]:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    max_retries = 3
    base_delay = 2.0
    
    start_time = time.time()
    telemetry.total_calls += 1

    last_error = None
    for model_candidate in candidate_models:
        model = genai.GenerativeModel(
            model_name=model_candidate,
            system_instruction=system_instruction,
            generation_config=generation_config
        )
        for attempt in range(max_retries):
            try:
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
                last_error = api_err
                if isinstance(api_err, NotFound):
                    logger.warning(f"Model {model_candidate} returned 404 NotFound, trying next candidate...")
                    break
                telemetry.retries += 1
                if attempt == max_retries - 1:
                    break
                delay = base_delay * (2.0 ** attempt)
                if isinstance(api_err, ResourceExhausted):
                    logger.warning(f"Rate limited (429 ResourceExhausted). Backing off for {delay + 3.0}s...")
                    time.sleep(delay + 3.0)
                else:
                    logger.warning(f"API Call Error. Retrying in {delay}s...")
                    time.sleep(delay)
            except Exception as e:
                last_error = e
                if isinstance(e, NotFound):
                    logger.warning(f"Model {model_candidate} returned 404 NotFound, trying next candidate...")
                    break
                telemetry.retries += 1
                if attempt == max_retries - 1:
                    break
                delay = base_delay * (2.0 ** attempt)
                logger.warning(f"Unexpected error: {str(e)}. Retrying in {delay}s...")
                time.sleep(delay)

    # ── All Gemini models failed — try Groq as last resort ──
    if groq_key:
        logger.warning("All Gemini models failed. Falling back to Groq provider...")
        try:
            result = _call_groq_fallback(prompt, system_instruction, json_mode)
            telemetry.successful_calls += 1
            telemetry.total_processing_time += (time.time() - start_time)
            return result
        except Exception as groq_err:
            logger.error(f"Groq fallback also failed: {groq_err}")

    telemetry.failed_calls += 1
    telemetry.total_processing_time += (time.time() - start_time)
    logger.error(f"Gemini API error occurred on final attempt: {str(last_error)}")
    raise Exception(f"Gemini API call failed: {str(last_error)}")

