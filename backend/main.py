"""
HomeBase3 - AI-powered Metaverse Design Generation API
FastAPI backend with Anthropic Claude integration using httpx
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API key - try Anthropic first, fallback to OpenAI
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Determine which provider to use
ai_provider = os.getenv("AI_PROVIDER", "anthropic").lower()

if ai_provider == "anthropic" and ANTHROPIC_API_KEY:
    USE_ANTHROPIC = True
elif OPENAI_API_KEY:
    USE_ANTHROPIC = False
    ai_provider = "openai"
else:
    raise ValueError("No valid API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")

ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
OPENAI_BASE_URL = "https://api.openai.com/v1"

# Request models
class StyleRequest(BaseModel):
    prompt: str

class ArtifactRequest(BaseModel):
    prompt: str
    styleInstruction: str

# Response models
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    provider: str

class StylesResponse(BaseModel):
    styles: list[str]

class ArtifactResponse(BaseModel):
    html: str
    status: str

async def call_anthropic(prompt: str, system_prompt: str, max_tokens: int = 2000) -> str:
    """Make API call to Anthropic Claude using httpx"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{ANTHROPIC_BASE_URL}/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": [{"role": "user", "content": prompt}]
            }
        )

        if response.status_code != 200:
            raise Exception(f"Anthropic API error: {response.text}")

        data = response.json()
        return data["content"][0]["text"]

async def call_openai(prompt: str, system_prompt: str, max_tokens: int = 2000) -> str:
    """Make API call to OpenAI using httpx"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8,
                "max_tokens": max_tokens
            }
        )

        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.text}")

        data = response.json()
        return data["choices"][0]["message"]["content"]

async def call_ai(prompt: str, system_prompt: str, max_tokens: int = 2000) -> str:
    """Call AI provider based on configuration"""
    if USE_ANTHROPIC:
        return await call_anthropic(prompt, system_prompt, max_tokens)
    else:
        return await call_openai(prompt, system_prompt, max_tokens)

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Returns the health status of the API"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        provider=ai_provider
    )

@app.post("/api/generate-styles", response_model=StylesResponse)
async def generate_styles(request: StyleRequest):
    """Generate creative Metaverse design directions based on a prompt."""
    if not request.prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    system_prompt = """You are a creative Metaverse design expert.
Generate 3 distinct, creative style directions for metaverse UI/UX designs.
Each style should have a name and a brief description (1-2 sentences).
Return ONLY a JSON array of 3 strings in this format:
["Style Name: Description", "Style Name: Description", "Style Name: Description"]"""

    try:
        content = await call_ai(
            f"Generate 3 creative design styles for: {request.prompt}",
            system_prompt,
            max_tokens=300
        )

        # Extract JSON array from response
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
    """Generate a Metaverse UI widget (HTML/CSS) based on prompt and style."""
    if not request.prompt or not request.styleInstruction:
        raise HTTPException(
            status_code=400,
            detail="Both prompt and styleInstruction are required"
        )

    system_prompt = """You are a expert UI/UX designer for the Metaverse.
Generate a complete, self-contained HTML/CSS artifact.
- Use modern CSS (flexbox, grid, gradients, glassmorphism)
- Include inline CSS and JS if needed
- Make it visually stunning and futuristic
- Return ONLY the raw HTML code, no explanations or markdown code blocks"""

    try:
        html = await call_ai(
            f"""Create a Metaverse UI widget for: {request.prompt}

Style direction: {request.styleInstruction}

Generate beautiful, futuristic HTML/CSS that matches this style.""",
            system_prompt,
            max_tokens=2000
        )

        # Clean up any markdown formatting
        html = html.strip()
        if html.startswith("```html"):
            html = html[7:]
        elif html.startswith("```"):
            html = html[3:]
        if html.endswith("```"):
            html = html[:-3]
        html = html.strip()

        return ArtifactResponse(html=html, status="success")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

