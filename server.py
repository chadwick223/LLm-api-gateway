import os
import sys
import time
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Ensure project root is in path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from routing.agent import CodingAgent
from configuration.key_pool import KeyPoolManager, save_provider_keys
from configuration.rate_limiter import RateLimiterManager
from configuration.usage_store import UsageStoreManager
from configuration.limits import get_provider_limits, PROVIDER_LIMITS
from configuration.database import SessionLocal, CallRecord
from configuration.token_estimation import estimate_token
from models.easy_models import create_client_for_provider

# Global singletons
agent_instance: Optional[CodingAgent] = None
key_pool = KeyPoolManager()
usage_store = UsageStoreManager()
rate_limiter = RateLimiterManager(key_pool, usage_store)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_instance
    print("=" * 60)
    print("Initializing Gateway Backend...")
    print("Loading BGE Semantic Router into memory (one-time initialization)...")
    agent_instance = CodingAgent()
    print("BGE Semantic Router loaded and warm in memory.")
    print("Gateway Backend is ready to serve requests.")
    print("=" * 60)
    yield
    print("Shutting down Gateway Backend.")

app = FastAPI(
    title="Coding Agent LLM Gateway API",
    description="Intelligent API Gateway with Semantic Routing and Multi-Key Pool Management",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Request / Response Models -----------------

class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User prompt or coding question")

class UpdateKeysRequest(BaseModel):
    provider: str
    keys: List[str]
    extra: Optional[Dict[str, str]] = None

class TestKeyRequest(BaseModel):
    provider: str
    key: str
    extra: Optional[Dict[str, str]] = None

# ----------------- API Endpoints -----------------

@app.get("/api/health")
def health_check():
    return {
        "status": "ready" if agent_instance is not None else "loading",
        "model": "BAAI/bge-small-en-v1.5",
        "timestamp_ms": int(time.time() * 1000)
    }

@app.post("/api/chat")
def handle_chat(req: ChatRequest):
    if agent_instance is None:
        raise HTTPException(status_code=503, detail="Coding agent is still warming up. Please retry shortly.")

    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    try:
        # Run agent with metadata details
        result = agent_instance.run(prompt, return_details=True)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

@app.get("/api/keys")
def get_key_configuration():
    key_pool.reload_keys()
    providers = ["groq", "gemini", "cloudflare", "nvidia", "ollama"]
    status_by_provider = {}

    current_time_ms = int(time.time() * 1000)
    one_day_ago = current_time_ms - (24 * 60 * 60 * 1000)
    one_minute_ago = current_time_ms - (60 * 1000)

    for prov in providers:
        keys = key_pool.get_keys(prov)
        prov_limits = get_provider_limits(prov) or {"rpm": 0, "rpd": 0, "tpd": 0}

        key_items = []
        for idx, key in enumerate(keys):
            cooldown_rem = key_pool.get_cooldown_remaining(prov, idx)
            rpm_used = usage_store.count_calls_since(prov, idx, one_minute_ago)
            rpd_used = usage_store.count_calls_since(prov, idx, one_day_ago)
            tpd_used = usage_store.count_tokens_since(prov, idx, one_day_ago)

            key_items.append({
                "index": idx,
                "masked": key_pool.mask_key(key),
                "is_cooling": cooldown_rem > 0,
                "cooldown_remaining_sec": cooldown_rem,
                "rpm_used": rpm_used,
                "rpd_used": rpd_used,
                "tpd_used": tpd_used
            })

        extra_info = {}
        if prov == "cloudflare":
            extra_info["account_id"] = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
        elif prov == "ollama":
            extra_info["base_url"] = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/v1")

        status_by_provider[prov] = {
            "provider": prov,
            "total_keys": len(keys),
            "keys": key_items,
            "limits": prov_limits,
            "extra": extra_info,
            "has_available": len(key_pool.available_indexes(prov)) > 0
        }

    return {
        "providers": status_by_provider,
        "database_connected": os.getenv("DATABASE_URL") is not None
    }

@app.post("/api/keys")
def update_provider_key_pool(req: UpdateKeysRequest):
    provider = req.provider.lower().strip()
    valid_providers = ["groq", "gemini", "cloudflare", "nvidia", "ollama"]
    if provider not in valid_providers:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")

    clean_keys = [k.strip() for k in req.keys if k and k.strip()]
    extra_vars = {}

    if req.extra:
        if provider == "cloudflare" and "account_id" in req.extra:
            extra_vars["CLOUDFLARE_ACCOUNT_ID"] = req.extra["account_id"]
        elif provider == "ollama" and "base_url" in req.extra:
            extra_vars["OLLAMA_BASE_URL"] = req.extra["base_url"]

    success = save_provider_keys(provider=provider, keys=clean_keys, extra_vars=extra_vars)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save keys to configuration.")

    key_pool.reload_keys()

    return {
        "status": "success",
        "provider": provider,
        "updated_keys_count": len(clean_keys)
    }

@app.post("/api/keys/test")
def test_provider_key(req: TestKeyRequest):
    provider = req.provider.lower().strip()
    test_key = req.key.strip()

    if not test_key:
        raise HTTPException(status_code=400, detail="No key provided for testing.")

    # Temporarily set extra env variables if testing Cloudflare
    if provider == "cloudflare" and req.extra and "account_id" in req.extra:
        os.environ["CLOUDFLARE_ACCOUNT_ID"] = req.extra["account_id"]

    try:
        client = create_client_for_provider(provider, test_key)
        # Attempt a lightweight listing or minimal token test
        if provider == "groq":
            models = client.models.list()
            return {"valid": True, "message": "Groq API key verified successfully! Available models found."}
        elif provider == "gemini":
            models = client.models.list()
            return {"valid": True, "message": "Gemini API key verified successfully!"}
        elif provider == "nvidia":
            models = client.models.list()
            return {"valid": True, "message": "NVIDIA NIM API key verified successfully!"}
        elif provider == "cloudflare":
            models = client.models.list()
            return {"valid": True, "message": "Cloudflare Workers AI key & Account ID verified successfully!"}
        elif provider == "ollama":
            models = client.models.list()
            return {"valid": True, "message": "Ollama connection verified successfully!"}
        else:
            return {"valid": True, "message": "Key accepted."}
    except Exception as e:
        return {"valid": False, "message": f"Verification failed: {str(e)}"}

@app.get("/api/metrics")
def get_gateway_metrics(limit: int = 50):
    session = SessionLocal()
    try:
        total_calls = session.query(CallRecord).count()
        ok_calls = session.query(CallRecord).filter(CallRecord.status == "ok").count()
        error_calls = session.query(CallRecord).filter(CallRecord.status == "error").count()

        current_time_ms = int(time.time() * 1000)
        one_day_ago = current_time_ms - (24 * 60 * 60 * 1000)
        today_calls = session.query(CallRecord).filter(CallRecord.ts >= one_day_ago).count()

        records = session.query(CallRecord).order_by(CallRecord.ts.desc()).limit(limit).all()

        call_logs = []
        for r in records:
            call_logs.append({
                "id": r.id,
                "ts": r.ts,
                "provider": r.provider,
                "key_index": r.key_index,
                "model_name": r.model_name,
                "endpoint": r.endpoint,
                "status": r.status,
                "http_status": r.http_status,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens
            })

        return {
            "summary": {
                "total_calls": total_calls,
                "today_calls": today_calls,
                "ok_calls": ok_calls,
                "error_calls": error_calls
            },
            "recent_calls": call_logs
        }
    finally:
        session.close()

# ----------------- Serve Frontend Static Files -----------------

frontend_dir = os.path.join(project_root, "frontend")

@app.get("/")
def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Gateway API running. frontend/index.html not found."}

@app.get("/{full_path:path}")
def serve_static_or_spa(full_path: str):
    # Prevent intercepting /api routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    
    target_file = os.path.join(frontend_dir, full_path)
    if os.path.isfile(target_file):
        return FileResponse(target_file)
    
    # Fallback to index.html for SPA routing
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="File not found")

def start_server(host: str = "127.0.0.1", port: int = 8080):
    import uvicorn
    print(f"Starting server on http://{host}:{port} ...")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    port_to_use = int(os.getenv("PORT", "8080"))
    start_server(port=port_to_use)


