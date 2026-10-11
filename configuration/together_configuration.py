import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Retrieve API Key
API_KEY = os.getenv("TOGETHER_API_KEY")

if not API_KEY:
    raise ValueError("TOGETHER_API_KEY is not set. Please check your .env file.")

# Initialize the client pointing to Together's base URL
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.together.xyz/v1",
)

# Define the best coding models available on Together AI's serverless endpoints
CODING_MODELS = {
    "glm_5_3": "glm-5.3",
    "deepseek_flash": "deepseek-v4-flash-0731",
    "kimi_k3": "kimi-k3",
    "qwen_9b": "qwen3.5-9b"
}

# Default API Configuration Parameters
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TOP_P = 1.0
