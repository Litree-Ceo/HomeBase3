"""
HomeBase3 - AI-powered Metaverse Design Generation API
FastAPI backend - supports OpenAI, Anthropic, DeepSeek, OpenRouter with Azure Integration
"""
import os
import json
import re
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Import Azure integration (optional)
try:
    from azure_integration import AzureConfig, AzureMonitoring, AZURE_APP_CONFIG
    AZURE_ENABLED = True
except ImportError:
    AZURE_ENABLED = False
    logger.warning("Azure integration not available")

app = FastAPI(
    title="LiTLabS OS AI API",
    description="AI Proxy Server for Metaverse Design Generation",
    version="2.0.0"
)

# CORS Middleware
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request middleware for monitoring
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests and track performance"""
    start_time = time.time()
    path = request.url.path
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log to Application Insights if enabled
        if AZURE_ENABLED:
            AzureMonitoring.log_metric(
                "request_duration_ms",
                duration * 1000,
                {"path": path, "status": response.status_code}
            )
        
        # Add custom headers
        response.headers["X-Process-Time"] = str(duration)
        if AZURE_ENABLED:
            response.headers["X-Azure-App"] = AzureConfig.AZURE_APP_NAME
        
        logger.info(f"{request.method} {path} - {response.status_code} ({duration:.3f}s)")
        return response
        
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        if AZURE_ENABLED:
            AzureMonitoring.log_exception(e)
        raise

# Get API keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Azure OpenAI support
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

# Use AI_PROVIDER env var or auto-detect
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto").lower()

# Try providers in order of preference
PROVIDER = None
API_KEY = None
BASE_URL = None
MODEL = None

if AI_PROVIDER == "azure" or (AI_PROVIDER == "auto" and AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY):
    PROVIDER = "azure-openai"
    API_KEY = AZURE_OPENAI_API_KEY
    BASE_URL = AZURE_OPENAI_ENDPOINT
    MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    logger.info("Using Azure OpenAI")
    
elif AI_PROVIDER == "openai" or (AI_PROVIDER == "auto" and OPENAI_API_KEY and OPENAI_API_KEY not in ["your-openai-api-key-here", "invalid", ""]):
    PROVIDER = "openai"
    API_KEY = OPENAI_API_KEY
    BASE_URL = "https://api.openai.com/v1"
    MODEL = "gpt-4o-mini"
    
elif AI_PROVIDER == "anthropic" or (AI_PROVIDER == "auto" and ANTHROPIC_API_KEY and ANTHROPIC_API_KEY not in ["your-anthropic-api-key-here", "invalid", ""]):
    PROVIDER = "anthropic"
    API_KEY = ANTHROPIC_API_KEY
    BASE_URL = "https://api.anthropic.com"
    MODEL = "claude-3-haiku-20240307"
    
elif AI_PROVIDER == "google" or (AI_PROVIDER == "auto" and GOOGLE_API_KEY and GOOGLE_API_KEY not in ["your-google-api-key-here", "invalid", ""]):
    PROVIDER = "google"
    API_KEY = GOOGLE_API_KEY
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    MODEL = "gemini-1.5-flash"
    
elif AI_PROVIDER == "deepseek" or (AI_PROVIDER == "auto" and DEEPSEEK_API_KEY and DEEPSEEK_API_KEY not in ["your-deepseek-api-key-here", "invalid", ""]):
    PROVIDER = "deepseek"
    API_KEY = DEEPSEEK_API_KEY
    BASE_URL = "https://api.deepseek.com/v1"
    MODEL = "deepseek-chat"
    
elif AI_PROVIDER == "openrouter" or (AI_PROVIDER == "auto" and OPENROUTER_API_KEY and OPENROUTER_API_KEY not in ["your-openrouter-api-key-here", "invalid", ""]):
    PROVIDER = "openrouter"
    API_KEY = OPENROUTER_API_KEY
    BASE_URL = "https://openrouter.ai/api/v1"
    MODEL = "openai/gpt-3.5-turbo"

if not PROVIDER:
    raise ValueError("No valid API key found. Set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, DEEPSEEK_API_KEY, OPENROUTER_API_KEY, or Azure OpenAI vars in .env")

logger.info(f"Using AI Provider: {PROVIDER}")
if AZURE_ENABLED:
    AzureMonitoring.log_event("app_startup", {"provider": PROVIDER, "azure_app": AzureConfig.AZURE_APP_NAME})

# Request/Response models
class StyleRequest(BaseModel):
    prompt: str

class ArtifactRequest(BaseModel):
    prompt: str
    styleInstruction: str

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    provider: str
    azure: bool = AZURE_ENABLED
    environment: str = os.getenv("ENVIRONMENT", "development")

class StylesResponse(BaseModel):
    styles: list[str]

class ArtifactResponse(BaseModel):
    html: str
    status: str

async def call_ai(prompt: str, system_prompt: str, max_tokens: int = 2000) -> str:
    """Make API call to AI provider"""
    
    if PROVIDER == "anthropic":
        headers = {
            "x-api-key": API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/messages",
                headers=headers,
                json={
                    "model": MODEL,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                    "system": system_prompt
                }
            )
            if response.status_code != 200:
                raise Exception(f"Anthropic API error: {response.text}")
            data = response.json()
            return data["content"][0]["text"]

    elif PROVIDER == "google":
        headers = {"Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/models/{MODEL}:generateContent?key={API_KEY}",
                headers=headers,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "generationConfig": {"temperature": 0.8, "maxOutputTokens": max_tokens}
                }
            )
            if response.status_code != 200:
                raise Exception(f"Google API error: {response.text}")
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    elif PROVIDER == "azure-openai":
        # Azure OpenAI uses OpenAI SDK with different endpoint
        headers = {
            "api-key": API_KEY,
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/openai/deployments/{MODEL}/chat/completions?api-version=2024-02-15-preview",
                headers=headers,
                json={
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.8,
                    "max_tokens": max_tokens
                }
            )
            if response.status_code != 200:
                raise Exception(f"Azure OpenAI API error: {response.text}")
            data = response.json()
            return data["choices"][0]["message"]["content"]

    else:
        # OpenAI, DeepSeek, OpenRouter (OpenAI-compatible)
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

        if PROVIDER == "openrouter":
            headers["HTTP-Referer"] = "https://homebase3.app"
            headers["X-Title"] = "HomeBase3"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/chat/completions",
                headers=headers,
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.8,
                    "max_tokens": max_tokens
                }
            )

            if response.status_code != 200:
                raise Exception(f"API error: {response.text}")

            data = response.json()
            return data["choices"][0]["message"]["content"]

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Azure"""
    health = HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        provider=PROVIDER,
        azure=AZURE_ENABLED
    )
    
    if AZURE_ENABLED:
        AzureMonitoring.log_metric("health_check", 1.0, {"status": "healthy"})
    
    return health

