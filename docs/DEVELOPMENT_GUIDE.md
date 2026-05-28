# Development Guide

## 1. Start the Project

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Open:

```text
http://127.0.0.1:8001/app_home
```

## 2. Switch Provider

Edit local `.env`.

DeepSeek main path:

```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-flash
```

Fallback/debug mode:

```bash
LLM_PROVIDER=mock
```

Keep `.env` local. Never commit real API keys.

## 3. Run Tests

Compile first:

```bash
venv/bin/python -m compileall app scripts
```

If the service is running:

```bash
CHAT_URL=http://127.0.0.1:8001/chat venv/bin/python scripts/test_page_chat_deepseek.py
venv/bin/python scripts/test_materials_module.py
venv/bin/python scripts/test_memory_candidate_flow.py
BASE_URL=http://127.0.0.1:8001 venv/bin/python scripts/test_demo_flow_page.py
BASE_URL=http://127.0.0.1:8001 venv/bin/python scripts/test_reminiscence_page.py
venv/bin/python scripts/run_v05_acceptance_check.py
```

If the acceptance check requires the service, start uvicorn first.

## 4. Add a Page

1. Add a template under `templates/`.
2. Add or reuse a route in `app/main.py`.
3. Add navigation metadata only if the page should appear in the app shell.
4. Add JavaScript behavior in `static/script.js` only when needed.
5. Keep the page role clear: patient, caregiver, demo, or debug.

## 5. Add a Care Scenario

1. Define the trigger condition in the relevant service.
2. Decide whether it is patient-only, caregiver-visible, or both.
3. Use structured records for factual care status.
4. Add a gentle patient-side reply path.
5. Add caregiver event creation when follow-up is needed.
6. Add or update a focused test script.

## 6. Avoid Breaking the DeepSeek Main Chain

- Keep `LLM_PROVIDER=deepseek` as the primary demo configuration.
- Do not make mock the default production path.
- Do not remove template fallback or safety guards.
- Do not let medication status be guessed by free-form LLM output.
- Check provider diagnostics in `/conversation?debug=1` and `/debug-dashboard`.
- Run `scripts/test_page_chat_deepseek.py` when changing LLM routing.

## 7. Git Branches

- `main`: stable showcase version
- `dev`: daily development
- `feature/xxx`: single feature
- `fix/xxx`: bug fix

Before committing:

```bash
venv/bin/python -m compileall app scripts
venv/bin/python scripts/run_v05_acceptance_check.py
```
