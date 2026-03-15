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

# Get API keys
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Try providers in order of preference
PROVIDER = None
API_KEY = None
BASE_URL = None
MODEL = None

# Check DeepSeek first (usually has free credits)
if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY not in ["your-deepseek-api-key-here", "invalid", ""]:
    PROVIDER = "deepseek"
    API_KEY = DEEPSEEK_API_KEY
    BASE_URL = "https://api.deepseek.com/v1"
    MODEL = "deepseek-chat"

# Fallback to OpenRouter
elif OPENROUTER_API_KEY and OPENROUTER_API_KEY not in ["your-openrouter-api-key-here", "invalid", ""]:
    PROVIDER = "openrouter"
    API_KEY = OPENROUTER_API_KEY
    BASE_URL = "https://openrouter.ai/api/v1"
    MODEL = "openai/gpt-3.5-turbo"

if not PROVIDER:
    raise ValueError("No valid API key found. Set DEEPSEEK_API_KEY or OPENROUTER_API_KEY in .env")

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
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    if PROVIDER == "deepseek":
        headers["Content-Type"] = "application/json"
    elif PROVIDER == "openrouter":
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

