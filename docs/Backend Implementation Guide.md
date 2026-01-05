


##  BACKEND IMPLEMENTATION GUIDE
AI Product Video Generation Platform
(Sandboxing via Daytona)

Core Backend Principles (Read First)
Before writing code, lock these principles:
## 1. Execution > Conversation
Everything is a job, not a chat.
## 2. Deterministic Agents
Plans are generated once, then executed.
## 3. Sandbox First
All user code runs inside Daytona-managed sandboxes.
- Event-Driven Pipeline
Recording, streaming, and segmentation are async consumers.
- Replayable by Design
Store actions + timestamps, not just raw video.

Backend Tech Stack (Recommended)
## Core
- API Framework: FastAPI (Python)
- Async Worker: Celery / Temporal / BullMQ
- LLM Access: OpenAI / Claude
- Browser Automation: MCP Playwright Server
## • Sandboxing: Daytona
- Streaming: WebSockets + WebRTC
- Video Processing: FFmpeg
- Storage: S3-compatible (video + metadata)
- DB: PostgreSQL + Redis


## Backend Service Decomposition
backend/
├── api-gateway/
├── project-service/
├── intent-service/
├── sandbox-service/   <-- Daytona integration
├── agent-service/
├── browser-service/   <-- MCP orchestration
├── recorder-service/
├── editor-service/
├── export-service/
└── common/
Each service can start as a module, not a microservice (MVP).

Daytona Sandboxing Service (CRITICAL)
This is the foundation.
## 3.1 Responsibilities
- Create isolated dev environments
- Build & run user apps
- Expose preview URL
- Auto-destroy environments

## 3.2 Daytona Workflow
## Step 1 — Create Workspace
daytona workspace create \
--name project-123 \
--image node:18 \

## --cpu 2 \
--memory 4Gi
Backend wraps this via Daytona API/CLI.

## Step 2 — Inject Code
- Clone repo inside workspace
- Or unzip uploaded files
git clone https://github.com/org/app .

## Step 3 — Detect Build System
Backend runs detection logic:
if package_json:
build = "npm install && npm run dev"
elif dockerfile:
build = "docker build && docker run"
elif requirements_txt:
build = "pip install -r requirements.txt && python app.py"

## Step 4 — Run App
npm install
npm run dev
Expose via:
https://sandbox.daytona.internal/project-123

Step 5 — Register Preview URL
Store in DB:
## {
## "project_id": "123",

## "preview_url": "https://sandbox..."
## }

## Step 6 — Auto Cleanup
Destroy workspace:
- after video generation
- or inactivity timeout (e.g. 30 min)

## Project & Repo Service
## Responsibilities
- Accept Git URLs / uploads
- Store metadata
- Trigger sandbox creation
APIs
POST /projects
POST /projects/{id}/build
GET  /projects/{id}
## Implementation Steps
- Validate repo
- Save metadata
- Trigger Daytona sandbox job

## Intent & Planning Service
## Responsibilities
- Parse user prompt
- Determine video type
- Generate execution plan
## Implementation Steps

- Call LLM with Intent Prompt
- Validate output JSON
- Store execution plan immutably
Never regenerate plan mid-run.

## Agent Execution Service
This is your AI brain at runtime.

## 6.1 Agent State Machine
state = INIT

for feature in plan:
for step in feature.steps:
execute(step)
verify()
record_event()
emit_feature_milestone()

## 6.2 Key Data Structures
## {
## "session_id": "sess-789",
## "current_feature": "login",
## "step_index": 2,
## "browser_session": "mcp-456"
## }

## 6.3 Runtime Execution Loop
- Load execution plan

- Request browser from MCP
- For each step:
o Ask LLM for reasoning (small prompt)
o Send action to MCP browser
o Await success condition
o Emit event

Browser Automation Service (MCP)
## Responsibilities
- Control real browsers
- Execute clicks, typing, navigation
- Stream live browser view

7.1 MCP Tool Mapping
Action MCP Tool
Navigate browser.navigate
Click browser.click
Type browser.type
Wait browser.waitFor
Snapshot browser.screenshot

## 7.2 Live Browser Streaming
## Backend:
- Subscribe to MCP browser frame stream
- Forward frames via WebRTC
## Frontend:
- Render live view

- Overlay “AI is interacting...”
This is a trust multiplier.

## Recorder & Segmentation Service
## Responsibilities
- Record video stream
- Capture interaction timeline
- Segment clips

8.1 What to Record
- Video frames
- Action events
- Feature milestones
## • Timestamps
## 8.2 Clip Algorithm
clip.start = feature_start_time
clip.end   = feature_success_time
## Store:
## {
## "clip_id": "c1",
## "feature": "login",
## "start": 0,
## "end": 12.4
## }

Event Bus (Highly Recommended)
Use Redis / Kafka for events:
## • AGENT_ACTION

## • FEATURE_MILESTONE
## • RECORDING_READY
## • CLIPS_GENERATED
## Decouples:
- execution
- recording
- UI updates

## Editor Backend
## Responsibilities
- Serve clips
- Manage timelines
- Apply transformations
No heavy AI here — keep it fast.

## Export & Rendering Service
## Responsibilities
- Stitch clips
- Add captions / voiceover
- Render formats
## Uses:
ffmpeg -i input.mp4 -vf subtitles=...
Queue exports — never block UI.

## Security & Abuse Prevention
## Sandboxing Rules
- No outbound internet by default
- Read-only filesystem except /app

- Resource limits via Daytona
## Agent Limits
- Max steps per session
- Max browser time
- Kill switch on loops

## MVP BUILD ORDER (IMPORTANT)
Build in this order:
Project ingestion + Daytona sandbox
Manual browser automation via MCP
Live browser streaming
Recorder + segmentation
Agent planning logic
## Editor
## Export

