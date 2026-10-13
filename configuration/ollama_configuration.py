import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Retrieve API Key and Base URL (defaults to standard local Ollama endpoint)
API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")
BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# Initialize OpenAI client pointed to Ollama OpenAI-compatible endpoint
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)

# Verified models available on Ollama library (ollama.com/library)
CODING_MODELS = {
    "gemma4_31b": "gemma4:31b",
    "gpt_oss_120b": "gpt-oss:120b",
    "gpt_oss_20b": "gpt-oss:20b",
}

# Default API Configuration Parameters
DEFAULT_TEMPERATURE = 0.2
