# v0.5 System Overview

## Version Positioning

v0.5 is a stable GitHub/demo version of the Alzheimer Family Care Assistant. The project is a controlled LLM prototype for family care, not a general chatbot and not a medical diagnosis system.

Primary model:

- Provider: DeepSeek
- Model: `deepseek-v4-flash`
- Mock: fallback/debug only
- Template fallback: safety repair path for high-risk or unstable outputs

## Core Capabilities

### Patient-side Stable Companionship

- `/conversation` provides the patient-facing conversation page.
- DeepSeek is used as the primary LLM provider.
- Replies are short, gentle, low-stimulation, and context-aware.
- High-risk scenarios are guarded: medication uncertainty, wandering/location confusion, anxiety, deceased relatives, and repeated questions.
- Browser TTS fallback works through `speechSynthesis`.
- MiniMax TTS configuration and wrapper are ready for end-to-end validation.

### Caregiver-side Daily Care Loop

- `/analysis` provides the caregiver dashboard.
- Reminder status supports pending, confirmed, missed, and skipped states.
- Medication-related replies use structured reminder records instead of LLM guesses.
- Caregiver events capture risk signals from patient conversations.
- Daily care summary combines reminders, events, and suggested actions.

### Personal Memory and Reminiscence

- `/materials` manages familiar materials such as family photos, voice messages, music, places, and old events.
- `/chat-history` shows dialogue history and pending memory candidates.
- `/reminiscence` uses approved materials for gentle memory support.
- Memory candidates must be reviewed by caregivers before becoming durable familiar materials.

## Main Pages

- `/app_home`: app entry and system-line overview
- `/demo-flow`: stable walkthrough for presentations
- `/conversation`: patient-side chat
- `/conversation?debug=1`: chat with provider/fallback diagnostics
- `/analysis`: caregiver daily care dashboard
- `/materials`: familiar materials library
- `/chat-history`: chat history and memory candidate review
- `/reminiscence`: memory and reminiscence support
- `/test-results`: evaluation and acceptance evidence
- `/debug-dashboard`: provider and diagnostic visibility

## Evaluation Snapshot

Current controlled comparison:

- direct baseline LLM score: `5.60`
- care system score: `8.13`
- improvement: `+2.53`
- verdict: `PASS`

The evaluation compares direct DeepSeek responses with the full care system pipeline. The care system performs better because it combines personal context, reminder status, response guards, template fallback, caregiver events, and memory candidate capture.

## Safety Boundary

- This system is not a medical device.
- It does not diagnose or treat Alzheimer’s disease.
- Medication facts are not inferred by the LLM.
- Sensitive memories require caregiver review.
- Real patient data should not be used without explicit consent.

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
