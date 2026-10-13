import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Cloudflare requires both an API Key (Token) and Account ID
API_KEY = os.getenv("CLOUDFLARE_API_KEY")
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")

if not API_KEY:
    raise ValueError("CLOUDFLARE_API_KEY is not set. Please check your .env file.")

if not ACCOUNT_ID:
    raise ValueError("CLOUDFLARE_ACCOUNT_ID is not set. Please check your .env file.")

# OpenAI-compatible Cloudflare Workers AI base URL
BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/v1"

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)

# Verified Cloudflare Workers AI model identifiers
CODING_MODELS = {
    "qwen_2_5_coder_32b": "@cf/qwen/qwen2.5-coder-32b-instruct",
    "gpt_oss_120b": "@cf/openai/gpt-oss-120b",
    "qwen3_30b": "@cf/qwen/qwen3-30b-a3b-fp8",
    "glm_4_7_flash": "@cf/zai-org/glm-4.7-flash",
}

DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.95
