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

---

## Future Direction: Care Loop + Emotional Memory Companion

本项目未来将围绕"日常照护闭环"和"情感记忆陪伴"双主线发展：
前者面向家属减负和风险管理，后者面向患者的熟悉感、安全感与情绪支持。

### Core Direction A: Care Loop（照护闭环）

系统从"能聊天"发展为"辅助家属完成日常照护流程"。
重点不是让 LLM 自由判断，而是用结构化提醒、家属确认、
风险事件和每日照护记录形成闭环。

关键能力：
- daily care loop（每日照护台账）
- reminder confirmation（提醒确认）
- caregiver dashboard（家属看板）
- risk events（风险事件识别）
- medication safety（用药安全，不让 LLM 猜测用药事实）
- care log（照护日志）
- family burden reduction（减轻家属压力）

### Core Direction B: Emotional Memory Companion（情感记忆陪伴）

系统从"回答问题"发展为"用熟悉素材建立情感陪伴"。
通过照片、老歌、语音留言、旧地点、旧事件和家属审核后的记忆素材，
帮助患者获得熟悉感和安全感。

关键能力：
- familiar materials（熟悉素材）
- reminiscence support（回忆陪伴）
- family photo timeline（家庭记忆相册）
- voice notes（家属语音留言）
- old songs / personal stories（旧歌/个人故事）
- emotional grounding（情绪锚定）
- non-testing conversation（非测试式对话，不考问患者）

### Why Both Are Necessary（为何两者缺一不可）

只做照护管理会显得冷冰冰，只做情感陪伴又不能真正减轻家属压力。
这个项目的优势在于把两者连接起来：

患者端对话
-> 情绪/记忆/风险识别
-> 家属端照护摘要
-> 家属审核记忆素材
-> 回到患者端形成更个性化陪伴
