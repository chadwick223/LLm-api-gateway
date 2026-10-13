import os

from dotenv import load_dotenv

from groq import Groq

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY is not set. Please check your .env file.")



CODING_MODELS = {
    "gpt_120b": "openai/gpt-oss-120b",
    "qwen_27b": "qwen-3.8-27b",
    "gpt_20b": "openai/gpt-oss-20b"
}

DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.95
