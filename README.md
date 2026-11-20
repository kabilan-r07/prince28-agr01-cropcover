# CropCover – Crop Insurance Assistant


[![CI](https://github.com/kabilan-r07/prince28-agr01-cropcover/actions/workflows/ci.yml/badge.svg)](https://github.com/kabilan-r07/prince28-agr01-cropcover/actions/workflows/ci.yml)
[![Live](https://img.shields.io/website?url=https%3A%2F%2Fcropcover.onrender.com%2Fhealth&label=live)](https://cropcover.onrender.com/docs)
[![Uptime (30 days)](https://img.shields.io/uptimerobot/ratio/m804746065-8f84f5e0c7acddb913fee4b2)](https://cropcover.onrender.com/health)

**Live:** [https://cropcover.onrender.com](https://cropcover.onrender.com) · [API docs](https://cropcover.onrender.com/docs) · [health](https://cropcover.onrender.com/health)

CropCover is an AI-powered crop insurance guidance application designed to help Tamil Nadu farmers understand the **Pradhan Mantri Fasal Bima Yojana (PMFBY)** scheme.

It provides information about crop insurance coverage, claim procedures, claim deadlines, premium amounts, and sum insured based on official government documents.

**Status:** Week 1 complete · live at https://cropcover.onrender.com

## Who Is It For?

CropCover is designed for farmers in Tamil Nadu, especially paddy farmers who face crop damage due to heavy rainfall, floods, droughts, or other natural calamities.

For example, a paddy farmer in Nagapattinam whose samba crop is damaged by heavy November rainfall may not know whether the damage is covered by insurance or how to submit a claim.

CropCover helps farmers understand the applicable insurance rules and the next steps.

## The Problem

Many farmers in Tamil Nadu are unaware of the crop insurance benefits available under PMFBY. They often find it difficult to understand insurance guidelines, claim procedures, premium amounts, and eligibility conditions because the information is spread across different government documents. Farmers may also miss important claim deadlines because they do not know when and how to report crop damage. This project aims to provide simple, understandable, and reliable crop insurance guidance using official government information.

## Main Features

- **Crop Insurance Information:** Explains PMFBY coverage and eligibility.
- **Claim Guidance:** Provides steps to report crop damage and submit claims.
- **Claim Deadline Information:** Explains applicable reporting deadlines, including the 72-hour intimation requirement where applicable.
- **Premium Calculator:** Displays premium information based on crop, district, and season.
- **Sum Insured Details:** Provides insurance coverage amounts from official notifications.
- **Source Citations:** Links answers to relevant government guidelines and notifications.
- **Tamil Nadu Focus:** Provides information relevant to Tamil Nadu farmers.

## Data Sources

The application uses official government documents and notifications.

1. PMFBY Official Portal – https://pmfby.gov.in/
2. Ministry of Agriculture and Farmers Welfare – https://agriwelfare.gov.in/
3. Tamil Nadu Agriculture Department notifications.
4. PMFBY Operational Guidelines.
5. Weather-Based Crop Insurance Scheme (RWBCIS) guidelines.

All important insurance figures and claim rules should be verified against the applicable official documents.

## Technology Stack

- **Backend:** Python, FastAPI
- **Data Processing:** Python
- **Testing:** Pytest
- **Code Quality:** Ruff
- **Documentation:** Markdown
- **Version Control:** Git and GitHub

## Hardest Technical Challenge

One of the major challenges is understanding the difference between area-based yield loss claims and individual claims for localised calamities.

Another challenge is extracting accurate premium and sum insured values from government notification tables, which vary according to crop, district, and season.

The system must retrieve the correct information and provide references to the original government guidelines instead of generating unsupported answers.

## Signature Feature

### Smart Crop Damage Claim Guidance

Farmers can select the type of crop damage they experienced.

The application will help identify the potentially applicable claim category, explain the reporting deadline, provide the next steps, and show the relevant official guideline references.

## Project Goals and Target Metrics

| Metric | Target |
|---|---:|
| Premium accuracy | 100% |
| Sum insured accuracy | 100% |
| Claim classification accuracy | 90% or higher |
| Test scenarios | 30 |
| Crop-district cases | 30 |

These targets will be evaluated during testing.

## Project Structure

```text
CropCover/
│
├── cropcover/
│   └── api/
│       └── main.py
│
├── docs/
│   ├── QUESTIONS.md
│   └── REQUIREMENTS.md
│
├── tests/
│
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd CropCover
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment Variables

Windows Command Prompt:

```cmd
copy .env.example .env
```

### 4. Run the Application

```bash
uv run uvicorn cropcover.api.main:create_app --factory --reload
```

### 5. Open API Documentation

Visit:

http://localhost:8000/docs

## Run Tests

```bash
uv run pytest
```

## Check Code Quality

```bash
uv run ruff check .
```

## Future Enhancements

- Tamil language support.
- AI-powered question-answering system.
- Retrieval-Augmented Generation (RAG).
- Voice-based farmer assistance.
- Integration with official crop insurance information.
- Mobile-friendly user interface.

## Project Objective

The main objective of CropCover is to make crop insurance information easier to understand and access for Tamil Nadu farmers through reliable, accurate, and transparent digital assistance.

## Run locally in one command

You need Docker Desktop running. From a fresh clone:

```bash
docker compose up --build
```

This starts Postgres (with pgvector), Redis, runs the migrations and loads the sample data once, then starts the API.

- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Liveness: [http://localhost:8000/health](http://localhost:8000/health)
- Readiness (checks the database): [http://localhost:8000/ready](http://localhost:8000/ready)

Stop with `Ctrl+C`, then `docker compose down`. Add `-v` to also delete the database volume.

## Develop and test

| Task | Mac / Linux | Windows |
|---|---|---|
| Run the API with reload | `make dev` | `uv run poe dev` |
| Unit tests (no network) | `make test` | `uv run poe test` |
| Integration tests (needs `docker compose up`) | `make test-integration` | `uv run poe test-integration` |
| Coverage report | `make cov` | `uv run poe cov` |
| Lint and format check | `make lint` | `uv run poe lint` |
