<div align="center">

# ◈ J A R V I S

### **Just A Rather Very Intelligent System**

*A modular Windows desktop AI assistant built to understand natural-language commands and turn them into real actions.*

<p>
  <img src="assets/jarvis-banner.gif" alt="JARVIS animated banner" width="900">
</p>

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Playwright](https://img.shields.io/badge/Playwright-Browser%20Automation-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev/)
[![Groq](https://img.shields.io/badge/LLM-Groq-FF4F00?style=for-the-badge)](https://groq.com/)
[![Status](https://img.shields.io/badge/JARVIS-Stage%204%20in%20progress-7B61FF?style=for-the-badge)](#-project-status)

</div>

---

## ⚡ What is JARVIS?

JARVIS is an evolving **desktop AI agent for Windows**. The project started with conversational AI and is being expanded into a practical computer-control system capable of interacting with applications, the filesystem, keyboard/mouse input, and a web browser.

The architecture is intentionally modular:

```text
                         ┌──────────────────────┐
                         │        USER          │
                         │ "Open Brave..."      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       JARVIS         │
                         │  Agent / Orchestrator│
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     LLM PROVIDER     │
                         │  Groq / configurable │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │      TOOL REGISTRY   │
                         └──────┬─────┬─────┬───┘
                                │     │     │
                         ┌──────▼┐ ┌──▼───┐ ┌▼────────┐
                         │Windows│ │Files │ │  Brave  │
                         │ Tools │ │Tools │ │ Browser │
                         └──────┘ └──────┘ └─────────┘
```

> **Design principle:** the model decides *what* needs to happen; deterministic tools are responsible for *how* the action is executed and validated.

---

## ✨ Current Capabilities

### 🧠 Agent & Conversation
- Natural-language interaction with JARVIS.
- Configurable AI-provider layer.
- Conversation history and agent/tool loop.
- Structured tool calls and explicit tool results.

### 🖥️ Windows Control
- Launch desktop applications.
- Keyboard interaction.
- Mouse interaction.
- Controlled filesystem operations.
- Validation and safety checks around computer actions.

### 🌐 Brave Browser Automation
- Launch/reuse Brave.
- Navigate to websites.
- Search the web through the browser.
- Read page content.
- Click and fill browser elements.
- Scroll pages.
- Manage multiple tabs.
- Go back / forward / refresh.
- Keyboard actions such as `Space`, `Enter`, `Escape`, and arrow keys.
- Multi-step browser workflows.

### 🛡️ Reliability & Safety
- Browser state synchronization.
- Stale/closed-page handling.
- Tool execution limits.
- Structured failures instead of silent false success.
- Browser content treated as untrusted data.
- No password/token/cookie extraction.
- High-impact actions can require user confirmation.

---

# 📊 Project Status

<!-- JARVIS_STATUS_START -->
### Current build

**Stage 4 — Browser Integration & Automation** · 🟡 **IN PROGRESS**

| Stage | Area | Status |
|:---:|---|:---:|
| 1 | Core Agent & Identity | 🟢 **COMPLETE** |
| 2 | Application Launching & Tool Registry | 🟢 **COMPLETE** |
| 3 | Windows Computer Control | 🟢 **COMPLETE** |
| 4 | Brave Browser Automation | 🟡 **IN PROGRESS** |
| 5 | Voice / Wake Word | ⚪ **PLANNED** |
| 6 | Persistent Background Assistant | ⚪ **PLANNED** |
| 7 | Advanced Computer Vision | ⚪ **PLANNED** |
| 8 | Advanced Multi-App Workflows | ⚪ **PLANNED** |
| 9 | Memory & Personalization | ⚪ **PLANNED** |
| 10 | Full JARVIS Experience | ⚪ **PLANNED** |

**Progress:** `████████████░░░░░░░░` **40%**

**Last repository update:** `Generated automatically by GitHub Actions`

<!-- JARVIS_STATUS_END -->

> **Automatic status:** every push can run the repository's status workflow. The workflow updates the generated status block, records the latest commit/test state, and commits the refreshed README when the status changes. Stage completion is intentionally controlled through `.github/jarvis_status.json` so the automation never falsely declares a stage complete just because a folder or file exists.

---

## 🧭 Roadmap

```mermaid
flowchart LR
    S1["01<br/>Core Agent"] --> S2["02<br/>App Launching"]
    S2 --> S3["03<br/>Computer Control"]
    S3 --> S4["04<br/>Browser Automation"]
    S4 --> S5["05<br/>Voice + Wake Word"]
    S5 --> S6["06<br/>Background Assistant"]
    S6 --> S7["07<br/>Computer Vision"]
    S7 --> S8["08<br/>Advanced Workflows"]
    S8 --> S9["09<br/>Memory"]
    S9 --> S10["10<br/>Full JARVIS"]

    classDef done fill:#123d2a,stroke:#35d07f,color:#fff;
    classDef active fill:#3d315f,stroke:#a78bfa,color:#fff;
    classDef planned fill:#222831,stroke:#6b7280,color:#fff;

    class S1,S2,S3 done;
    class S4 active;
    class S5,S6,S7,S8,S9,S10 planned;
```

### Stage 1 — Core Agent
Foundation, provider abstraction, identity, configuration and conversational history.

### Stage 2 — Application Control
Tool-based application launching and an extensible tool registry.

### Stage 3 — Computer Control
Keyboard, mouse, filesystem and controlled Windows interaction.

### Stage 4 — Browser Automation
Brave control, navigation, tabs, page reading, interaction and multi-step browser tasks.

### Stage 5 — Voice Interface
Wake-word detection, speech-to-text and text-to-speech so JARVIS can respond without a terminal prompt.

### Stage 6 — Persistent Background Assistant
Run JARVIS as a background Windows process/service with startup and tray controls.

### Stage 7 — Computer Vision
Use screenshots/vision to understand UI state when DOM/API-level automation is insufficient.

### Stage 8 — Advanced Workflows
Longer multi-application tasks with planning, verification and recovery.

### Stage 9 — Memory & Personalization
Useful long-term preferences, task context and configurable memory.

### Stage 10 — Full JARVIS Experience
A polished voice-first desktop assistant combining the previous capabilities into one cohesive system.

---

# 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                         JARVIS                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Input                                                 │
│      │                                                      │
│      ▼                                                      │
│  Agent / Orchestrator                                       │
│      │                                                      │
│      ├──────────────► LLM Provider                          │
│      │                   │                                  │
│      │                   ▼                                  │
│      │              Tool Selection                          │
│      │                   │                                  │
│      ▼                   ▼                                  │
│  Tool Registry ──────────────────────────────────────────┐  │
│      │             │              │                      │  │
│      ▼             ▼              ▼                      ▼  │
│  Windows       Filesystem      Browser                Future │
│  Tools         Tools           Tools                  Tools  │
│      │             │              │                      │  │
│      └─────────────┴──────────────┴──────────────────────┘  │
│                            │                                │
│                            ▼                                │
│                      Tool Result                            │
│                            │                                │
│                            ▼                                │
│                         Agent                               │
│                            │                                │
│                            ▼                                │
│                         Response                            │
└─────────────────────────────────────────────────────────────┘
```

The separation between **LLM reasoning** and **deterministic tools** is important: it lets JARVIS change models without rewriting every computer-control capability.

---

# 🚀 Quick Start

## 1. Clone the repository

```powershell
git clone <YOUR_REPOSITORY_URL>
cd JARVIS
```

## 2. Create a virtual environment

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run JARVIS directly through the virtual environment's Python executable instead.

### Windows CMD

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

## 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure environment variables

Copy the template:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```env
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
LOG_LEVEL=INFO
```

**Never commit `.env` or expose your API key.**

Make sure `.gitignore` contains:

```gitignore
.env
venv/
__pycache__/
.pytest_cache/
```

---

# ▶️ Run JARVIS

## CLI

```powershell
.\venv\Scripts\python -m backend.main
```

## FastAPI server

```powershell
.\venv\Scripts\python -m uvicorn backend.main:app --reload
```

> If your project entry point changes, keep the command synchronized with the actual `backend.main` implementation.

---

# 🧪 Testing

Run the full test suite:

```powershell
.\venv\Scripts\python -m pytest tests/ -v
```

A useful development loop is:

```powershell
git pull
.\venv\Scripts\python -m pytest tests/ -v
```

Then start JARVIS and perform the relevant manual acceptance tests.

---

# 🔧 Development

A typical project layout:

```text
JARVIS/
├── backend/
│   ├── main.py
│   ├── agent/
│   ├── providers/
│   └── tools/
├── tests/
├── scripts/
├── assets/
├── .github/
│   └── workflows/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

The exact structure may evolve as new stages are implemented.

---

# 🔄 Automatic GitHub Status

The repository includes a GitHub Actions workflow:

```text
git push
   │
   ▼
GitHub Actions
   │
   ├── Install dependencies
   ├── Run tests
   ├── Read .github/jarvis_status.json
   ├── Calculate stage progress
   ├── Update README status block
   └── Commit status update
```

The workflow uses the repository's built-in `GITHUB_TOKEN`; no personal GitHub token is required.

### Update stage status

Edit:

```text
.github/jarvis_status.json
```

Example:

```json
{
  "stages": [
    {"id": 1, "name": "Core Agent & Identity", "status": "complete"},
    {"id": 2, "name": "Application Launching & Tool Registry", "status": "complete"},
    {"id": 3, "name": "Windows Computer Control", "status": "complete"},
    {"id": 4, "name": "Brave Browser Automation", "status": "in_progress"},
    {"id": 5, "name": "Voice / Wake Word", "status": "planned"},
    {"id": 6, "name": "Persistent Background Assistant", "status": "planned"},
    {"id": 7, "name": "Advanced Computer Vision", "status": "planned"},
    {"id": 8, "name": "Advanced Multi-App Workflows", "status": "planned"},
    {"id": 9, "name": "Memory & Personalization", "status": "planned"},
    {"id": 10, "name": "Full JARVIS Experience", "status": "planned"}
  ]
}
```

After pushing:

```powershell
git add .
git commit -m "Update JARVIS stage"
git push
```

GitHub Actions regenerates the README status section.

### Status values

Use only:

```text
complete
in_progress
planned
blocked
```

This makes the status automation predictable and prevents accidental "100% complete" claims.

---

# 🔐 Security

JARVIS is intended to operate with meaningful access to a Windows machine, so security is a core part of the architecture.

**Never commit:**

- API keys
- passwords
- authentication tokens
- cookies
- private credentials
- personal `.env` files

Browser pages should be treated as **untrusted input**. Text displayed by a webpage must not be allowed to override JARVIS's trusted instructions or authorize unrelated computer actions.

High-impact actions should require appropriate confirmation.

---

# 🎯 Project Philosophy

JARVIS is not intended to be just a chatbot with a fancy name.

The long-term goal is an assistant that can:

```text
UNDERSTAND
    ↓
PLAN
    ↓
SELECT TOOLS
    ↓
ACT
    ↓
OBSERVE
    ↓
VERIFY
    ↓
RECOVER
    ↓
RESPOND
```

Every stage expands the same underlying agent architecture rather than creating a collection of unrelated scripts.

---

# 🌌 Long-Term Vision

The final JARVIS experience is envisioned as a **voice-first Windows assistant** that can understand a natural request, determine the necessary actions, operate applications and websites, verify what happened, and report the result clearly.

Example:

> **User:** "Hello JARVIS, open Brave, find the official Python website, check the latest release information, and tell me what you found."

The target architecture is:

```text
Voice
  ↓
Wake Word
  ↓
Speech-to-Text
  ↓
JARVIS Agent
  ↓
LLM
  ↓
Tool Planning
  ↓
Brave / Windows / Files / Vision
  ↓
Verification
  ↓
Text-to-Speech
  ↓
User
```

---

# 🤝 Contributing

This is an evolving project.

When adding a new capability:

1. Keep it modular.
2. Add it to the existing tool registry.
3. Validate inputs.
4. Return structured tool results.
5. Add automated tests.
6. Update the relevant stage status.
7. Keep secrets out of source control.

---

<div align="center">

### ◈ JARVIS IS BEING BUILT ONE CAPABILITY AT A TIME ◈

`UNDERSTAND` → `ACT` → `VERIFY` → `IMPROVE`

⭐ **Star the repository if you want to follow the build.**

</div>
