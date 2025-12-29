# AutoVidAI Backend

AI-powered video demo generation platform backend.

## Architecture

```
backend/
├── app/
│   ├── api/           # FastAPI routes and WebSocket handlers
│   ├── core/          # Configuration, database, events
│   ├── models/        # Pydantic schemas
│   ├── services/      # Business logic services
│   │   ├── project/   # Repository management
│   │   ├── sandbox/   # Daytona sandbox orchestration
│   │   ├── intent/    # LLM-based plan generation
│   │   ├── agent/     # Execution state machine
│   │   ├── browser/   # Playwright automation
│   │   └── recorder/  # Video capture & segmentation
│   └── workers/       # Background task workers
└── requirements.txt
```

## Services

### Project Service
- Git repository ingestion
- Build system detection (Node.js, Python, Docker)
- Metadata management

### Sandbox Service (Daytona)
- Isolated dev environment creation
- App building and deployment
- Preview URL provisioning
- Auto-cleanup

### Intent Service
- Prompt analysis via LLM
- Execution plan generation
- Deterministic step creation

### Agent Service
- State machine execution
- Browser action orchestration
- Event emission

### Browser Service
- Playwright-based automation
- Click, type, navigate, scroll
- Screenshot capture
- Accessibility tree extraction

### Recorder Service
- Video recording management
- Feature milestone tracking
- Clip generation

## API Endpoints

### Projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects
- `GET /api/v1/projects/{id}` - Get project
- `POST /api/v1/projects/{id}/build` - Start build
- `DELETE /api/v1/projects/{id}` - Delete project

### Demos
- `POST /api/v1/demos/generate` - Start generation
- `GET /api/v1/demos/{id}` - Get demo status
- `GET /api/v1/demos/{id}/clips` - Get clips
- `GET /api/v1/demos/{id}/plan` - Get execution plan

### Sessions
- `GET /api/v1/sessions/{id}` - Get session
- `POST /api/v1/sessions/{id}/stop` - Stop session
- `GET /api/v1/sessions/{id}/screenshot` - Get screenshot

### WebSocket
- `WS /ws/{channel}` - Real-time events

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `DATABASE_URL` - PostgreSQL connection
- `SUPABASE_*` - Supabase credentials
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` - LLM access
- `DAYTONA_API_KEY` - Sandbox orchestration
- `REDIS_URL` - Event bus (optional)
