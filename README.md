<p align="center">
  <img src="assets/qelvori-banner.png" alt="QELVORI AI Research Intelligence" width="100%">
</p>

<br>


# QELVORI — AI Research Intelligence

An AI-powered research intelligence platform that automates information discovery, content extraction, analysis, evidence verification, and PDF report generation.

## Overview

QELVORI is built with Python and FastAPI. It uses locally hosted AI models through Ollama to analyze research material and produce structured reports.

## Key Features

- **Automated Research:** Searches multiple online sources for relevant information.
- **Content Extraction:** Extracts information from web pages and PDF documents.
- **AI-Powered Analysis:** Uses Qwen 3 through Ollama.
- **Evidence Verification:** Performs AI-assisted checks on claims and supporting sources.
- **Citation Validation:** Validates references against collected source IDs.
- **PDF Generation:** Produces downloadable research reports.
- **Interactive Dashboard:** Monitors research progress through a web interface.
- **REST API:** Provides endpoints for research tasks and report access.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| AI Runtime | Ollama |
| Language Model | Qwen 3 (4B) |
| Frontend | HTML, CSS, JavaScript |
| PDF Processing | PyMuPDF, ReportLab |
| Web Extraction | BeautifulSoup |
| Testing | Pytest |

## Architecture

```text
QELVORI
│
├── agents/
│   └── research_agent.py
│
├── core/
│   ├── ai_analyzer.py
│   ├── evidence_verifier.py
│   └── report_generator.py
│
├── tools/
│   ├── search_tool.py
│   └── content_extractor.py
│
├── static/
│   └── index.html
│
├── tests/
│   ├── pytest.ini
│   └── test_api.py
│
├── main.py
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10 or later
- Git
- Ollama
- Qwen 3 (4B) model

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/vinodxkumar345-png/qelvori-ai-research-agent.git
cd qelvori-ai-research-agent
```

### 2. Create a virtual environment

```powershell
py -m venv .venv
```

### 3. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
py -m pip install -r requirements.txt
```

### 5. Set up the AI model

Install Ollama, then run:

```powershell
ollama pull qwen3:4b
```

Ensure Ollama is running before starting a research task.

### 6. Start the application

```powershell
py -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Access QELVORI

| Service | Address |
|---|---|
| Dashboard | http://127.0.0.1:8000 |
| API Documentation | http://127.0.0.1:8000/docs |
| Health Check | http://127.0.0.1:8000/health |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Application dashboard |
| GET | `/health` | Application health check |
| POST | `/api/research` | Start a research task |
| GET | `/api/research/{job_id}` | Retrieve research task status |
| GET | `/api/reports` | Retrieve available reports |

## Running Tests

```powershell
py -m pytest -q
```

## Important Notes

- QELVORI uses a locally hosted Ollama model for AI analysis.
- Ollama must be running for AI-powered research features.
- Evidence verification is AI-assisted and does not guarantee complete factual accuracy.
- Always review generated findings against their original sources.

## Project Vision

QELVORI aims to bring automated research, AI-powered analysis, evidence checking, and structured reporting together in one platform.

---

**QELVORI — Turning information into structured intelligence.**