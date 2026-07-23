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

---

## Roadmap（重新规划版）

### P0：真实试用前稳定性修复
目的：确保系统不会把 demo 数据污染真实患者，
不会重复推送提醒，不会因缓存/登录问题影响真实试用。

具体任务：
- patient_id 上下文隔离验证
- demo 数据不污染真实患者（李桂兰/小雨/老王只在 demo 出现）
- medication overdue 防重复推送
- Service Worker 缓存版本控制
- 登录失败提示完善

### P1：真实家庭测试准备
目的：生成测试家庭初始化脚本、用户指南、部署清单、启动脚本，
支持 1-2 个真实或模拟照护家庭试用。

具体任务：
- scripts/setup_test_family.py
- docs/user_guide.md
- docs/deploy_checklist.md
- docs/start.sh
- results/usability_test_plan.md（已有，确认可用）

### P2：情感记忆陪伴增强
目的：以家庭记忆相册、照片故事、语音说明和回忆对话为核心，
提高患者端情感价值。

具体任务：
- 家庭记忆相册（photo timeline，按年代浏览）
- 照片故事（story_text，照护者录入）
- 家属语音留言录制（voice note）
- 从照片直接开启对话
- 旧歌/旧地点素材支持（扩展）
- 敏感记忆安全边界标记

---

### v0.6 — Real Testing and Care Reliability
目标：先让真实家庭或模拟家庭能够试用，验证照护闭环基本可用。

重点：
1. 遗留 bug 修复（P0 任务）
2. 真实测试准备（P1 任务）
3. 每日照护台账完善（跨天记录、今日/昨日对比、风险事件处理状态）

### v0.7 — Emotional Memory Companion
目标：强化患者端情感陪伴，不只是管理后台。

重点：
1. 家庭记忆相册（photo timeline + 年代浏览 + 照片故事 + 语音说明）
2. 回忆陪伴增强（旧地点/家属语音留言/敏感记忆安全边界）
3. 家属审核式记忆沉淀增强（去重/冲突合并/审核备注/敏感程度标记）

### v0.8 — Voice and Deployment
目标：让系统更像真实陪伴设备，可以稳定部署给真实家庭。

重点：
1. MiniMax TTS 真实端到端验证
2. 浏览器 TTS fallback 稳定性
3. 手机端 PWA 优化
4. 局域网部署文档
5. 隐私授权页完善
6. 真实照护家庭试用反馈整理
