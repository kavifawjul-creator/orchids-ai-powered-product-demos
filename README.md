# 🎬 AutoVidAI - AI-Powered Product Demo Video Generation Platform

**Turn your code into interactive video demos instantly.**

AutoVidAI is an autonomous AI-driven platform that generates professional product video demos directly from your codebase. Using advanced LLMs, browser automation, and structured video editing capabilities, it reduces video creation time from hours/days to minutes with minimal manual work.

[![Next.js](https://img.shields.io/badge/Next.js-15.1.3-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)](https://www.typescriptlang.org/)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Backend Services](#-backend-services)
- [Frontend Components](#-frontend-components)
- [API Reference](#-api-reference)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Development Status](#-development-status)
- [Roadmap](#-roadmap)

---

## 🎯 Overview

AutoVidAI empowers developers and product owners to automatically generate professional product videos (demo, walkthrough, explainer, feature ads) from their own codebase or deployed app using:

1. **Repository Ingestion** - Clone and analyze Git repositories
2. **Intent Parsing** - LLM-powered understanding of video requirements
3. **Sandbox Deployment** - Isolated container environments via Daytona
4. **AI Browser Automation** - Autonomous agent navigation with Playwright
5. **Live Browser Streaming** - Real-time WebSocket video feed
6. **Recording & Segmentation** - Automatic clip generation based on milestones
7. **Video Editor** - Timeline-based editing with overlays and narration
8. **Export Pipeline** - FFmpeg-powered video rendering with transitions

---

## ✨ Key Features

### 🤖 Autonomous AI Agent
- **Intelligent Exploration** - AI agents crawl your application to find valuable user journeys
- **Vision-Based Verification** - Uses GPT-4 Vision to verify UI state before actions
- **Self-Healing Execution** - Automatic error detection and recovery strategies
- **Smart State Verification** - LLM-powered precondition checking

### 🎥 Live Browser Streaming
- **WebSocket-Based Streaming** - Real-time browser view at 5-15 FPS
- **JPEG Compression** - Efficient frame delivery with quality presets (low/medium/high)
- **Delta Detection** - Smart frame skipping for unchanged content
- **Action Overlays** - Visual indicators during AI interactions

### 🎬 Video Editor Capabilities
- **Clip Trimming** - Non-destructive trim points for clips
- **Clip Splitting** - Split clips at specific timestamps
- **TTS Narration** - OpenAI TTS with 6 voice options (alloy, echo, fable, onyx, nova, shimmer)
- **Text Overlays** - Customizable text overlays with animations
- **Transition Effects** - Fade, dissolve, wipe, and slide transitions
- **Background Music** - Royalty-free music presets with volume control
- **Aspect Ratios** - 16:9, 9:16, 1:1, 4:3, 21:9 support
- **Click Effects** - Visual ripple/circle effects on click locations
- **Zoom/Pan Effects** - Ken Burns style animations
- **Intro/Outro Generation** - Branded video segments

### 📦 Export Options
- **Multiple Formats** - MP4, WebM, GIF export
- **Resolution Options** - 720p, 1080p, 4K
- **Subtitle Support** - Auto-generated subtitles with styling
- **Watermark** - Configurable text watermark with positioning
- **Progress Tracking** - Real-time export progress via database polling

---

## 🏗️ Architecture

```
┌──────────────────────────┐
│      Web Frontend        │
│  - Repo Upload / URL     │
│  - Prompt Chat UI        │
│  - Live Browser View     │
│  - Video Editor          │
└────────────┬─────────────┘
             │ WebSocket / HTTPS
┌────────────▼─────────────┐
│      API Gateway         │
│  Auth • Rate Limit       │
│  Job Orchestration       │
└────────────┬─────────────┘
             │
┌────────────▼───────────────────────────────────────────┐
│              Core AI Orchestration Layer               │
│                                                        │
│  ┌──────────────┐   ┌─────────────────┐               │
│  │ Intent Parser│→→ │ Execution Planner│               │
│  │  (LLM)       │   │  (Steps & Flows) │               │
│  └──────────────┘   └─────────────────┘               │
│           │                    │                       │
│           ▼                    ▼                       │
│  ┌────────────────┐   ┌────────────────────┐          │
│  │ Code Analyzer  │   │ Browser Agent Ctrl │          │
│  │ (Static + LLM) │   │ (MCP Coordinator)  │          │
│  └────────────────┘   └────────────────────┘          │
└────────────┬───────────────────────────┬──────────────┘
             │                           │
┌────────────▼─────────────┐   ┌─────────▼──────────────┐
│ Build & Sandbox Service  │   │  MCP Browser Servers   │
│ (Daytona / Containers)   │   │ (Playwright / Browser) │
└────────────┬─────────────┘   └─────────┬──────────────┘
             │                           │ Live View + Events
┌────────────▼─────────────┐   ┌─────────▼──────────────┐
│   App Runtime (Preview)  │   │ Recorder & Segmenter   │
│   Internal URL           │   │ Video + Metadata       │
└──────────────────────────┘   └─────────┬──────────────┘
                                         │
                               ┌─────────▼──────────────┐
                               │ Video Storage & CDN    │
                               │ Clips • Assets         │
                               └─────────┬──────────────┘
                                         ▼
                               ┌──────────────────────┐
                               │ Export / Publish     │
                               │ FFmpeg • Presets     │
                               └──────────────────────┘
```

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **Next.js 15.1.3** | React framework with App Router |
| **TypeScript** | Type-safe development |
| **Tailwind CSS 4** | Utility-first CSS framework |
| **Radix UI** | Accessible component primitives |
| **Framer Motion** | Animation library |
| **Supabase Client** | Authentication & database client |
| **React Hook Form** | Form management with Zod validation |
| **Sonner** | Toast notifications |

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI 0.115.6** | Async Python API framework |
| **Playwright 1.49.1** | Browser automation |
| **OpenAI API** | LLM for intent parsing & TTS |
| **Anthropic API** | Alternative LLM provider |
| **Daytona SDK** | Cloud sandbox environments |
| **Celery** | Async task queue (optional) |
| **Redis** | Event bus & caching |
| **FFmpeg** | Video processing & export |
| **Supabase** | PostgreSQL database & auth |
| **SlowAPI** | Rate limiting |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **Supabase** | Database, Auth, Storage |
| **S3 Compatible** | Video/asset storage |
| **WebSockets** | Real-time browser streaming |
| **Daytona** | Sandboxed build environments |

---

## 📁 Project Structure

```
orchids-ai-powered-product-demos/
├── backend/                      # Python FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py         # REST API endpoints (870+ lines)
│   │   │   └── websocket.py      # WebSocket connection management
│   │   ├── core/
│   │   │   ├── config.py         # Environment configuration
│   │   │   ├── auth.py           # Supabase authentication
│   │   │   ├── database.py       # Database connection
│   │   │   ├── events.py         # Event types & bus
│   │   │   └── event_bus.py      # Redis-based event system
│   │   ├── models/
│   │   │   ├── schemas.py        # Pydantic models (Project, Demo, Clip, etc.)
│   │   │   ├── agent.py          # Agent session models
│   │   │   ├── browser.py        # Browser action models
│   │   │   ├── intent.py         # Intent & plan models
│   │   │   ├── project.py        # Project models
│   │   │   ├── recorder.py       # Recording models
│   │   │   └── sandbox.py        # Sandbox configuration models
│   │   ├── services/
│   │   │   ├── agent/            # AI agent execution service
│   │   │   │   └── service.py    # 700+ lines - session management, step execution
│   │   │   ├── browser/          # Browser automation
│   │   │   │   ├── service.py    # MCP browser service with Playwright
│   │   │   │   └── streaming.py  # WebSocket frame streaming
│   │   │   ├── editor/           # Video editing operations
│   │   │   │   └── service.py    # Clip trimming, narration, overlays
│   │   │   ├── export/           # Video export & rendering
│   │   │   │   └── service.py    # FFmpeg operations, transitions, effects
│   │   │   ├── intent/           # LLM intent parsing
│   │   │   │   └── service.py    # Prompt parsing, plan generation
│   │   │   ├── project/          # Project management
│   │   │   │   ├── service.py    # CRUD operations
│   │   │   │   └── analyzer.py   # Code analysis
│   │   │   ├── recorder/         # Recording & segmentation
│   │   │   │   └── service.py    # Milestone-based clip generation
│   │   │   ├── sandbox/          # Daytona sandbox management
│   │   │   │   └── service.py    # Build system detection, workspace management
│   │   │   ├── storage/          # S3/Supabase file storage
│   │   │   ├── audio/            # TTS audio generation
│   │   │   └── subtitle/         # Subtitle generation
│   │   ├── workers/
│   │   │   ├── celery_app.py     # Celery configuration
│   │   │   └── tasks.py          # Demo generation pipeline
│   │   └── main.py               # FastAPI app initialization
│   ├── requirements.txt          # Python dependencies
│   └── .env                      # Backend environment variables
│
├── src/                          # Next.js frontend
│   ├── app/
│   │   ├── page.tsx              # Landing page with hero, features, pricing
│   │   ├── layout.tsx            # Root layout
│   │   ├── (auth)/               # Authentication pages
│   │   │   ├── login/
│   │   │   └── signup/
│   │   ├── dashboard/
│   │   │   ├── page.tsx          # Dashboard with demo grid & stats
│   │   │   ├── layout.tsx        # Dashboard layout with sidebar
│   │   │   ├── new/              # New demo creation
│   │   │   ├── generate/         # Live generation view with WebSocket
│   │   │   ├── demo/             # Demo detail page
│   │   │   ├── demos/            # Demo listing
│   │   │   └── analytics/        # Analytics dashboard
│   │   ├── share/                # Public demo sharing
│   │   └── settings/             # User settings
│   ├── components/
│   │   ├── ui/                   # 50+ Radix-based UI components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── ... (dropdown, tabs, etc.)
│   │   ├── editor/
│   │   │   └── ClipTrimmer.tsx   # Video clip trimming interface
│   │   ├── app-sidebar.tsx       # Dashboard navigation sidebar
│   │   └── ErrorReporter.tsx     # Error boundary component
│   ├── lib/
│   │   ├── supabase/             # Supabase client configuration
│   │   ├── env.ts                # Environment helpers
│   │   └── utils.ts              # Utility functions
│   └── middleware.ts             # Auth middleware
│
├── docs/                         # Documentation
│   ├── prd.md                    # Product Requirements Document
│   ├── Backend Implementation Guide.md
│   ├── Ai Product Video Platform – Architecture & Apis.md
│   ├── AI Prompt Template.md
│   └── AI_agent_context.md
│
├── supabase/
│   └── migrations/               # Database migrations
│
├── public/                       # Static assets
├── package.json                  # Frontend dependencies
├── next.config.ts                # Next.js configuration
└── .env                          # Frontend environment variables
```

---

## 🔧 Backend Services

### 1. Agent Execution Service (`/services/agent/service.py`)
**Purpose:** Orchestrates autonomous browser interaction sessions

**Key Features:**
- Session state machine (INIT → PLANNING → EXECUTING → VERIFYING → RECORDING → FINISHED)
- Step-by-step execution with LLM reasoning
- Vision-based state verification using GPT-4 Vision
- Automatic error recovery and retry logic
- Real-time frame streaming to WebSocket clients

**Key Methods:**
- `create_session()` - Initialize new agent session
- `_start_execution()` - Begin plan execution
- `_execute_step()` - Execute individual browser actions
- `verify_state()` - LLM-powered UI state verification
- `_execute_recovery()` - Handle failures with retry strategies

### 2. Browser Service (`/services/browser/service.py`)
**Purpose:** MCP-compatible browser automation with Playwright

**Key Features:**
- Browser session management with configurable viewports
- Full action support: navigate, click, type, scroll, hover, keypress
- Screenshot capture with JPEG compression
- Live frame streaming at configurable FPS
- Event callbacks for recording integration

**MCP Tools Implemented:**
- `browser_navigate` - Navigate to URL
- `browser_click` - Click elements
- `browser_type` - Type text input
- `browser_screenshot` - Capture screenshots
- `browser_scroll` - Scroll page
- `browser_wait` - Wait for conditions
- `browser_hover` - Hover elements
- `browser_keypress` - Keyboard input
- `browser_get_page_info` - Page metadata
- `browser_get_elements` - Query elements

### 3. Intent Planning Service (`/services/intent/service.py`)
**Purpose:** LLM-powered intent parsing and execution plan generation

**Key Features:**
- Video type classification (demo, explainer, walkthrough, ad)
- Feature extraction from user prompts
- Step-by-step execution plan generation
- Milestone definition for clip segmentation
- Support for OpenAI and Anthropic models

### 4. Sandbox Service (`/services/sandbox/service.py`)
**Purpose:** Daytona-based isolated build environments

**Supported Build Systems:**
- Next.js (npm install && npm run dev)
- React/Vite (npm install && npm run dev)
- Vue/Nuxt (npm install && npm run dev)
- Express (npm install && npm start)
- FastAPI (pip install && uvicorn)
- Django (pip install && manage.py runserver)

**Key Features:**
- Automatic build system detection
- Preview URL generation
- Workspace lifecycle management
- Cleanup and recovery

### 5. Recorder Service (`/services/recorder/service.py`)
**Purpose:** Recording session management and clip segmentation

**Key Features:**
- Recording session tracking
- Event and milestone logging
- FFmpeg-based clip extraction
- Automatic clip upload to storage

### 6. Editor Service (`/services/editor/service.py`)
**Purpose:** Video editing operations

**Key Features:**
- Clip trimming (non-destructive)
- Clip splitting at timestamps
- TTS narration generation with 6 voices
- Text overlay management
- Audio duration detection

### 7. Export Service (`/services/export/service.py`)
**Purpose:** Video rendering and export pipeline

**Key Features:**
- FFmpeg-based video processing
- Format conversion (MP4, WebM, GIF)
- Resolution scaling (720p, 1080p, 4K)
- Transition effects (fade, dissolve, wipe, slide)
- Background music integration
- Watermark overlay
- Aspect ratio conversion
- Click effect animations
- Zoom/pan effects
- Intro/outro generation
- Progress tracking via database

---

## 🎨 Frontend Components

### Landing Page (`/src/app/page.tsx`)
- **Hero Section** - Animated headline with CTA buttons
- **Features Grid** - 6 capability cards with icons
- **How It Works** - 4-step process visualization
- **Solutions** - Startup/Enterprise/Teams pricing tiers
- **Pricing Plans** - Free, Pro ($49/mo), Enterprise
- **Testimonials** - Customer quote cards
- **CTA Section** - Final conversion section

### Dashboard (`/src/app/dashboard/page.tsx`)
- **Stats Cards** - Total demos, active agents, generation time, views
- **Workspace Switcher** - Multi-workspace support
- **Demo Grid** - Thumbnail cards with status badges
- **Demo Actions** - Delete, share, privacy settings
- **Live Status Indicators** - Real-time execution status

### Generate Page (`/src/app/dashboard/generate/page.tsx`)
- **Live Browser View** - WebSocket-connected frame display
- **Quality Presets** - Low/Medium/High streaming quality
- **Agent Logs** - Real-time action/reasoning logs
- **Progress Indicators** - Step and milestone tracking
- **Fullscreen Mode** - Expanded browser view

### UI Component Library (`/src/components/ui/`)
50+ Radix-based components including:
- Button, Card, Dialog, Dropdown
- Form, Input, Label, Select
- Tabs, Accordion, Navigation
- Progress, Slider, Switch
- Toast, Tooltip, Popover
- And many more...

---

## 📡 API Reference

### Project Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/projects` | Create new project |
| GET | `/api/v1/projects` | List all projects |
| GET | `/api/v1/projects/{id}` | Get project details |
| POST | `/api/v1/projects/{id}/build` | Start project build |
| DELETE | `/api/v1/projects/{id}` | Delete project |

### Demo Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/demos/generate` | Start demo generation |
| GET | `/api/v1/demos/{id}` | Get demo details |
| GET | `/api/v1/demos/{id}/clips` | Get demo clips |
| GET | `/api/v1/demos/{id}/plan` | Get execution plan |
| GET | `/api/v1/demos/{id}/status` | Get generation status |
| POST | `/api/v1/demos/{id}/export` | Export demo video |
| POST | `/api/v1/demos/{id}/export/advanced` | Advanced export with options |
| GET | `/api/v1/demos/{id}/export/{export_id}/status` | Get export progress |

### Editor Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/demos/{id}/clips/{clip_id}/trim` | Trim clip |
| POST | `/api/v1/demos/{id}/clips/{clip_id}/split` | Split clip |
| POST | `/api/v1/demos/{id}/clips/{clip_id}/narration` | Generate narration |
| POST | `/api/v1/demos/{id}/narration/preview` | Preview TTS |
| POST | `/api/v1/demos/{id}/clips/{clip_id}/overlays` | Add text overlay |
| DELETE | `/api/v1/demos/{id}/clips/{clip_id}/overlays/{overlay_id}` | Remove overlay |
| GET | `/api/v1/editor/voices` | List TTS voices |
| GET | `/api/v1/editor/music-presets` | List music presets |
| GET | `/api/v1/editor/transition-types` | List transitions |
| GET | `/api/v1/editor/aspect-ratios` | List aspect ratios |
| GET | `/api/v1/editor/click-effects` | List click effects |
| GET | `/api/v1/editor/zoom-effects` | List zoom effects |
| POST | `/api/v1/demos/{id}/intro` | Generate intro |
| POST | `/api/v1/demos/{id}/outro` | Generate outro |

### Session Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/sessions/{id}` | Get session details |
| GET | `/api/v1/sessions/{id}/status` | Get session status |
| GET | `/api/v1/sessions/{id}/screenshot` | Get current screenshot |
| POST | `/api/v1/sessions/{id}/stop` | Stop session |

### Sandbox Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/sandboxes/{id}` | Get sandbox details |
| DELETE | `/api/v1/sandboxes/{id}` | Destroy sandbox |
| POST | `/api/v1/sandboxes/{id}/extend` | Extend sandbox lifetime |

### WebSocket Endpoints
| Endpoint | Description |
|----------|-------------|
| `/ws/{channel}` | General event subscription |
| `/ws/session:{session_id}` | Agent session updates |
| `/ws/stream/{session_id}` | Browser frame streaming |

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- FFmpeg installed and in PATH
- Supabase account
- OpenAI API key
- Daytona account (for sandbox features)

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
# From project root
npm install

# Copy environment file
cp .env.example .env.local
# Edit .env.local with your Supabase credentials

# Start development server
npm run dev
```

### Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔐 Environment Variables

### Backend (`.env`)
```env
# Core
DEBUG=true
API_SECRET_KEY=your-secret-key

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# AI
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# Daytona
DAYTONA_API_KEY=your-daytona-key
DAYTONA_API_URL=https://api.daytona.io

# Storage (Optional)
S3_BUCKET_NAME=autovid-recordings
S3_ACCESS_KEY=xxx
S3_SECRET_KEY=xxx

# Redis (Optional)
REDIS_URL=redis://localhost:6379
```

### Frontend (`.env.local`)
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

---

## ✅ Development Status

### Completed Features

#### Backend
- ✅ FastAPI application with middleware (auth, logging, rate limiting)
- ✅ Project CRUD operations with Supabase
- ✅ Intent parsing with OpenAI/Anthropic
- ✅ Execution plan generation with milestones
- ✅ Daytona sandbox integration
- ✅ Playwright browser automation
- ✅ Agent execution with state machine
- ✅ Vision-based state verification
- ✅ WebSocket live streaming
- ✅ Recording session management
- ✅ Clip generation from milestones
- ✅ Editor operations (trim, split, overlays)
- ✅ TTS narration with 6 voices
- ✅ FFmpeg export pipeline
- ✅ Transition effects
- ✅ Background music integration
- ✅ Aspect ratio support
- ✅ Click effect animations
- ✅ Zoom/pan effects
- ✅ Intro/outro generation
- ✅ Export progress tracking

#### Frontend
- ✅ Landing page with animations
- ✅ Authentication (login/signup)
- ✅ Dashboard with demo management
- ✅ Live generation view with WebSocket
- ✅ Quality preset controls
- ✅ Agent action logs
- ✅ Demo sharing with privacy controls
- ✅ Workspace management

---



---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 👥 Contributors

Built with ❤️ by the AutoVidAI Team

---

## 📞 Support

For questions or support, please open an issue or contact the development team.
