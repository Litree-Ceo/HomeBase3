"""
HomeBase3 - AI-powered Metaverse Design Generation API
FastAPI backend - supports OpenAI, Anthropic, DeepSeek, OpenRouter
"""
import os
import json
import re
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

# Load environment variables
load_dotenv()

app = FastAPI(
    title="LiTLabS OS AI API",
    description="AI Proxy Server for Metaverse Design Generation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Use AI_PROVIDER env var or auto-detect
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto").lower()

# Try providers in order of preference based on AI_PROVIDER or availability
PROVIDER = None
API_KEY = None
BASE_URL = None
MODEL = None

if AI_PROVIDER == "openai" or (AI_PROVIDER == "auto" and OPENAI_API_KEY and OPENAI_API_KEY not in ["your-openai-api-key-here", "invalid", ""]):
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
    raise ValueError("No valid API key found. Set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, DEEPSEEK_API_KEY, or OPENROUTER_API_KEY in .env")

print(f"Using AI Provider: {PROVIDER}")

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

class StylesResponse(BaseModel):
    styles: list[str]

class ArtifactResponse(BaseModel):
    html: str
    status: str

async def call_ai(prompt: str, system_prompt: str, max_tokens: int = 2000) -> str:
    """Make API call to AI provider"""

    if PROVIDER == "anthropic":
        # Anthropic uses a different API format
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
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "system": system_prompt
                }
            )
            if response.status_code != 200:
                raise Exception(f"API error: {response.text}")
            data = response.json()
            return data["content"][0]["text"]

    elif PROVIDER == "google":
        # Google Gemini API
        headers = {"Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/models/{MODEL}:generateContent?key={API_KEY}",
                headers=headers,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "generationConfig": {
                        "temperature": 0.8,
                        "maxOutputTokens": max_tokens
                    }
                }
            )
            if response.status_code != 200:
                raise Exception(f"API error: {response.text}")
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

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
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        provider=PROVIDER
    )

@app.post("/api/generate-styles", response_model=StylesResponse)
async def generate_styles(request: StyleRequest):
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

        return StylesResponse(styles=styles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/api/generate-artifact", response_model=ArtifactResponse)
async def generate_artifact(request: ArtifactRequest):
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

        return ArtifactResponse(html=html.strip(), status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

