import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve API Key and Base URL for the cloud provider
API_KEY = os.getenv("OLLAMA_API_KEY")
BASE_URL = os.getenv("OLLAMA_BASE_URL")

if not API_KEY or not BASE_URL:
    raise ValueError("OLLAMA_API_KEY or OLLAMA_BASE_URL is not set. Please check your .env file.")

# You can initialize your preferred client here (e.g., the OpenAI client pointing to the Ollama endpoint)
# from openai import OpenAI
# client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# Define the best coding models available on Ollama cloud providers
CODING_MODELS = {
    "qwen_coder_30b": "qwen3-coder:30b",
    "gemma_12b": "gemma4:12b",
    "devstral_24b": "devstral:24b"
}

# Default API Configuration Parameters
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 4096
