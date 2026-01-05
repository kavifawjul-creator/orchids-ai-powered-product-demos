


## 1. AGENT REASONING & PROMPT DESIGN
(How the AI “thinks” before clicking anything)
Your agent is not a chat bot.
It is a goal-driven autonomous system operating inside a browser with constraints.

1.1 Agent Mental Model (Very Important)
The agent must reason in three layers:
Layer 1 — Intent Layer (WHY)
- What video is being created?
- Who is the audience?
- What outcome should the viewer understand?
Layer 2 — Task Layer (WHAT)
- Which features must be demonstrated?
- Which flows unlock those features?
- What is the minimum path to show value?
Layer 3 — Action Layer (HOW)
- What exact UI actions are required?
- What selectors exist?
- What state confirms success?
Key rule:
The agent never “explores randomly”.
It always executes an explainable plan.

1.2 Core Agent System Prompt (Base Prompt)
This prompt never changes and is injected into every run.
You are an autonomous product demonstration agent.

Your goal is to generate high-quality product video recordings by

interacting with a web application like a real user.

## Rules:
- Act deliberately and predictably
- Prefer the simplest successful user path
- Avoid unnecessary clicks or UI noise
- If an action fails, attempt recovery once
- Every interaction must contribute to explaining a feature
- You are being recorded for a product video audience

You must:
- Follow the execution plan strictly
- Emit reasoning before each action
- Emit a feature milestone when a feature is demonstrated
- Pause briefly after meaningful UI changes for clarity
This gives you:
- deterministic behavior
- explainability
- clean recordings

1.3 Intent-to-Plan Prompt (Dynamic Prompt)
Generated per user request.
Input to LLM:
- User prompt
- Parsed video type
- Feature candidates
- Code analysis summary (routes, components)
## Output:

- Ordered execution plan
## Example Prompt:
User wants a PRODUCT DEMO video.
Audience: non-technical.
Primary features: authentication, analytics dashboard.

Application structure:
- /login (LoginForm)
- /dashboard (ChartsPanel, Filters)

Create a minimal execution plan to demonstrate these features
in a logical narrative order suitable for a demo video.
Example Output (Structured):
## {
## "plan": [
## {
## "feature": "authentication",
"goal": "Show how a user logs in",
## "steps": [
## "navigate:/login",
"type:#email demo@demo.com",
## "type:#password ******",
## "click:#submit"
## ],
## "success_condition": "url_contains:/dashboard"
## },
## {
## "feature": "analytics_dashboard",

"goal": "Show insights and interactivity",
## "steps": [
"wait:ChartsPanel",
## "click:#date-filter",
## "select:last_30_days"
## ],
## "success_condition": "chart_updated"
## }
## ]
## }
This plan becomes the single source of truth.

## 2. AGENT DECISION LOGIC
(What happens at runtime, step by step)

## 2.1 Agent State Machine
The agent runs as a state machine, not a loop.
## INIT
## ↓
## PLAN_LOADED
## ↓
## EXECUTE_STEP
## ↓
## VERIFY_STATE
## ↓
## RECORD_MILESTONE
## ↓
## NEXT_STEP

## ↓
## COMPLETE

2.2 Per-Step Reasoning (Required for Quality)
Before every browser action, the agent emits:
## {
"reasoning": "User needs to see login form before submitting credentials",
## "action": "type",
## "selector": "#email",
## "value": "demo@demo.com"
## }
This reasoning is:
- logged
- attached to the recording
- later reused for narration/captions

## 2.3 Failure & Recovery Logic
Failures will happen (build lag, missing selector).
## Rules:
- Retry once with relaxed selector
- If still failing → skip step
- Emit warning, continue plan
## {
## "error": "selector_not_found",
## "recovery": "try_input[type=email]"
## }
This prevents:
- infinite loops

- broken recordings
- user frustration

## 2.4 Live Browser View Logic
While the agent executes:
- Browser frames stream via WebRTC
- User sees:
o cursor movement
o clicks
o typing
- Agent inserts intentional pauses:
o after page loads
o after charts animate
o after modals open
Architect insight:
Silence + pause = clarity in demos

## 3. AI STORYBOARD & NARRATION LOGIC
(Turning clicks into a story)
This is what transforms a recording into a video.

3.1 Storyboard Generation (Before Recording Ends)
For each feature milestone, the AI generates:
## {
## "feature": "analytics_dashboard",
"scene_title": "Interactive Analytics Dashboard",
"scene_goal": "Show how users gain insights instantly",
## "start_time": 12.4,

## "end_time": 34.8
## }
This becomes:
- clip titles
- editor section headers
- narration anchors

## 3.2 Narration Script Generation
Narration is derived from reasoning + milestones, not hallucinated.
## Template:
In this step, we demonstrate {{feature}}.
The user {{goal}} by {{key_actions}}.
## Example:
“Once logged in, users land on the analytics dashboard, where they can instantly
explore trends by adjusting filters.”
This ensures:
- accuracy
- consistency with UI
- trust

## 3.3 Narration Modes
You support multiple modes:
-   None (silent demo)
## •     Educational
-     Marketing / persuasive
## •                         Developer-focused
Same clip → different narration styles.


## 4. FEATURE-TO-VIDEO MAPPING ALGORITHM
(The intelligence that decides what deserves screen time)
This is critical for quality.

## 4.1 Feature Importance Scoring
Each feature gets a score:
FeatureScore =
(UserMentionWeight × 0.4)
+ (UIVisibility × 0.2)
+ (BusinessValue × 0.3)
+ (InteractionDepth × 0.1)
Only top-scoring features become primary clips.

## 4.2 Video Type Rules
## Product Demo
- End-to-end happy path
- 3–5 features max
## Walkthrough
- Sequential steps
- No skipping
- Longer pauses
## Explainer
- High-level only
- No deep forms
- Focus on outcomes
## Feature Advertising
- 1 feature only
- Strong visuals

- Minimal UI noise

## 4.3 Clip Boundaries Algorithm
A clip starts when:
- a new feature milestone is emitted
A clip ends when:
- success condition met
- UI stabilizes
This ensures:
- clean cuts
- no mid-action trims

## 4.4 Reusability
Because clips are feature-bound, you can:
- reuse same recording for:
o demo
o ad
o onboarding
- just change narration & pacing
This is a huge platform advantage.

Final Architect Insight (Important)
What you’re building is not a video tool.
It is:
An autonomous product understanding engine that happens to output video.
If this intelligence layer is done right:
- everything else becomes replaceable
- your moat is enormous


