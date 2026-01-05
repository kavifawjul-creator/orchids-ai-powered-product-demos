


## PRODUCT REQUIREMENTS DOCUMENT (PRD)
## 1) Product Name
AutoVidAI — AI-Driven Product Video Generation Platform
(Codebase → Autonomous App Interaction → Live Browser Recording → Editor → Publish)

## 2) Executive Summary
AutoVidAI empowers developers and product owners to automatically generate
professional product videos (demo, walkthrough, explainer, feature ads) from their own
codebase or deployed app using advanced LLMs + browser automation + AI reasoning
+ structured video editing.
User provides:
- Git repository link or uploaded project files
- Written natural-language video requirement (prompt)
System automatically:
- Builds the app
- Intelligently interacts with it
- Shows live browser playback
- Records key sequences
- Segments into clips
- Opens in a web video editor
## Goal:
Reduce video creation time from hours/days → minutes with minimal manual work.

3) Success Metrics (KPIs)
## Metric Target
User prompt → video draft time < 10 minutes
Clip quality (user rated) ≥ 4/5

## Metric Target
Prompt understanding accuracy ≥ 90%
Editor engagement (clip customization) ≥ 80% of users
Publish rate ≥ 30% of total users

## 4) Primary User Flows
Flow A — Create a Product Demo
- User pastes repo URL or uploads project.
- User enters prompt:
“Create a demo video showing login → dashboard analytics.”
- System parses intent, determines flows.
- AI runs app
- Live browser view shown as agent interacts.
- Recording segments auto-generated.
- Web editor opens with video timeline & clips.
- User edits, adds captions/voiceover, exports video.

## 5) Detailed Requirements
## 5.1 Functional
## 1. Repo Ingestion
o Clone Git repo (public or authenticated)
o Detect build system (npm, yarn, docker, pip)
o Static analysis for UI routes / components
## 2. Prompt Intent Parsing
o Classify video type (demo, explainer, walkthrough, ad)
o Identify features referenced in prompt
## 3. App Build & Runtime Sandbox

o Auto provisioning (container/MCP environment)
o Build & run app for automation
- AI Browser Automation Agent
o Navigate app like real user
o Interact with UI (click/type/hovers)
o Intelligent error detection & recovery
o Live browser view during interaction
o Capture structured event logs & screen recording
## 5. Segmented Recording Output
o Detect clips based on feature milestones
o Store raw clips + metadata
- Editor UI
o Timeline with clips
o Text overlays
o Voiceover support
o Auto captions
o Aspect ratio presets (16:9, 9:16, 1:1)
## 7. Publishing
o Export MP4
o Embed link generator
o Social share toolkit

6) Non-Functional Requirements
## Requirement Value
Security Sandboxed builds & sessions
Scalability Autoscale MCP workers
Latency Live browser updates < 500ms

## Requirement Value
Data privacy Encrypted storage
## Multi-tenant Yes

7) System Architecture (High-Level)

## DETAILED SYSTEM ARCHITECTURE
(Hierarchical step-by-step breakdown)

A) Frontend (User Interface)
## 1. Input Portal
- Accepts Git URL / file upload
- Prompt text box with examples
## 2. Live Browser Display
- WebRTC / WebSocket powered
- Shows AI agent interacting with browser in real time
- Smooth playback while recording ongoing
## 3. Editor
- Clip library
- Timeline playback
- Add overlays / captions / audio
- Export UI

## B) Backend Services
- Intent Parser (LLM Layer)
- LLM parses user text
- Outputs structured intent model

## • {
## •   "video_type": "demo",
## •   "features": ["login","dashboard"],
## •   "style": "professional"
## • }
## 2. Code Analyzer
- Static code inspection
- UI route detection
- Component mapping
## 3. Build & Sandbox Manager
- Kubernetes / container orchestration
- Auto builds (npm / docker / pip)
- Maps preview URL
- AI Automation Orchestrator
- Schedules tasks
- Controls browser automation MCP
- Generates action scripts
- Browser Automation (MCP Engine)
- Controls cloud browser instances
- Live interaction streams
- Logs every UI event
- Tools for navigation, clicks, typing
## 6. Recorder & Segmenter
- Streams DOM + video
- Detects key interactions & auto-segments
- Metadata tagging
## 7. Clip Store
- Stores clips, metadata

- Searchable by features
## 8. Editor Backend
- Render service (FFmpeg)
- Asset management
## 9. Publish / Export
- Video generation
- CDN hosting

## C) Infrastructure Layer
- Kubernetes clusters
- MCP servers (browser + other skills)
- LLM models (Gemini/OpenAI / Anthropic / Claude)
- Storage (S3)
- WebSockets (browser streaming)
## • Authentication + Permissions

Step-by-Step Architecture Workflow

## Repo Ingestion
- Receive Git URL / file upload
- Clone or extract
- Detect language / framework
- Run static analysis

## Intent Analysis
- LLM processes prompt
- Outputs video_type + feature list


## Build & Deploy
- Build in isolated container
- Deploy to internal staging URL
- Register staging in Browser MCP pool

## Browser Automation Begins
- AI Agent Controller uses MCP browser automation servers
(e.g., Playwright MCP / Browserbase MCP from MCPMarket) (MCP Market)
- Launch real browser instance configured with live streaming
- UI interactions according to plan
Live browser view:
Streaming of the browser viewport to frontend via WebRTC so the user sees the agent’s
actions in near-real-time as the video is recorded.

## Recording & Segmentation
- Recorder logs interactions
- Auto segments clips
- Tag clips using feature metadata

## Editor Population
- Database of clips delivered to frontend editor
- Editor fetches metadata + raw media
- Editor loads timeline

## Final Export
- User customizes
- Backend FFmpeg compiles final video
- Export & share


MCPMarket Recommendation — Skills & MCP Servers
Here’s how to leverage MCPMarket to support your platform:

Browser Automation MCP Servers
You need MCP servers that let AI control browsers:
## Recommended Servers:
- Playwright MCP Server — industry-standard browser automation support
(navigation/click/type) (MCP Market)
- Browserbase MCP Server — strong MCP browser automation with session
persistence and snapshots (MCP Market)
These provide tools like:
- navigate
- click
- type
- hover
- waitForSelector
- getNetworkRequests
(based on typical browser MCP toolsets) (MCP Now)
Use these for:
- Autonomous flows
- Recording steps
- Live view streaming

 Helpful MCP Skills (Agent Skills)
From MCPMarket “Agent Skills” leaderboard you can extend AI capabilities to:
- Code analysis helper skills
- Integration with GitHub
- Task orchestration skills

- Productivity and workflow skills
(Agent skill examples discovered) (MCP Market)
Strong categories to integrate:
## • Developer Tools
- API Development
## • Browser Automation
## • Productivity & Workflow

Why MCP + Skills Matters
MCP connects LLMs to real tools and environments, allowing:
- external tool execution
- browser automation
- code insights
- file manipulation
(MCP gives LLMs real-world capabilities beyond text) (AIPill)
Your “AI video automator” core will deeply depend on these.

