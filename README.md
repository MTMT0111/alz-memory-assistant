# Alzheimer Family Care Assistant

中文名：阿尔兹海默症家庭陪伴与照护辅助系统

## 1. Project Overview

This project is a controlled LLM system prototype for Alzheimer family care. It is not a generic chatbot and not a medical diagnosis system. The goal is to combine gentle patient-side companionship with caregiver-visible daily care signals, personal memory support, and safety-aware response control.

Core positioning:

- patient-side gentle companionship
- caregiver-side daily care loop
- personal memory and reminiscence support
- safety-aware LLM response control
- evaluation against direct LLM baseline

Current version: `v0.5`. DeepSeek V4 / `deepseek-v4-flash` is the primary chat model. Mock and template paths are fallback/debug mechanisms, not the main chat experience.

## 2. Why This Project

Family care for people with Alzheimer’s disease can be stressful, repetitive, and emotionally demanding. Common daily scenes include repeated questions, medication uncertainty, location confusion, anxiety, night-time insecurity, and wandering risk. These scenes need low-stimulation support and clear caregiver handoff.

Direct LLM responses are often not stable enough for this setting. This project controls LLM output through profile context, reminder status, familiar materials, rules, template fallback, and caregiver events.

Internal survey findings used in this prototype:

- 33 valid responses
- 87.88% considered such a device necessary
- 84.84% accepted caregiver-entered profile/materials
- 81.82% preferred voice interaction
- reminders, safety, and caregiver burden reduction were high-priority needs

## 3. Core System Lines

### Patient-side Stable Companionship

- DeepSeek as primary LLM
- gentle low-stimulation replies
- high-risk scenario guard
- template fallback
- browser TTS fallback / MiniMax TTS-ready structure

### Caregiver-side Daily Care Loop

- reminder status
- medication confirmation
- daily care summary
- caregiver events
- suggested actions
- medication facts are not guessed by LLM

### Personal Memory and Reminiscence

- familiar materials
- chat history
- memory candidates
- caregiver approval
- reminiscence page
- materials can be used as conversation context

## 4. Key Features

- Real DeepSeek provider integration
- mock/template fallback
- demo patient profile
- daily care loop
- reminder confirmation/miss/skip
- caregiver risk dashboard
- familiar materials library
- memory candidate review
- reminiscence support
- controlled LLM evaluation
- test results dashboard
- demo flow page

## 5. Tech Stack

- Python
- FastAPI
- SQLite
- HTML/CSS/JavaScript
- DeepSeek API compatible OpenAI-style client
- Browser `speechSynthesis` fallback
- Optional MiniMax TTS configuration

## 6. Project Structure

```text
app/
  main.py
  services/
  models/
templates/
static/
scripts/
docs/
results/
```

- `app/`: FastAPI application, routes, service layer, models, database initialization, and demo data.
- `app/main.py`: Web entry point and API surface.
- `app/services/`: LLM routing, chat pipeline, care loop, memory/material services, diagnostics, and TTS wrapper.
- `app/models/`: Lightweight data models used by services and APIs.
- `templates/`: HTML pages for patient, caregiver, demo, debug, and evaluation views.
- `static/`: CSS and browser JavaScript for the app shell, chat, care dashboard, materials, and voice fallback.
- `scripts/`: Test, evaluation, seeding, and acceptance-check scripts.
- `docs/`: Version notes, demo scripts, usability plan, release checklist, and development guide.
- `results/`: Formal demo/evaluation reports. Current committed reports use the demo patient only.

## 7. Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

Edit `.env`:

```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-flash
```

Start locally:

```bash
venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Visit:

```text
http://127.0.0.1:8001/app_home
```

## 8. Demo Flow

Recommended routes:

- `/demo-flow`
- `/conversation`
- `/analysis`
- `/materials`
- `/chat-history`
- `/reminiscence`
- `/test-results`

Recommended presentation order:

1. Open `/app_home` to introduce the three system lines.
2. Open `/demo-flow` to follow the stable v0.5 walkthrough.
3. Use `/conversation?debug=1` to show patient-side DeepSeek chat, fallback diagnostics, reminder status, and familiar-material usage.
4. Open `/analysis` to show caregiver daily care summary, medication status, risk events, and suggested actions.
5. Open `/materials` and `/chat-history` to show familiar materials and memory candidate review.
6. Open `/reminiscence` to show personal memory support.
7. Open `/test-results` to show controlled evaluation evidence.

## Screenshots

Screenshots can be added under `docs/screenshots/`.

## 9. Evaluation

Current controlled comparison report:

- direct baseline LLM score: `5.60`
- care system score: `8.13`
- improvement: `+2.53`
- verdict: `PASS`

The evaluation compares direct DeepSeek responses with the full care system pipeline. The care system combines reminder state, profile/material context, response guards, template fallback, caregiver events, and memory candidate capture.

Source report:

- `results/controlled_llm_comparison_report.json`
- `results/controlled_llm_comparison_report.md`

## 10. Safety and Limitations

- This is not a medical device.
- It does not diagnose or treat Alzheimer’s disease.
- Medication status must come from structured reminder records, not LLM guesses.
- Sensitive memories require caregiver review.
- Real patient data should not be used without consent.
- API keys must stay in local `.env` files and must not be committed.
- Local SQLite databases are for demo/development use only and should not contain real patient privacy data.

## 11. Roadmap

v0.6:

- real small-sample usability test
- MiniMax TTS end-to-end validation
- privacy and consent page
- cross-day care log
- memory candidate deduplication and conflict handling

## 12. License / Academic Use

This project is currently for academic and portfolio demonstration purposes.
