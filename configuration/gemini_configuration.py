import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve API Key
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set. Please check your .env file.")

# Define the best coding models based on current availability
CODING_MODELS = {
    "gemini_3_1_flash_lite": "gemini-3.1-flash-lite",
    "gemini_3_6_flash": "gemini-3.6-flash",
}

# Default Configuration Parameters
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.95
