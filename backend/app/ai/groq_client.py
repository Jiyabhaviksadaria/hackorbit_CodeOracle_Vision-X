"""
Groq API client — shared by all AI/ML stages.
Owned by API/Integration Engineer (client setup).
AI/ML Engineer owns the prompt logic in explainer.py, test_gen.py, refactor.py.

Reads GROQ_API_KEY and GROQ_MODEL from environment (never hardcoded).
Provides retry/backoff per RULES.md requirements.
"""
import os
import time
import logging
from typing import Optional
from groq import Groq, RateLimitError, APIConnectionError, APIStatusError

logger = logging.getLogger(__name__)

# ── Config from env ──────────────────────────────────────────────────
_API_KEY = os.getenv("GROQ_API_KEY")
_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Max tokens per request — keeps context bounded per RULES.md
_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "4096"))

# Retry settings
_MAX_RETRIES   = 2
_RETRY_DELAY_S = 3.0


def get_client() -> Groq:
    """
    Return a configured Groq client.
    Raises RuntimeError if GROQ_API_KEY is not set.
    """
    api_key = os.getenv("GROQ_API_KEY")  # read fresh — dotenv may load after import
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to backend/.env — "
            "see .env.example for the format."
        )
    return Groq(api_key=api_key)


def chat(
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.2,
) -> str:
    """
    Send a chat completion request to Groq with retry/backoff.

    Per RULES.md:
      - Single provider, single call path
      - Retry once on rate-limit/connection error, then raise gracefully
      - Never dump unbounded context — caller must chunk large inputs

    Args:
        system_prompt: Sets the AI role/behaviour.
        user_prompt:   The actual task content (chunked by caller).
        model:         Override model (defaults to GROQ_MODEL env var).
        max_tokens:    Override token limit (defaults to GROQ_MAX_TOKENS).
        temperature:   Sampling temperature — low = more deterministic.

    Returns:
        Assistant response string.

    Raises:
        RuntimeError: If all retries fail or key is missing.
    """
    client     = get_client()
    use_model  = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    use_tokens = max_tokens or int(os.getenv("GROQ_MAX_TOKENS", "4096"))

    last_error: Optional[Exception] = None

    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=use_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                max_tokens=use_tokens,
                temperature=temperature,
            )
            content = response.choices[0].message.content
            if not content or not content.strip():
                raise ValueError("Empty response from Groq — will retry")
            return content.strip()

        except RateLimitError as e:
            last_error = e
            logger.warning("Groq rate limit hit (attempt %d/%d)", attempt + 1, _MAX_RETRIES + 1)
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY_S * (attempt + 1))

        except APIConnectionError as e:
            last_error = e
            logger.warning("Groq connection error (attempt %d/%d): %s", attempt + 1, _MAX_RETRIES + 1, e)
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY_S)

        except APIStatusError as e:
            last_error = e
            logger.error("Groq API error %d: %s", e.status_code, e.message)
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY_S)

        except ValueError as e:
            last_error = e
            logger.warning("Empty Groq response (attempt %d/%d)", attempt + 1, _MAX_RETRIES + 1)
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY_S)

        except Exception as e:
            last_error = e
            logger.error("Unexpected Groq error: %s", e)
            break

    raise RuntimeError(
        f"Groq request failed after {_MAX_RETRIES + 1} attempts: {last_error}"
    )
