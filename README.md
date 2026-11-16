# QELVORI â€“ AI Research Intelligence

QELVORI is an AI-powered research assistant built with Python and FastAPI. It automates the research workflow by collecting information from online sources, extracting content, analyzing findings with a locally hosted language model, and generating structured PDF reports.

## Features

- **Automated Research:** Searches multiple sources for information related to a given topic.
- **Content Extraction:** Extracts relevant content from supported web pages and PDF documents.
- **AI-Powered Analysis:** Uses the Qwen 3 model through Ollama to analyze collected information.
- **Evidence Verification:** Performs AI-assisted checks on claims and supporting source material.
- **Citation Validation:** Checks whether cited source IDs correspond to collected sources.
- **PDF Report Generation:** Generates downloadable research reports.
- **Web Dashboard:** Provides a dark-themed interface to submit topics and monitor research progress.
- **REST API:** Exposes research functionality through FastAPI endpoints.

## Technology Stack

- Python
- FastAPI
- Ollama
- Qwen 3 (4B)
- HTML, CSS and JavaScript
- ReportLab
- PyMuPDF
- BeautifulSoup
- Pytest

## Requirements

Before running QELVORI, install:

- Python 3.10 or later
- Git
- Ollama
- Qwen 3 (4B) model

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/qelvori-ai-research-agent.git
cd qelvori-ai-research-agent
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Create a virtual environment

```powershell
py -m venv .venv
```

### 3. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
py -m pip install -r requirements.txt
```

### 5. Set up Ollama

Install Ollama and download the required model:

```powershell
ollama pull qwen3:4b
```

Make sure the Ollama service is running before starting a research task.

### 6. Start QELVORI

```powershell
py -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Access the Application

Once the server starts, open:

**Dashboard:** http://127.0.0.1:8000

**API Documentation:** http://127.0.0.1:8000/docs

**Health Check:** http://127.0.0.1:8000/health

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Application dashboard |
| GET | `/health` | Application health check |
| POST | `/api/research` | Start a research task |
| GET | `/api/research/{job_id}` | Retrieve research task status |
| GET | `/api/reports` | Retrieve available reports |

## Project Structure

```text
qelvori-ai-research-agent/
â”‚
â”œâ”€â”€ agents/
â”‚   â””â”€â”€ research_agent.py
â”‚
â”œâ”€â”€ core/
â”‚   â”œâ”€â”€ ai_analyzer.py
â”‚   â”œâ”€â”€ evidence_verifier.py
â”‚   â””â”€â”€ report_generator.py
â”‚
â”œâ”€â”€ tools/
â”‚   â”œâ”€â”€ search_tool.py
â”‚   â””â”€â”€ content_extractor.py
â”‚
â”œâ”€â”€ static/
â”‚   â””â”€â”€ index.html
â”‚
â”œâ”€â”€ tests/
â”‚
â”œâ”€â”€ main.py
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ .gitignore
â””â”€â”€ README.md
```

## Running Tests

Run the automated test suite:

```powershell
py -m pytest -q
```

## Important Notes

- QELVORI uses a locally hosted Ollama model for AI analysis.
- Ollama must be installed and running for AI-powered research features.
- AI-assisted evidence verification does not guarantee that every claim is factually correct.
- Always review generated research and its original sources before relying on the findings.

## Project Goal

QELVORI aims to simplify research by combining automated information retrieval, AI-powered analysis, evidence checking, and structured report generation in one application.