@app.get("/api/status")
async def status():
    """Detailed status endpoint"""
    return {
        "status": "running",
        "provider": PROVIDER,
        "model": MODEL,
        "azure_enabled": AZURE_ENABLED,
        "azure_app": AzureConfig.AZURE_APP_NAME if AZURE_ENABLED else "local",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/generate-styles", response_model=StylesResponse)
async def generate_styles(request: StyleRequest):
    """Generate style suggestions for metaverse design"""
    if not request.prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    system_prompt = """You are a creative Metaverse design expert.
Generate 3 distinct, creative style directions for metaverse UI/UX designs.
Each style should have a name and a brief description (1-2 sentences).
Return ONLY a JSON array of 3 strings: ["Style: Description", "Style: Description", "Style: Description"]"""

    try:
        content = await call_ai(
            f"Generate 3 creative design styles for: {request.prompt}",
            system_prompt, max_tokens=300
        )

        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            styles = json.loads(match.group())
        else:
            styles = [s.strip() for s in content.split('\n') if s.strip()][:3]

        if AZURE_ENABLED:
            AzureMonitoring.log_event("styles_generated", {"count": len(styles)})

        return StylesResponse(styles=styles)
    except Exception as e:
        logger.error(f"Style generation failed: {str(e)}")
        if AZURE_ENABLED:
            AzureMonitoring.log_exception(e)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/api/generate-artifact", response_model=ArtifactResponse)
async def generate_artifact(request: ArtifactRequest):
    """Generate HTML artifact for metaverse UI"""
    if not request.prompt or not request.styleInstruction:
        raise HTTPException(status_code=400, detail="Both prompt and styleInstruction are required")

    system_prompt = """You are a expert UI/UX designer for the Metaverse.
Generate a complete, self-contained HTML/CSS artifact.
- Use modern CSS (flexbox, grid, gradients, glassmorphism)
- Make it visually stunning and futuristic
- Return ONLY the raw HTML code, no markdown"""

    try:
        html = await call_ai(
            f"Create a Metaverse UI widget for: {request.prompt}. Style: {request.styleInstruction}",
            system_prompt, max_tokens=2000
        )

        html = html.strip()
        if html.startswith("```html"): html = html[7:]
        elif html.startswith("```"): html = html[3:]
        if html.endswith("```"): html = html[:-3]

        if AZURE_ENABLED:
            AzureMonitoring.log_event("artifact_generated", {"length": len(html)})

        return ArtifactResponse(html=html.strip(), status="success")
    except Exception as e:
        logger.error(f"Artifact generation failed: {str(e)}")
        if AZURE_ENABLED:
            AzureMonitoring.log_exception(e)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    if AZURE_ENABLED:
        AzureMonitoring.log_exception(exc)
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request.headers.get("x-request-id")}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
