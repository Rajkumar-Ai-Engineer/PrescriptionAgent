# PrescriptionAgent: AI-Powered Prescription Assistance

## Overview

**PrescriptionAgent** is an intelligent assistant designed to parse, verify, and explain medical prescriptions. The system processes prescription data, cross-checks drug interactions and dosages, and provides patient-friendly explanations and clinical summaries through an interactive interface.

---

## Repository Structure

```text
PrescriptionAgent/
├── .sf/orgs/.../metadata-catalog/   # Salesforce / Agentforce metadata configurations
├── img/                             # Diagrams, architecture flowcharts, and UI assets
├── notebooks/                       # Prototyping, prompt testing, and pipeline evaluation
├── src/                             # Core agent modules, tools, and orchestration logic
├── .gitignore                       # Ignored build and runtime artifacts
├── .python-version                  # Targeted Python runtime definition
├── README.md                        # Project summary and documentation
├── app.py                           # Frontend / UI entry point (Streamlit or FastAPI)
├── main.py                          # Pipeline CLI runner and orchestrator entry point
├── pyproject.toml                   # Project metadata and packaging configuration
├── requirements.txt                 # Runtime dependencies
└── verify.md                        # Verification checklist and testing instructions

```

---

## Architecture & Workflow

```text
[Prescription Input] ──► [OCR / Extraction] ──► [Agent Orchestrator (src/)]
(Image / PDF / Text)                               │
                                                   ├──► Drug Verification & Interaction Check
                                                   ├──► Salesforce / CRM Integration (.sf/)
                                                   └──► Patient Guidance Generation
                                                           │
                                                           ▼
                                                [UI (app.py) / Output]

```

1. **Input Ingestion**: Accepts raw prescription text, structured inputs, or digital clinical notes via `app.py`.
2. **Clinical Parsing & Entity Extraction**: Identifies drug names, dosage levels, administration frequencies, and duration.
3. **Agent Verification (`src/`)**: Validates extracted medication schedules against safety rules, potential contraindications, and interaction catalogs.
4. **Platform Integration (`.sf/`)**: Bridges medical recommendations or prescription events with Salesforce Health Cloud / CRM metadata for clinical record tracking.
5. **Guidance Delivery**: Formats intake schedules, dosage warnings, and patient instructions into clear, non-technical language.

---

## Installation & Setup

### Prerequisites

* Python 3.10+ (matching `.python-version`)
* `git` installed
* Access credentials for relevant LLM or platform APIs (e.g., OpenAI, Salesforce Connected App if integrated)

### 1. Clone the Repository

```bash
git clone https://github.com/Rajkumar-Ai-Engineer/PrescriptionAgent.git
cd PrescriptionAgent

```

### 2. Environment Setup

```bash
# Set up virtual environment
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate

```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt

```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_api_key_here
# Salesforce / Agentforce credentials if integrating CRM workflows:
SF_INSTANCE_URL=https://your-instance.salesforce.com
SF_ACCESS_TOKEN=your_token_here

```

---

## Usage Guide

### Running the Web Interface

Launch the interactive application:

```bash
python app.py

```

*(If built with Streamlit, run `streamlit run app.py`)*

### Running Pipeline Directly

Execute the primary agent orchestration flow via CLI:

```bash
python main.py

```

### Verification & Testing

Follow the step-by-step test scenarios in `verify.md`:

```bash
pytest

```

---

## Core Components

* **`src/`**: Contains core agent classes, prompt templates, tool declarations, and schema validations.
* **`.sf/`**: Holds metadata catalogs connecting agent workflows into Salesforce platforms.
* **`notebooks/`**: Interactive exploratory notebooks for agent prompt optimization and OCR/extraction experiments.
* **`verify.md`**: Outlines expected test payloads, edge-case evaluations, and manual QA validation steps.

---

## Safety & Medical Disclaimer

> **Disclaimer**: PrescriptionAgent is designed for informational and assistive workflow support only. It does not replace professional clinical judgment, diagnosis, or prescription validation by a licensed pharmacist or physician.
