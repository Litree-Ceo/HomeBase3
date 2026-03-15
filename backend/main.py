"""
HomeBase3 - AI-powered Metaverse Design Generation API
FastAPI backend with multi-provider AI support (Google, OpenAI, Anthropic)
"""
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
import httpx

# Load environment variables
load_dotenv()

app = FastAPI(
    title="LiTLabS OS AI API",
    description="AI Proxy Server for Metaverse Design Generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Provider Configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "google").lower()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# API URLs
GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
OPENAI_BASE_URL = "https://api.openai.com/v1"
ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"

# Request models
class StyleRequest(BaseModel):
    prompt: str = Field(..., description="The design prompt for style generation")

class ArtifactRequest(BaseModel):
    prompt: str = Field(..., description="The design prompt for artifact generation")
    styleInstruction: str = Field(..., description="The style direction for the artifact")

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    provider: str

class StylesResponse(BaseModel):
    styles: List[str]

class ArtifactResponse(BaseModel):
    html: str
    status: str = "success"


def get_provider_config():
    """Get the active AI provider configuration."""
    if AI_PROVIDER == "google":
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        return {
            "name": "google",
            "api_key": GOOGLE_API_KEY,
            "model": "gemini-1.5-flash"
        }
    elif AI_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment")
        return {
            "name": "openai",
            "api_key": OPENAI_API_KEY,
            "model": "gpt-4"
        }
    elif AI_PROVIDER == "anthropic":
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        return {
            "name": "anthropic",
            "api_key": ANTHROPIC_API_KEY,
            "model": "claude-3-sonnet-20240229"
        }
    else:
        raise ValueError(f"Unknown AI provider: {AI_PROVIDER}")


async def generate_with_google(prompt: str, system_prompt: str = "") -> str:
    """Generate content using Google Gemini API."""
    config = get_provider_config()
    api_key = config["api_key"]
    model = config["model"]
    
    url = f"{GOOGLE_BASE_URL}/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": f"{system_prompt}\n\n{prompt}"}]
        }],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 8192
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        
        if "candidates" in data and len(data["candidates"]) > 0:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text
        else:
            raise Exception("No response from Gemini API")


async def generate_with_openai(prompt: str, system_prompt: str = "") -> str:
    """Generate content using OpenAI API."""
    config = get_provider_config()
    api_key = config["api_key"]
    model = config["model"]
    
    url = f"{OPENAI_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt} if system_prompt else {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def generate_with_anthropic(prompt: str, system_prompt: str = "") -> str:
    """Generate content using Anthropic Claude API."""
    config = get_provider_config()
    api_key = config["api_key"]
    model = config["model"]
    
    url = f"{ANTHROPIC_BASE_URL}/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]


async def generate_content(prompt: str, system_prompt: str = "") -> str:
    """Generate content using the configured AI provider."""
    config = get_provider_config()
    
    if config["name"] == "google":
        return await generate_with_google(prompt, system_prompt)
    elif config["name"] == "openai":
        return await generate_with_openai(prompt, system_prompt)
    elif config["name"] == "anthropic":
        return await generate_with_anthropic(prompt, system_prompt)
    else:
        raise ValueError(f"Unsupported provider: {config['name']}")


# API Endpoints
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        provider=AI_PROVIDER
    )


@app.post("/api/generate-styles", response_model=StylesResponse)
async def generate_styles(request: StyleRequest):
    """Generate 3 creative Metaverse design styles from a prompt."""
    try:
        system_prompt = """You are a Metaverse design expert. Generate exactly 3 creative, distinct design style directions.
Respond ONLY with a JSON array of 3 style descriptions. Example format:
["Cyberpunk Neon with dark futuristic glowing accents", "Minimal Zen with clean lines and natural elements", "Retro Futurism blending 80s aesthetics with modern tech"]"""

        user_prompt = f"Generate 3 Metaverse design styles for: {request.prompt}"
        
        response = await generate_content(user_prompt, system_prompt)
        
        # Try to extract JSON array from response
        try:
            # Find JSON array in the text
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                styles = json.loads(match.group())
            else:
                # Fallback: split by newlines or commas
                styles = [s.strip().strip('"- ') for s in response.replace('\n', ',').split(',') if s.strip()]
            
            # Ensure we have exactly 3 styles
            styles = styles[:3] if len(styles) >= 3 else styles + ["Default Style"] * (3 - len(styles))
            
            return StylesResponse(styles=styles)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return StylesResponse(styles=[
                "Cyberpunk Neon Style",
                "Minimal Zen Style", 
                "Futuristic Abstract Style"
            ])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate styles: {str(e)}")


@app.post("/api/generate-artifact", response_model=ArtifactResponse)
async def generate_artifact(request: ArtifactRequest):
    """Generate a Metaverse UI widget based on prompt and style."""
    try:
        system_prompt = """You are an expert Metaverse UI designer and developer. Create complete, self-contained HTML/CSS widgets.
The code should be fully self-contained in a single HTML file with embedded CSS. Use modern CSS (flexbox/grid, gradients, animations).
Include inline SVG icons or emojis. Make it responsive and visually impressive with dark theme suitable for Metaverse environments.
Respond ONLY with the raw HTML code, no markdown formatting, no explanations."""

        user_prompt = f"""Create a Metaverse UI widget:
Design Request: {request.prompt}
Style Direction: {request.styleInstruction}

Generate the complete HTML/CSS code:"""

        response = await generate_content(user_prompt, system_prompt)
        
        # Clean up markdown code blocks if present
        html = response.replace("```html", "").replace("```", "").strip()
        
        return ArtifactResponse(html=html, status="success")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate artifact: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "HomeBase3 API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "provider": AI_PROVIDER
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
