# REFERENCES

## A. 仓库内主证据

- [REPO-01] `README.md` — 当前版本、定位、问卷摘要、内部评估数字。
- [REPO-02] `CHANGELOG.md` — v0.3/v0.4/v0.5 增量记录。
- [REPO-03] `app/main.py` — 主要页面/API、Service Worker header、results 页面。
- [REPO-04] `app/init_db.py` — SQLite schema。
- [REPO-05] `app/services/llm_service.py` — DeepSeek 默认 provider、guard、template fallback。
- [REPO-06] `app/services/chat_service.py` — 对话编排与提醒/记忆上下文。
- [REPO-07] `app/services/patient_service.py` — 多患者服务。
- [REPO-08] `app/services/reminder_service.py` — medication schedule 与 daily medication record。
- [REPO-09] `app/services/caregiver_event_service.py` — caregiver events、风险等级与建议动作。
- [REPO-10] `app/services/familiar_material_service.py` — familiar materials 结构与使用。
- [REPO-11] `app/services/memory_candidate_service.py` — 候选捕捉、审批与写入素材。
- [REPO-12] `app/services/notify_service.py` — WeCom/DingTalk webhook。
- [REPO-13] `app/services/tts_service.py` — MiniMax TTS 与浏览器 fallback。
- [REPO-14] `templates/*.html` — patients/index/conversation/materials/photo_timeline/reminiscence/chat_history/consent/location_safety 等页面证据。
- [REPO-15] `static/manifest.json`, `static/sw.js` — PWA scaffolding。
- [REPO-16] `results/controlled_llm_comparison_report.json` — 5.60 → 8.13（+2.53）。
- [REPO-17] `results/deepseek_demo_patient_report.json` — DeepSeek demo patient internal report。
- [REPO-18] `results/real_api_patient_dialogue_report.json` — 实际 provider 为 mock，仅可视为 mock end-to-end evidence。
- [REPO-19] `results/usability_test_plan.md`, `docs/USABILITY_TEST_PLAN_V0_5.md` — 可用性测试计划，非已完成结果。
- [REPO-20] `docs/FUTURE_DIRECTION_CARE_AND_MEMORY.md` — Care Loop + Emotional Memory Companion 主线叙事。
- [REPO-21] `docs/PROJECT_STATUS_AND_NEXT_STEPS.md` — 项目状态与下一步。
- [REPO-22] `docs/screenshots/README.md` — 建议截图名称；当前仓库未提交真实截图。

## B. 外部公开来源（只用于背景论证）

- [EXT-01] World Health Organization. *Dementia*. <https://www.who.int/news-room/fact-sheets/detail/dementia>
- [EXT-02] Alzheimer’s Association. *Alzheimer’s Disease Facts and Figures*. <https://www.alz.org/alzheimers-dementia/facts-figures>
- [EXT-03] Alzheimer’s Association. *Wandering*. <https://www.alz.org/help-support/caregiving/safety/wandering>
- [EXT-04] Alzheimer’s Association. *Reminiscence and reminiscence therapy*. <https://www.alz.org/help-support/caregiving/daily-care/reminiscence-and-reminiscence-therapy>

### 这些来源可安全支撑的背景论点
- 痴呆是重要公共卫生问题，会给患者、照护者和照护系统带来持续负担。
- 家庭照护中的走失/外出风险、困惑、重复确认等问题具有现实性。
- 熟悉人物、照片、故事与回忆活动可作为温和陪伴和情感支持的背景依据。

### 不应用这些来源证明的内容
- 本项目已经具备临床疗效。
- 本项目已经真实降低 caregiver burden。
- 情感陪伴等同于治疗。

## C. 仓库内证据边界说明

1. README 提到 **33 份有效问卷** 与若干比例，但当前仓库快照中**未找到原始数据或独立分析文件**；因此仅能表述为早期探索性需求验证摘要。
2. 可用性测试目前只有计划，没有已完成的参与者结果。
3. 当前仓库快照**不可审计有效 git history**，版本判断以代码与已提交文档为准。
4. 当前仓库未提交真实产品截图，因此报告统一使用显式占位符。
