import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Retrieve API Key for NVIDIA NIM
API_KEY = os.getenv("NVIDIA_API_KEY")

if not API_KEY:
    raise ValueError("NVIDIA_API_KEY is not set. Please check your .env file.")

# NVIDIA NIM OpenAI-compatible endpoint
BASE_URL = "https://integrate.api.nvidia.com/v1"

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)

# Verified NVIDIA Nemotron-3 models hosted on build.nvidia.com
CODING_MODELS = {
    "nemotron_3_super_120b": "nvidia/nemotron-3-super-120b-a12b",
    "nemotron_3_ultra_550b": "nvidia/nemotron-3-ultra-550b-a55b",
    "nemotron_3_nano_omni_30b": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
}

# Default API Configuration Parameters
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.95
