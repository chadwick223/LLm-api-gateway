import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve API Key
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set. Please check your .env file.")

# Define the best free-tier coding models based on current availability
CODING_MODELS = {
    # Gemini 3 Flash is currently the go-to for free tier coding tasks (1M context window)
    "gemini_flash": "gemini-3-flash",
    "gemini_flash_lite": "gemini-3.1-flash-lite"
}

# Default Configuration Parameters
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TOP_P = 0.95
