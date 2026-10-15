# Aegis — Intelligent LLM API Gateway & Autonomous Coding Agent

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Semantic Router](https://img.shields.io/badge/Router-BGE--small--en--v1.5-orange.svg)](https://huggingface.co/BAAI/bge-small-en-v1.5)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%2F%20Neon-336791.svg?logo=postgresql)](https://neon.tech)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Aegis** is a resilient, production-ready LLM API Gateway and autonomous coding assistant. It combines **local semantic intent routing** (via sub-50ms vector embeddings), **multi-provider model cascades** (Cloudflare Workers AI, Google Gemini, NVIDIA NIM, Ollama, and Groq), **3-layer hybrid token estimation**, **automated multi-key round-robin rotation with 429 cooldowns**, and **real-time telemetry persistence** into a single cohesive system with a warm linen SPA dashboard.

---

## Visual Overview

![Aegis Agent Playground](assets/screenshots/agent_playground.png)

---

## Table of Contents

- [Core Capabilities](#core-capabilities)
- [System Architecture](#system-architecture)
- [Semantic Complexity Routing (Easy vs. Medium)](#semantic-complexity-routing-easy-vs-medium)
- [Multi-Provider Model Cascades](#multi-provider-model-cascades)
- [Token Estimation Architecture](#token-estimation-architecture)
- [Key Pooling, Rate Limiting & Cooldowns](#key-pooling-rate-limiting--cooldowns)
- [Database Telemetry & Wire Status Capture](#database-telemetry--wire-status-capture)
- [Interactive Web Dashboard](#interactive-web-dashboard)
- [Annotated Project Directory Tree](#annotated-project-directory-tree)
- [Developer Customization Guide](#developer-customization-guide)
- [Local Setup & Getting Started](#local-setup--getting-started)
- [Testing & Verification Suite](#testing--verification-suite)

---

## Core Capabilities

1. **Local Semantic Intent Routing**: Classifies incoming tasks as **Easy** or **Medium** in under 50ms using `BAAI/bge-small-en-v1.5` embeddings, keeping operational cost at zero and bypassing expensive LLM classification hops.
2. **Multi-Provider Failover Cascades**: Automatically traverses priority-ordered candidate models across Cloudflare, Gemini, NVIDIA, Ollama, and Groq until an available model with adequate context capacity and valid quota is found.
3. **Pre-Flight Context Safeguards**: Evaluates input prompt token counts before making network calls. If a prompt's tokens exceed a model's maximum generation output capacity, the model is safely bypassed.
4. **Resilient Key Rotation & Cooldowns**: Supports comma-delimited API key pools in `.env`. When an API key hits an HTTP 429 (Rate Limit), it is automatically placed in a 60-second cooldown while the gateway seamlessly retries with the next key.
5. **Multi-Dimensional Rate Limiting**: Tracks Requests Per Minute (RPM), Requests Per Day (RPD), and Tokens Per Day (TPD) against a sliding time window.
6. **Telemetry & Live Metrics**: Captures true wire HTTP status codes, latency, prompt tokens, and completion tokens in a Neon PostgreSQL database (with automatic SQLite fallback).
7. **Vanilla Modular Web UI**: A zero-build-tooling single-page application built with clean ES Modules and CSS tokens styled with a warm linen aesthetic.

---

## System Architecture

```mermaid
flowchart TD
    User([User Prompt / API Client]) --> Gateway[FastAPI Server / CLI Entrypoint]
    
    subgraph Routing ["1. Semantic Routing Layer"]
        Gateway --> IntentExtract[Head/Tail Prompt Condenser]
        IntentExtract --> BGE[BAAI/bge-small-en-v1.5 Local Embeddings]
        BGE --> Classifier{SemanticRouter\nThreshold = 0.60}
        Classifier -->|Score >= 0.60 & Easy| EasyPool[Easy Candidate Pool]
        Classifier -->|Score >= 0.60 & Medium| MediumPool[Medium Candidate Pool]
        Classifier -->|Uncertain / No Match| MediumPool
    end

    subgraph Estimation ["2. Token Estimation Layer"]
        EasyPool & MediumPool --> TokenEst[3-Layer Token Estimator]
        TokenEst --> CheckLen{Prompt Length}
        CheckLen -->|<= 60,000 Chars| TiktokenBPE[Exact BPE: cl100k_base]
        CheckLen -->|> 60,000 Chars| FastHeuristic[Heuristic: 4 chars / token]
    end

    subgraph DecisionEngine ["3. Decision & Failover Engine"]
        TiktokenBPE & FastHeuristic --> CandidateLoop[Iterate Ordered Candidates]
        CandidateLoop --> CapCheck{Estimated Tokens <= Max Output?}
        CapCheck -->|No| SkipModel[Skip Candidate -> Next Model]
        CapCheck -->|Yes| RateCheck{RateLimiter: RPM / RPD / TPD Valid?}
        RateCheck -->|No| SkipKey[Skip Key / Key Cooling]
        RateCheck -->|Yes| Dispatch[Dispatch via Provider Client]
    end

    subgraph Execution ["4. Execution & Key Pool"]
        Dispatch --> CallAPI[LLM API Call]
        CallAPI -->|HTTP 200 OK| RecordUsage[Record Neon DB Metrics]
        CallAPI -->|HTTP 429 RateLimit| Cooldown[KeyPool 60s Cooldown -> Failover Next]
        Cooldown --> CandidateLoop
    end

    RecordUsage --> Response([Client Response + Telemetry])
```

---

## Semantic Complexity Routing (Easy vs. Medium)

Rather than using a heavy LLM or rigid regex patterns to classify user intent, Aegis utilizes **local semantic vector similarity**:

### 1. Vector Model & Speed
- **Model**: `BAAI/bge-small-en-v1.5` loaded into memory at server startup via `semantic-router` and `HuggingFaceEncoder`.
- **Latency**: Sub-50ms vector comparison running on local CPU without sending prompt data to third-party APIs.

### 2. Head/Tail Prompt Condensation (`extract_intent_text`)
When developers send massive prompts (such as entire 1,000-line codebases), vector encoders can exceed their context limits or degrade in semantic accuracy. Aegis handles this through prompt condensation in `routing/layer.py`:

```python
def extract_intent_text(user_prompt: str, char_limit: int = 400) -> str:
    string_length = len(user_prompt)
    max_allowed_length = char_limit * 2
    if string_length <= max_allowed_length:
        return user_prompt
    first_part = user_prompt[:char_limit]
    last_part = user_prompt[-char_limit:]
    return first_part + " ... " + last_part
```
By taking the first 400 characters (the user's initial instruction) and the last 400 characters (their concluding question or constraint), Aegis captures core semantic intent while bounding embedding overhead.

### 3. Utterances & Threshold Calibration
- **Similarity Threshold**: `score_threshold = 0.60`.
- **Easy Utterances**: Focused on lightweight, deterministic tasks:
  - `"fix the formatting"`
  - `"can you fix the formatting of this python file?"`
  - `"add docstrings"`
  - `"add comments to my code"`
  - `"write a regex pattern"`
  - `"find the syntax error"`
  - `"why is there a red underline here"`
  - `"fix the typo"`
  - `"rename this variable"`
- **Medium Utterances**: Focused on architectural and multi-step reasoning:
  - `"refactor this code"`
  - `"implement a retry mechanism"`
  - `"build a caching layer"`
  - `"optimize this function for speed"`
  - `"rewrite this class to be object oriented"`
  - `"create a database schema"`
  - `"add error handling to the entire module"`
- **Safety Fallback**: If the similarity score does not exceed 0.60 for either route, the router safely defaults to **Medium** to ensure complex queries receive sufficient model capacity.

---

## Multi-Provider Model Cascades

Aegis configures distinct candidate pools for Easy and Medium difficulties. Each candidate is tried in strict priority order.

### Easy Candidates Pool (`models/easy_models.py`)

| Priority | Provider | Model Identifier | Context Window | Max Output Tokens | Role / Advantage |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | **Groq** | `openai/gpt-oss-20b` | 131,072 | 8,000 | Ultra-low latency LPU inference for fast answers |
| **2** | **Cloudflare** | `@cf/zai-org/glm-4.7-flash` | 131,072 | 8,192 | Cost-effective edge inference via Workers AI |
| **3** | **Gemini** | `gemini-3.1-flash-lite` | 1,048,576 | 65,536 | Massive 1M context with high generation ceiling |
| **4** | **NVIDIA** | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | 262,144 | 4,096 | Reasoning-specialized compact coding model |
| **5** | **Ollama** | `gpt-oss:20b` | 131,072 | 32,768 | Local / self-hosted fallback |

### Medium Candidates Pool (`models/medium_models.py`)

| Priority | Provider | Model Identifier | Context Window | Max Output Tokens | Role / Advantage |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | **Cloudflare** | `@cf/openai/gpt-oss-120b` | 128,000 | 65,536 | Frontier open model on global edge infrastructure |
| **2** | **Cloudflare** | `@cf/qwen/qwen2.5-coder-32b-instruct` | 32,768 | 32,768 | Specialized code intelligence & instruction following |
| **3** | **Cloudflare** | `@cf/qwen/qwen3-30b-a3b-fp8` | 32,768 | 8,192 | High-throughput FP8 quantized reasoning model |
| **4** | **Gemini** | `gemini-3.6-flash` | 1,048,576 | 65,536 | 1M context powerhouse for large refactorings |
| **5** | **NVIDIA** | `nvidia/nemotron-3-super-120b-a12b` | 1,048,576 | 65,536 | High-capacity enterprise reasoning model |
| **6** | **NVIDIA** | `nvidia/nemotron-3-ultra-550b-a55b` | 1,048,576 | 65,536 | 550B flagship frontier model for heavy logic |
| **7** | **Ollama** | `gpt-oss:120b` | 131,072 | 32,768 | High-capacity local deployment |
| **8** | **Groq** | `openai/gpt-oss-120b` | 131,072 | 8,000 | Accelerated fallback for large models |

---

## Token Estimation Architecture

The token estimation layer lives in `configuration/token_estimation/estimator.py`. It guarantees that incoming prompts are validated, measured, and checked against context constraints before network calls are dispatched.

```
[ User Input ]
      │
      ▼
┌──────────────────────────────────────────────┐
│ Layer 1: Payload Construction                │
│ Creates dictionary: {"message": user_input}  │
└──────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────────┐
│ Layer 2: Message Validation                  │
│ Asserts len(message.strip()) > 0             │
│ (Raises ValueError on empty or whitespace)   │
└──────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────────┐
│ Layer 3: Hybrid Token Calculation            │
│ • If len(text) > 60,000 characters:          │
│   Fast Heuristic: max(1, len(text) // 4)     │
│ • If len(text) <= 60,000 characters:         │
│   Exact BPE via tiktoken ('cl100k_base')     │
└──────────────────────────────────────────────┘
```

### Pre-Flight Model Skipping Rule
Inside `execute_easy_task` and `execute_medium_task`:
```python
max_output_tokens = get_max_output_tokens(provider, model_name)

if estimated_tokens > max_output_tokens:
    print(f"Skipping {provider} ({model_name}): input tokens ({estimated_tokens}) > max output tokens ({max_output_tokens})")
    continue
```
If a prompt requires more tokens than a model's configured generation allowance, the decision engine automatically skips that candidate and advances to a model with higher capacity (e.g., escalating from NVIDIA Nano Omni 4k to Gemini 65k).

---

## Key Pooling, Rate Limiting & Cooldowns

### 1. Comma-Separated Key Rotation
Multiple API keys can be supplied per provider in `configuration/.env` as comma-separated values:
```bash
GROQ_API_KEY="gsk_key1,gsk_key2,gsk_key3"
```
`KeyPoolManager` splits these keys, tracks their active cooldowns, and maintains an internal round-robin rotation pointer. When a request succeeds, the pointer advances to evenly distribute traffic across all configured keys.

### 2. Automated 60-Second Cooldowns
When any provider returns an HTTP 429 (`RateLimitError`), the engine catches the exception, logs the event, and puts that specific key index into cooldown:
```python
key_pool.report_rate_limited(provider=provider, index=key_index, seconds=60)
```
While in cooldown, `is_cooling(provider, index)` returns `True`, and `RateLimiterManager` automatically skips that key index without failing the user's request.

### 3. Multi-Tiered Quota Limits
In `configuration/limits.py`, provider-level defaults and per-model limits govern throughput:

```python
PROVIDER_LIMITS = {
    "groq":       {"rpm": 30,  "rpd": 1000,  "tpd": 200000},
    "gemini":     {"rpm": 15,  "rpd": 1500,  "tpd": 1000000},
    "cloudflare": {"rpm": 300, "rpd": 10000, "tpd": 1000000},
    "nvidia":     {"rpm": 40,  "rpd": 1000,  "tpd": 500000},
    "ollama":     {"rpm": 60,  "rpd": 10000, "tpd": 1000000},
}
```
Before issuing a call, `RateLimiterManager.get_valid_key()` verifies:
1. Calls in the last 60 seconds < `rpm`
2. Calls in the last 24 hours < `rpd`
3. Cumulative tokens consumed in the last 24 hours < `tpd`

### 4. Dynamic In-App Hot-Reloading
New keys can be added directly through the UI or `save_provider_keys()`. The function writes the new keys to `configuration/.env` and triggers `key_pool.reload_keys()` to update the live pool without restarting the server.

---

## Database Telemetry & Wire Status Capture

Every call processed by the gateway records an entry into the `api_calls` table via SQLAlchemy:

```python
class CallRecord(Base):
    __tablename__ = "api_calls"

    id = Column(Integer, primary_key=True, index=True)
    ts = Column(BigInteger, index=True)          # Timestamp (epoch ms)
    provider = Column(String, index=True)        # 'groq', 'cloudflare', etc.
    key_index = Column(Integer, index=True)      # Index of the key used
    model_name = Column(String)                  # Target model string
    endpoint = Column(String)                    # 'chat.completions'
    status = Column(String)                      # 'ok' or 'error'
    http_status = Column(Integer, nullable=True) # Real wire status (200, 429, 500)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
```

### Real Wire HTTP Status Code Extraction
Aegis does not assume every success is 200 or every failure is 500. It extracts real HTTP status codes directly from the provider response:
- **Success**: Uses `with_raw_response` on OpenAI/Groq clients to extract `raw_response.status_code`.
- **Errors**: Inspects `exc.status_code`, `exc.response.status_code`, or maps classified exceptions (e.g. 429 for rate limits, 401 for auth errors).

---

## Interactive Web Dashboard

Aegis includes a built-in single-page application served directly from `frontend/` by FastAPI.

### 1. Agent Playground
Submit prompts, run presets (Refactor, Find bugs, Unit tests, Explain), view execution timelines (Routing -> Model -> Key -> Done), and inspect formatted markdown with language-specific code copy buttons.
![Agent Playground](assets/screenshots/agent_playground.png)

### 2. API Keys & Rotation Pools
Monitor total keys, keys in cooldown, and database connectivity. Track real-time RPM and RPD capacity bars per provider and run instant ping tests.
![API Keys and Pools](assets/screenshots/api_keys_pool.png)

### 3. Telemetry & Audit Logs
Live telemetry dashboard displaying total calls, success rate bars, provider filters, search filters, and individual call receipts.
![Telemetry Dashboard](assets/screenshots/telemetry_dashboard.png)

---

## Annotated Project Directory Tree

```
coding_agents/
├── README.md                           # Master technical documentation
├── requirements.txt                    # Project dependencies (FastAPI, PyTorch CPU, etc.)
├── server.py                           # FastAPI gateway server & API endpoints
│
├── routing/                            # Semantic routing & agent orchestration
│   ├── agent.py                        # CodingAgent class, interactive REPL CLI & router runner
│   ├── layer.py                        # TaskRouter: BGE embeddings, score threshold & intent extraction
│   └── utterances.py                   # Labeled semantic reference phrases for Easy and Medium tasks
│
├── models/                             # Decision engines & provider candidate cascades
│   ├── easy_models.py                  # Easy task cascade, pre-flight capacity checks & failover
│   └── medium_models.py                # Medium task cascade, frontier models & retry logic
│
├── configuration/                      # Gateway configuration, rate limits & key pooling
│   ├── .env                            # Active environment variables (API keys, DB URL)
│   ├── database.py                     # SQLAlchemy engine, session maker & CallRecord model
│   ├── key_pool.py                     # KeyPoolManager: key rotation, cooldown tracking & masking
│   ├── limits.py                       # PROVIDER_LIMITS (RPM/RPD/TPD) & MODEL_SPECS context registry
│   ├── rate_limiter.py                 # RateLimiterManager: sliding window usage vs quota validation
│   ├── usage_store.py                  # UsageStoreManager: DB call recording and token/call counting
│   │
│   ├── token_estimation/               # Token counting & payload validation
│   │   ├── __init__.py                 # Export estimate_token
│   │   └── estimator.py                # 3-layer token estimator (BPE cl100k_base + 60k heuristic)
│   │
│   ├── cloudflareapi_configuration.py  # Cloudflare Workers AI client & model registry
│   ├── gemini_configuration.py         # Google Gemini configuration & model registry
│   ├── groq_configuration.py           # Groq client configuration & model registry
│   ├── nvedia_configuration.py         # NVIDIA NIM configuration & model registry
│   ├── ollama_configuration.py         # Ollama OpenAI-compatible client configuration
│   ├── together_configuration.py       # Together AI model configuration
│   └── bytez_configuration.py          # Bytez API client configuration
│
├── frontend/                           # Interactive SPA dashboard (Vanilla ES Modules + CSS)
│   ├── index.html                      # Main HTML structure with semantic layout
│   ├── style.css                       # Root CSS forwarder importing css/main.css
│   ├── app.js                          # Root JS forwarder importing js/app.js
│   ├── marked.min.js                   # Local zero-dependency GitHub-flavored markdown parser
│   ├── css/                            # Modular stylesheets
│   │   ├── main.css                    # Master stylesheet aggregator
│   │   ├── variables.css               # Design tokens (warm linen palette, typography, radii)
│   │   ├── base.css                    # Resets, layout frame (.app-frame), typography
│   │   ├── navbar.css                  # Header branding, tabs & router status pill
│   │   ├── agent.css                   # Playground layout, prompt textarea, run button & response card
│   │   ├── keys.css                    # Key pools view, summary cards, provider table & progress bars
│   │   ├── telemetry.css               # Metrics summary cards, segmented bar, filters & logs table
│   │   └── modal-toast.css             # Key management modal & toast notifications
│   └── js/                             # Modular JavaScript architecture
│       ├── app.js                      # Application bootstrap & module initialization
│       ├── config.js                   # Reactive UI state and endpoint constants
│       ├── api.js                      # Clean fetch client for /api routes
│       ├── components/                 # View-specific components
│       │   ├── agent.js                # Prompt auto-resize, run button state & response renderer
│       │   ├── keys.js                 # Keys table rendering, test ping trigger & modal handler
│       │   ├── navbar.js               # Tab navigation switching & router health polling
│       │   ├── telemetry.js            # Telemetry rendering, filter pills, search & pagination
│       │   └── toast.js                # Floating toast notifications (success, error, info)
│       └── utils/                      # Helper utilities
│           └── markdown.js             # Marked.js integration, fallback parser & code copy buttons
│
├── test/                               # Comprehensive unit & integration test suite
│   ├── test_easy_decision_engine.py    # Unit tests for Easy candidate selection & capacity checks
│   ├── test_medium_decision_engine.py  # Unit tests for Medium candidate selection & capacity checks
│   ├── test_token_estimator.py         # Unit tests for 3-layer token estimator & heuristic threshold
│   ├── test_key_rotation.py            # Unit tests for round-robin rotation & cooldown tracking
│   ├── test_provider_configurations.py # Unit tests for provider clients & model configurations
│   ├── test_frontend_api.py            # Integration tests for FastAPI endpoints & static assets
│   ├── test_run_agent_8k.py            # 8K token capacity stress test script
│   └── test_run_parallel_rate_limiter.py # Concurrency & rate limiter parallel load test
│
└── assets/screenshots/                 # UI screenshots embedded in documentation
    ├── agent_playground.png            # Agent Playground interface with response
    ├── api_keys_pool.png               # API Keys status & rate limit usage meters
    └── telemetry_dashboard.png         # Telemetry metrics and Neon DB call logs
```

---

## Developer Customization Guide

### 1. Adding a New Model to a Candidate Pool
To add a model (e.g., a new Cloudflare or Gemini model):
1. Register its context window and max output tokens in `configuration/limits.py` under `MODEL_SPECS`:
   ```python
   MODEL_SPECS["cloudflare"]["@cf/meta/llama-3.3-70b-instruct"] = {
       "context_window": 131072,
       "max_output_tokens": 8192,
   }
   ```
2. Insert the model into `EASY_CANDIDATES` in `models/easy_models.py` or `MEDIUM_CANDIDATES` in `models/medium_models.py`:
   ```python
   {
       "provider": "cloudflare",
       "model": "@cf/meta/llama-3.3-70b-instruct"
   }
   ```

### 2. Customizing Complexity Utterances & Thresholds
To refine the classifier or adjust sensitivity:
1. Open `routing/utterances.py` and add domain-specific phrases to `EASY_UTTERANCES` or `MEDIUM_UTTERANCES`.
2. Open `routing/layer.py` and adjust the similarity score threshold (default: `0.60`):
   ```python
   easy_route = Route(name="Easy", utterances=EASY_UTTERANCES, score_threshold=0.65)
   ```

### 3. Modifying Provider Quotas (RPM / RPD / TPD)
Open `configuration/limits.py` and update the values in `PROVIDER_LIMITS`:
```python
PROVIDER_LIMITS["groq"] = {
    "rpm": 30,     # Max requests per minute
    "rpd": 1000,   # Max requests per day
    "tpd": 200000  # Max tokens per day
}
```

### 4. Adding a New LLM Provider
1. Add the provider's API key variable to `configuration/.env` (e.g. `MISTRAL_API_KEY="..."`).
2. Map the environment variable in `configuration/key_pool.py` in `env_var_map`.
3. Add client factory logic in `create_client_for_provider` within `models/easy_models.py` and `models/medium_models.py`.
4. Add default rate limits to `PROVIDER_LIMITS` in `configuration/limits.py`.

---

## Local Setup & Getting Started

### 1. Prerequisites
- **Python**: Version `3.11` or higher
- **Git**: Installed and configured on your system

### 2. Clone and Setup Environment
```bash
# Clone the repository
git clone https://github.com/chadwick223/LLm-api-gateway.git
cd LLm-api-gateway

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies (CPU PyTorch + FastAPI + Semantic Router)
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create or verify `configuration/.env` with your API keys:
```bash
# Provider API Keys (comma-separated for multi-key rotation pools)
GROQ_API_KEY="gsk_key1,gsk_key2"
GEMINI_API_KEY="AIzaSy..."
CLOUDFLARE_API_KEY="cfat_..."
CLOUDFLARE_ACCOUNT_ID="44640a..."
NVIDIA_API_KEY="nvapi-..."
OLLAMA_API_KEY="ollama"
OLLAMA_BASE_URL="http://localhost:11434/v1"

# Database Connection (Neon PostgreSQL or omit for local SQLite)
DATABASE_URL="postgresql://user:password@ep-host.aws.neon.tech/neondb?sslmode=require"
```
*(If `DATABASE_URL` is omitted, Aegis automatically creates a local SQLite database at `sqlite:///./gateway.db`.)*

### 4. Running the Gateway Web Server
Start the FastAPI server and web dashboard:
```bash
python server.py
```
Open your browser and navigate to:
```
http://localhost:8080
```
- **Web UI**: `http://localhost:8080/`
- **Health Check**: `http://localhost:8080/api/health`
- **API Documentation**: `http://localhost:8080/docs`

### 5. Running the Interactive CLI (REPL Mode)
If you prefer running queries directly in the terminal without a web browser:
```bash
python routing/agent.py
```
The BGE model loads once into memory, allowing you to enter repeated prompts interactively with sub-second turnaround.

### 6. Running a Single Prompt via CLI
```bash
python routing/agent.py --prompt "Fix the syntax error in def add(a, b) return a + b"
```

---

## Testing & Verification Suite

Aegis includes a comprehensive suite of unit and integration tests. Run all tests with the virtual environment activated:

```powershell
# Run Easy Decision Engine tests
python test/test_easy_decision_engine.py

# Run Medium Decision Engine tests
python test/test_medium_decision_engine.py

# Run Token Estimator tests (exact BPE + 60k heuristic)
python test/test_token_estimator.py

# Run Provider Client & Configuration tests
python test/test_provider_configurations.py

# Run Key Pool Rotation & Cooldown tests
python test/test_key_rotation.py

# Run FastAPI & Frontend integration tests
python test/test_frontend_api.py
```

### Running All Unit Tests in One Command
```bash
python -m unittest discover -s test -p "test_*.py"
```

---

## License

This project is licensed under the [MIT License](LICENSE).
