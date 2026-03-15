# HomeBase3 - Agent Guide

## Project Overview

HomeBase3 is an AI-powered Metaverse design generation API. It provides endpoints for generating creative Metaverse design directions and UI widgets based on user prompts. The project is designed to be deployed on Azure with a containerized backend.

**Current Status**: This project is in the infrastructure setup phase. The backend application code (FastAPI) and frontend (Astro) referenced in configuration files have not yet been implemented. Only infrastructure configuration, Docker setup, and API specification exist.

## Technology Stack

### Backend (Planned)
- **Framework**: FastAPI (Python 3.11)
- **Server**: Uvicorn ASGI server
- **Port**: 8000 (Docker), 3001 (docker-compose mapping)
- **API Spec**: OpenAPI 3.0 (defined in `openapi.json`)

### Frontend (Planned)
- **Framework**: Astro
- **Build Output**: `dist` directory
- **Location**: `/frontend` (not yet created)

### Infrastructure & Deployment
- **Containerization**: Docker with Docker Compose
- **Cloud Platform**: Azure
  - Azure Container Apps (backend)
  - Azure Static Web Apps (frontend)
  - Azure API Management (with rate limiting policies)
- **IaC**: Bicep templates (`.azure/*.bicep`)
- **Deployment Tool**: Azure Developer CLI (azd)

### Development Tools
- **IDE**: VS Code with recommended extensions
- **Code Formatting**: Prettier
- **Linting**: ESLint
- **API Testing**: REST Client, OpenAPI/Swagger tools

## Project Structure

```
HomeBase3/
├── .azure/                     # Azure infrastructure (Bicep)
│   ├── container-app.bicep     # Azure Container App definition
│   ├── static-web-app.bicep    # Azure Static Web App definition
│   └── plan.md                 # Deployment plan
├── .vscode/                    # VS Code configuration
│   ├── extensions.json         # Recommended extensions
│   ├── launch.json             # Debug configurations
│   ├── settings.json           # Editor settings
│   └── tasks.json              # Build/development tasks
├── backend/                    # Backend application (NOT YET IMPLEMENTED)
│   └── Dockerfile              # FastAPI container definition
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore rules
├── apim-policies.xml           # Azure API Management policies
├── azure.yaml                  # Azure Static Web Apps config
├── docker-compose.yml          # Local development orchestration
├── openapi.json                # API specification (OpenAPI 3.0)
└── README.md                   # Setup instructions
```

## API Specification

The API is defined in `openapi.json` with the following endpoints:

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/health` | GET | Health check endpoint | Public |
| `/api/generate-styles` | POST | Generate 3 style directions from a prompt | Authenticated |
| `/api/generate-artifact` | POST | Generate HTML/CSS widget from prompt + style | Authenticated |

**Base URLs**:
- Production: `https://litlabs-os-api.azure-api.net`
- Local Dev: `http://localhost:3001`

## Environment Configuration

### Required Environment Variables

Create a `.env` file by copying `.env.example`:

```powershell
copy .env.example .env
```

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | API key for Claude Code integration | Yes |

### Security Notes
- Never commit `.env` files to version control
- The `.gitignore` already excludes `.env` and `.env.*.local` files
- Only `.env.example` should be committed (with placeholder values)

## Build and Development Commands

### Docker Commands

```powershell
# Build backend Docker image
docker build -t homebase3-api ./backend

# Start all services (detached)
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Rebuild and restart
docker compose up -d --build
```

### VS Code Tasks

The following tasks are configured in `.vscode/tasks.json`:

| Task | Command | Purpose |
|------|---------|---------|
| `docker-build` | `docker build -t homebase3-api ./backend` | Build backend image |
| `docker-up` | `docker compose up -d` | Start services |
| `docker-down` | `docker compose down` | Stop services |
| `docker-logs` | `docker compose logs -f` | View logs |
| `docker-rebuild` | `docker compose up -d --build` | Full rebuild |
| `openapi-validate` | `npx @apidevtools/swagger-cli validate openapi.json` | Validate API spec |
| `openapi-generate` | `npx openapi-generator-cli generate -i openapi.json -g typescript-axios -o src/api` | Generate client |

Run tasks via: `Ctrl+Shift+P` → `Tasks: Run Task`

## Code Style Guidelines

### Editor Configuration
- **Formatter**: Prettier (default)
- **Tab Size**: 4 spaces
- **Format On Save**: Enabled
- **Fix on Save**: Enabled
- **Organize Imports on Save**: Enabled

### File Associations
- `*.json` files are treated as `jsonc` (allows comments)
- OpenAPI schema validation for `openapi.json`

### Excluded Files (VS Code)
- `node_modules`
- `dist`
- `.azure`

## Testing Instructions

### Local Testing

1. Set up environment variables:
   ```powershell
   $env:ANTHROPIC_API_KEY = "your-key-here"
   ```

2. Start the backend:
   ```powershell
   docker compose up -d
   ```

3. Test health endpoint:
   ```powershell
   curl http://localhost:3001/api/health
   ```

### API Validation

Validate the OpenAPI specification:
```powershell
npx @apidevtools/swagger-cli validate openapi.json
```

## Deployment Process

### Prerequisites
- Azure CLI or Azure Developer CLI (azd)
- Docker (for local testing)

### Deployment Steps (from `.azure/plan.md`)

1. Review generated infrastructure files in `.azure/`
2. Deploy using Azure CLI or `azd up`
3. Update Container App with actual ACR image URL

### Azure Resources

| Resource | Purpose | File |
|----------|---------|------|
| Container App | Host FastAPI backend | `container-app.bicep` |
| Static Web App | Host Astro frontend | `static-web-app.bicep` |
| API Management | Rate limiting, auth | `apim-policies.xml` |

### Rate Limiting
- 100 calls per minute per subscription
- Requires `Ocp-Apim-Subscription-Key` header

## Security Considerations

1. **API Keys**: Store in `.env`, never commit
2. **Authentication**: API routes protected via Azure API Management
3. **PowerShell Sandboxing**: Backend implements secure PowerShell execution for cloud
4. **CORS**: Configure appropriately for production

## Missing Components

The following components are referenced in configuration but not yet implemented:

1. **Backend Application**: FastAPI Python code with:
   - `main.py` (entry point)
   - `requirements.txt` (dependencies)
   - Route handlers for `/api/health`, `/api/generate-styles`, `/api/generate-artifact`

2. **Frontend Application**: Astro-based frontend in `/frontend` directory

3. **AI Integration**: Code to call AI services (Gemini/Anthropic) for style and artifact generation

## Next Steps for Development

1. Implement the FastAPI backend with the defined API endpoints
2. Create the Astro frontend application
3. Add AI service integration for content generation
4. Update Dockerfile if Python dependencies change
5. Test locally with Docker Compose
6. Deploy to Azure using azd or Azure CLI
