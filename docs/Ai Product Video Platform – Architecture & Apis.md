

AI Product Video Generation Platform
- System Architecture Diagrams (Drawn)
1.1 High-Level Architecture
## ┌──────────────────────────┐
## │        Web Frontend      │
│  - Repo Upload / URL     │
│  - Prompt Chat UI        │
## │  - Live Browser View     │
## │  - Video Editor          │
## └────────────┬─────────────┘
│ WebSocket / HTTPS
## ┌────────────▼─────────────┐
│        API Gateway       │
## │  Auth • Rate Limit       │
## │  Job Orchestration       │
## └────────────┬─────────────┘
## │
## ┌────────────▼───────────────────────────────────────────┐
│                Core AI Orchestration Layer              │
## │                                                         │
## │  ┌──────────────┐   ┌─────────────────┐               │
## │  │ Intent Parser│→→ │ Execution Planner│               │
│  │  (LLM)       │   │  (Steps & Flows) │               │
## │  └──────────────┘   └─────────────────┘               │
## │           │                    │                       │
## │           ▼                    ▼                       │
## │  ┌────────────────┐   ┌────────────────────┐          │
## │  │ Code Analyzer  │   │ Browser Agent Ctrl │          │
│  │ (Static + LLM) │   │ (MCP Coordinator) │          │
## │  └────────────────┘   └────────────────────┘          │
## └────────────┬───────────────────────────┬──────────────┘
## │                           │
## ┌────────────▼─────────────┐   ┌─────────▼──────────────┐
│ Build & Sandbox Service  │   │  MCP Browser Servers    │
│ (Daytona / Containers)   │   │ (Playwright / Browser) │
## └────────────┬─────────────┘   └─────────┬──────────────┘
## │                           │ Live View + Events
## ┌────────────▼─────────────┐   ┌─────────▼──────────────┐
│   App Runtime (Preview)  │   │ Recorder & Segmenter   │
│   Internal URL           │   │ Video + Metadata       │
## └────────────┬─────────────┘   └─────────┬──────────────┘
## │                           │
## └──────────────┬────────────┘
## ▼
## 1

## ┌──────────────────────┐
│ Video Storage & CDN  │
## │ Clips • Assets       │
## └─────────┬────────────┘
## ▼
## ┌──────────────────────┐
## │ Export / Publish     │
│ FFmpeg • Presets     │
## └──────────────────────┘
## 1.2 Live Browser Interaction & Recording Flow
## User Browser
## ┌────────────────────────────┐
│  Live Browser View (WebRTC)│◀──────────────┐
│  Shows AI clicking live    │               │
## └─────────────┬──────────────┘               │
│ WebSocket                    │
## ┌─────────────▼──────────────┐      ┌────────▼──────────┐
│ Browser Agent Controller   │────▶ │ MCP Browser Node  │
│ Action Planning + Control │      │ Real Chrome/FF    │
## └─────────────┬──────────────┘      └────────┬──────────┘
│ Events / DOM / Frames          │
## ┌─────────────▼──────────────┐      ┌────────▼──────────┐
## │ Recorder Service           │◀─────│ Screen Capture    │
## │ Timeline + Segmentation    │      │ + Interaction    │
## └────────────────────────────┘      └───────────────────┘
- Detailed Component API Specifications
2.1 API Gateway
POST /projects
## {
## "source_type":"github",
## "repo_url":"https://github.com/org/app",
## "auth_token":"optional"
## }
Response: project_id
## 2

## 2.2 Prompt & Intent Service
POST /projects/{id}/intent
## {
"prompt":"Create a product demo showing login and analytics dashboard"
## }
## Response:
## {
## "video_type":"product_demo",
## "features": ["login","dashboard","analytics"],
## "audience":"non_technical",
## "style":"professional"
## }
## 2.3 Code Analysis Service
POST /projects/{id}/analyze
## Returns:
## {
"framework":"Next.js",
## "routes": ["/login","/dashboard"],
"components": ["LoginForm","ChartPanel"],
## "auth_required":true
## }
## 2.4 Build & Sandbox Service
POST /projects/{id}/build
## Response:
## {
## "status":"running",
## "preview_url":"https://sandbox.internal/app/123"
## }
## 3

## 2.5 Browser Automation Controller
POST /automation/start
## {
## "project_id":"123",
## "preview_url":"https://sandbox.internal/app/123",
## "execution_plan": [
## {"action":"navigate", "url":"/login"},
## {"action":"type", "selector":"#email", "value":"demo@ai.com"},
## {"action":"click", "selector":"#submit"}
## ]
## }
## 2.6 Live Browser Stream
WebSocket: /stream/{session_id}
## Events:
## {
## "type":"frame",
## "timestamp": 17222333,
## "image":"base64-frame"
## }
## {
## "type":"action",
## "action":"click",
## "selector":"#submit"
## }
## 2.7 Recorder & Segmenter
POST /recordings/{session_id}/finalize
## Response:
## {
## "clips": [
## {
## "clip_id":"c1",
"title":"User Login",
## 4

## "start": 0,
## "end": 12.4
## },
## {
## "clip_id":"c2",
"title":"Dashboard Analytics",
## "start": 12.4,
## "end": 34.8
## }
## ]
## }
2.8 Video Editor API
GET /clips?project_id=123
Returns clip metadata + URLs.
## 2.9 Export & Publish
POST /export
## {
## "clips": ["c1","c2"],
## "format":"mp4",
## "aspect_ratio":"16:9",
## "captions":true,
## "voiceover":"ai"
## }
## Response:
## {
## "video_url":"https://cdn.ai/videos/final.mp4"
## }
- Engineering Notes (15+ yrs perspective)
Live browser view is NOT optional → massive trust & UX win
Separate automation, recording, and rendering services
MCP servers should be stateless & horizontally scalable
Store interaction metadata first, video second (future re-edits)
Treat video creation as a replayable execution, not raw capture
## •
## •
## •
## •
## •
## 5

## 4. Recommended Next Build Order
Repo ingestion + sandbox build
MCP browser automation with live streaming
Recorder + segmentation
Minimal editor (trim + reorder)
Export pipeline
If you want next: - Sequence diagrams (per request type) - MCP tool definitions (Playwright MCP
schema) - Agent reasoning prompts - MVP vs V1 infra sizing
## 1.
## 2.
## 3.
## 4.
## 5.
## 6