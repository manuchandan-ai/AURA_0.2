import os
import json
import logging
from dotenv import load_dotenv
from openai import OpenAI
from groq import Groq

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AURA-Router")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY is not set in .env — Groq engine will be unavailable, falling back to Ollama only.")

groq_client = None
ACTIVE_GROQ_MODEL = None

if GROQ_API_KEY.startswith("gsk_"):
    try:
        groq_client = Groq(api_key=GROQ_API_KEY, timeout=12.0)
        models_data = groq_client.models.list()
        available_ids = [m.id for m in models_data.data]
        logger.info(f"Available Groq models on your key: {available_ids}")

        # Targeted preference matching your exact key entitlements:
        preference = [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b",
            "allam-2-7b"
        ]

        for pref in preference:
            if pref in available_ids:
                ACTIVE_GROQ_MODEL = pref
                break

        logger.info(f"Selected Groq Model: {ACTIVE_GROQ_MODEL}")

    except Exception as e:
        logger.warning(f"Could not initialize Groq client: {e}")
        groq_client = None

# Fallback: Ollama Local
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    timeout=45.0
)
OLLAMA_MODEL = "llama3.2:3b"

def run_llm_with_failover(messages: list, json_mode: bool = False) -> tuple[str, str]:
    # 1. Attempt Groq Cloud
    if groq_client and ACTIVE_GROQ_MODEL:
        try:
            logger.info(f"Executing via Primary Engine (Groq Cloud: {ACTIVE_GROQ_MODEL})...")
            kwargs = {
                "model": ACTIVE_GROQ_MODEL,
                "messages": messages,
                "temperature": 0.2 if json_mode else 0.7
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = groq_client.chat.completions.create(**kwargs)
            return response.choices[0].message.content, f"Groq ({ACTIVE_GROQ_MODEL})"

        except Exception as primary_error:
            logger.warning(f"Groq Cloud failed: {primary_error}. Attempting Ollama fallback...")

    # 2. Attempt Ollama Local Fallback
    try:
        logger.info("Executing via Fallback Engine (Ollama Local)...")
        kwargs = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "temperature": 0.2 if json_mode else 0.7
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        fallback_response = ollama_client.chat.completions.create(**kwargs)
        return fallback_response.choices[0].message.content, "Ollama (Local Fallback)"

    except Exception as fallback_error:
        logger.error(f"Both engines failed. Ollama error: {fallback_error}")
        raise RuntimeError(
            f"All AI engines failed. Check your GROQ_API_KEY or ensure Ollama is running. "
            f"Details: {fallback_error}"
        )