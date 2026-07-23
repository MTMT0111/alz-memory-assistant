const fs=require('fs');const p=require('path');const b='/root/alz-memory-assistant/docs/adventurex';const a=p.join(b,'assets');fs.mkdirSync(a,{recursive:true});const w=(f,c)=>{const x=p.join(b,f);fs.mkdirSync(p.dirname(x),{recursive:true});fs.writeFileSync(x,c,'utf8')};
const css=`:root{--ink:#1f2937;--muted:#4b5563;--line:#d7dde5;--soft:#f5f7fa;--soft2:#eef3f7;--brand:#23445d;--accent:#3f8f88;--warn:#b86a3b;--bg:#fff}*{box-sizing:border-box}html,body{margin:0;padding:0;background:var(--bg);color:var(--ink);font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6}body{padding:0}.container{width:210mm;margin:0 auto;padding:14mm 14mm 18mm}.cover{min-height:260mm;display:flex;flex-direction:column;justify-content:space-between;padding:10mm 0 6mm}.cover-kicker,.kicker{color:var(--accent);font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.cover h1{margin:8px 0 4px;font-size:28px;line-height:1.2;color:var(--brand)}.cover h2{margin:0;font-size:18px;font-weight:700}.cover h3{margin:8px 0 18px;font-size:16px;font-weight:600;color:var(--muted)}.tagline{font-size:15px;max-width:160mm}.meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px 18px;margin-top:20px}.meta-card,.panel,.stat,.quote,.placeholder,.note{background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:10px 12px}.headerline{display:flex;justify-content:space-between;align-items:baseline;border-bottom:2px solid var(--brand);padding-bottom:6px;margin-bottom:14px}.headerline .small{color:var(--muted);font-size:12px}.section{page-break-inside:avoid;margin:0 0 16px}.section h2{font-size:22px;color:var(--brand);margin:18px 0 10px}.section h3{font-size:16px;color:var(--brand);margin:14px 0 8px}.section h4{font-size:14px;color:var(--ink);margin:12px 0 6px}p,li{font-size:12px}ul,ol{margin:8px 0 8px 20px}.twocol{display:grid;grid-template-columns:1fr 1fr;gap:12px}.threecol{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}table{width:100%;border-collapse:collapse;margin:10px 0 14px;font-size:11px;page-break-inside:avoid}th,td{border:1px solid var(--line);padding:7px 8px;vertical-align:top}th{background:var(--soft2);text-align:left;color:var(--brand)}code{font-family:Consolas,monospace;font-size:10.5px;background:#f3f4f6;padding:1px 4px;border-radius:4px}blockquote{margin:10px 0;padding:10px 12px;border-left:4px solid var(--accent);background:var(--soft)}.placeholder{color:var(--muted);font-style:italic}.quote strong,.stat strong{color:var(--brand)}.stat-row{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.stat .value{font-size:22px;line-height:1.1;color:var(--brand);font-weight:800;margin:4px 0}.figure{margin:12px 0 16px;page-break-inside:avoid}.figure img,.figure svg{width:100%;display:block;border:1px solid var(--line);border-radius:10px;background:#fff}.figcaption{font-size:11px;color:var(--muted);margin-top:6px}.small{font-size:11px;color:var(--muted)}.footer{margin-top:20px;padding-top:8px;border-top:1px solid var(--line);color:var(--muted);font-size:11px}.page-break{page-break-before:always}.badge{display:inline-block;padding:3px 8px;border-radius:999px;font-size:10px;font-weight:700}.ok{background:#eaf5ef;color:#1f6b47}.partial{background:#fff3e8;color:#9a531f}.plan{background:#eef6ff;color:#235b8a}.long{background:#f3f4f6;color:#4b5563}@page{size:A4;margin:14mm 12mm 16mm}@media print{.container{width:auto;margin:0;padding:0}a{color:inherit;text-decoration:none}}`;
w('assets/proposal.css',css);
const audit=`# PROJECT FACT AUDIT

> 审计范围：当前仓库快照（代码、模板、静态资源、results、docs、scripts）。
> 事实优先级：代码与数据库结构 > 测试脚本与 results/*.json > README/docs > 旧版本文档。

## 当前版本结论
- **当前最可信版本：v0.5**
- 证据：\`README.md\`、\`CHANGELOG.md\`、\`docs/V0_5_SYSTEM_OVERVIEW.md\`、\`app/main.py\`
- Git 历史：**Needs manual confirmation**（当前仓库快照不可审计有效 git log/tag）

## A. 已实现功能
| 模块 | 证据文件 | 页面/API | 测试证据 | 当前状态 |
|---|---|---|---|---|
| FastAPI + SQLite 原型 | \`app/main.py\`, \`app/init_db.py\` | 全站 | \`scripts/run_v05_acceptance_check.py\` | 已实现 |
| Caregiver PIN 登录 | \`templates/login.html\`, \`app/main.py\` | \`/login\`, \`/api/login\` | 代码证据 | 已实现 |
| 多患者管理 | \`templates/patients.html\`, \`patient_service.py\` | \`/patients\`, \`/api/patients/*\` | 代码证据 | 已实现 |
| 患者设置 / 用药 / 团队 | \`templates/patient_detail.html\`, \`reminder_service.py\` | \`/patient/{patient_id}/settings\` | 代码证据 | 已实现 |
| DeepSeek 主链路 | \`llm_service.py\` | \`/chat\` | \`results/controlled_llm_comparison_report.json\`, \`results/deepseek_demo_patient_report.json\` | 已实现 |
| 规则安全层 + template fallback | \`llm_service.py\`, \`conversation_style_engine.py\` | \`/chat\` | \`results/controlled_llm_comparison_report.json\` | 已实现 |
| 患者端对话 | \`conversation.html\`, \`static/script.js\`, \`static/voice.js\` | \`/conversation/{patient_id}\` | \`scripts/test_page_chat_deepseek.py\` | 已实现 |
| reminder / medication schedule | \`reminder_service.py\`, \`templates/index.html\` | \`/api/reminders/{patient_id}\` | \`scripts/test_reminder_status.py\` | 已实现 |
| daily care / trend | \`daily_summary_service.py\`, \`care_trend.html\` | \`/api/daily-care/{patient_id}/today\`, \`/care-trend/{patient_id}\` | \`scripts/test_daily_care_loop.py\` | 已实现 |
| caregiver events / risk events | \`caregiver_event_service.py\`, \`risk_service.py\` | \`/api/caregiver/{patient_id}/events\` | \`results/deepseek_demo_patient_report.json\` | 已实现 |
| familiar materials | \`materials.html\`, \`familiar_material_service.py\` | \`/materials/{patient_id}\` | \`scripts/test_materials_module.py\` | 已实现 |
| photo timeline | \`photo_timeline.html\` | \`/photo-timeline/{patient_id}\` | 代码证据 | 已实现 |
| memory candidate capture/approve | \`memory_candidate_service.py\` | \`/api/memory-candidates/*\` | \`scripts/test_memory_candidate_flow.py\` | 已实现 |
| reminiscence | \`reminiscence.html\`, \`memory_vector_service.py\` | \`/reminiscence/{patient_id}\` | \`scripts/test_reminiscence_page.py\` | 已实现（基础） |
| consent gate | \`consent.html\`, \`consent_service.py\` | \`/consent/{patient_id}\` | 代码证据 | 已实现 |
| MiniMax TTS + browser fallback | \`tts_service.py\`, \`voice.js\` | \`/api/tts\` | \`scripts/test_tts_service.py\` | 已实现（环境依赖） |
| webhook 通知 | \`notify_service.py\` | \`/api/settings/test-notify\` | 代码证据 | 已实现 |
| PWA scaffolding / SW | \`manifest.json\`, \`sw.js\`, \`base.html\` | 全站 | 代码证据 | 已实现 |

## B. 部分实现功能
| 功能 | 已完成部分 | 尚未完成部分 | 风险 |
|---|---|---|---|
| patient_id 上下文隔离 | 非 demo prompt 防污染规则；多患者 patient_id 已进入部分链路 | 鉴权与 access check 不一致；legacy profile 与 UUID patient 双模型并存 | 不可夸大为完整隔离 |
| Demo 数据不污染真实患者 | 有专门 prompt 规则与 \`scripts/test_patient_context.py\` | 脚本只构造 prompt，不发真实请求 | 只能写成“已有防污染设计” |
| memory review → 长期检索 | 候选生成、审批、写入 materials 已存在 | 进入当前真实聊天检索链路 **Needs manual confirmation** | 不可写成完整长期记忆系统 |
| real-patient chat 全量复用 care pipeline | UUID patient 能进入聊天与部分背景任务 | 未完全复用 legacy demo 富上下文链路 | demo 路径与 real-patient 路径有差异 |
| MiniMax TTS | 集成和 fallback 存在 | 当前环境真实成功率 **Needs manual confirmation** | 不可写成稳定量产语音能力 |
| notification | webhook 与 overdue checker 已实现 | 无原生 push subscription | 不可写成原生移动推送 |
| PWA | manifest + SW + install 基础具备 | 无完整离线 / push / API cache | 只能写成基础安装壳 |
| location safety | 页面、后端结构、事件记录存在 | 页面明确为占位，未接地图/设备 | 不得写成已完成防走失产品 |
| privacy / consent | 同意页面、签署记录存在 | 文案与真实外部 API 边界仍需完善 | 不能写成成熟合规方案 |
| chat history 中记忆审核 UI | 会话质量查看完整 | 当前模板未完整挂载 candidate review 面板 | 报告应写“部分实现” |

## C. 五天内可实现功能
| 功能 | 依赖 | 预计工作量 | 验收方式 |
|---|---|---|---|
| Hero Demo 串联：照片→回忆对话→照护反馈 | 已有 patients / materials / conversation / care-portal / memory-candidates | 中 | 完整走通演示脚本 |
| 家庭记忆相册叙事强化 | 已有 photo timeline + story text + voice note fields | 中 | 新增 1 条带年份/故事/语音的素材后可进入对话 |
| Voice note 情感陪伴演示 | 已有 voice note upload + browser TTS fallback | 中 | 家属录制/上传一段安抚语音，患者端可播放 |
| Daily care ledger 展示优化 | 已有 daily summary/trend/event/risk data | 中 | 至少展示两天结构化记录 |
| Memory candidate 审核演示稳定化 | 已有 candidate capture/approve APIs | 中 | 新线索进入候选并被家属审批 |
| Context isolation regression check | 已有 test script 和 patient paths | 低到中 | 人工复核 prompt/response 不出现 demo 关系词 |

## D. 长期设想
| 方向 | 价值 | 为什么不放进五天范围 |
|---|---|---|
| 完整 family-grounded long-term memory system | 提升长期熟悉感与个性化陪伴 | 需要更稳的检索、审核、冲突处理 |
| 更强 caregiver-in-the-loop 安全治理 | 提升高风险场景可控性 | 需要更多真实家庭试用 |
| 多家庭部署 / 完整权限系统 | 支撑真实使用 | 涉及 auth、数据隔离、运维 |
| 真正移动端 / 设备端长期陪伴 | 更贴近日常使用 | 超出五天范围 |
| 定位与防走失能力 | 对高风险家庭价值明显 | 需要硬件、地图、围栏、权限 |
| 真实小样本可用性研究 | 提升研究可信度 | 需要招募、伦理、流程与时间 |

## 最新评估结论
- baseline：**5.60**
- care system：**8.13**
- improvement：**+2.53**
- verdict：**PASS**

## Needs manual confirmation
- 当前环境中 DeepSeek API 是否仍可成功调用
- 当前环境中 MiniMax TTS 是否稳定成功
- memory candidate 审批后是否稳定进入当前真实聊天检索链路
- 是否存在仓库外未提交的 33 份问卷原始分析文件
- 是否存在仓库外未提交的真实截图
- 当前仓库快照是否对应正式 release/tag
`;
const refs=`# REFERENCES

## A. 仓库内主证据
- [REPO-01] \`README.md\` — 当前版本、定位、问卷摘要、内部评估数字。
- [REPO-02] \`CHANGELOG.md\` — v0.3/v0.4/v0.5 增量记录。
- [REPO-03] \`app/main.py\` — 主要页面/API、Service Worker header、results 页面。
- [REPO-04] \`app/init_db.py\` — SQLite schema。
- [REPO-05] \`app/services/llm_service.py\` — DeepSeek 默认 provider、guard、template fallback。
- [REPO-06] \`app/services/chat_service.py\` — 对话编排与提醒/记忆上下文。
- [REPO-07] \`app/services/patient_service.py\` — 多患者服务。
- [REPO-08] \`app/services/reminder_service.py\` — medication schedule 与 daily medication record。
- [REPO-09] \`app/services/caregiver_event_service.py\` — caregiver events、风险等级与建议动作。
- [REPO-10] \`app/services/familiar_material_service.py\` — familiar materials 结构与使用。
- [REPO-11] \`app/services/memory_candidate_service.py\` — 候选捕捉、审批与写入素材。
- [REPO-12] \`app/services/notify_service.py\` — WeCom/DingTalk webhook。
- [REPO-13] \`app/services/tts_service.py\` — MiniMax TTS 与浏览器 fallback。
- [REPO-14] \`templates/*.html\` — patients/index/conversation/materials/photo_timeline/reminiscence/chat_history/consent/location_safety 等页面证据。
- [REPO-15] \`static/manifest.json\`, \`static/sw.js\` — PWA scaffolding。
- [REPO-16] \`results/controlled_llm_comparison_report.json\` — 5.60 → 8.13（+2.53）。
- [REPO-17] \`results/deepseek_demo_patient_report.json\` — DeepSeek demo patient internal report。
- [REPO-18] \`results/real_api_patient_dialogue_report.json\` — 实际 provider 为 mock，仅可视为 mock end-to-end evidence。
- [REPO-19] \`results/usability_test_plan.md\`, \`docs/USABILITY_TEST_PLAN_V0_5.md\` — 可用性测试计划，非已完成结果。
- [REPO-20] \`docs/FUTURE_DIRECTION_CARE_AND_MEMORY.md\` — Care Loop + Emotional Memory Companion 主线叙事。
- [REPO-21] \`docs/PROJECT_STATUS_AND_NEXT_STEPS.md\` — 项目状态与下一步。
- [REPO-22] \`docs/screenshots/README.md\` — 建议截图名称；当前仓库未提交真实截图。

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
`;
const oneCN=`# AdventureX One-Page Summary (CN)

## Problem
阿尔兹海默症家庭照护的难点不只是聊天，而是重复提问、焦虑、位置困惑、用药不确定与家属长期压力同时存在。

## Insight
通用大模型能生成语言，但不能天然承担家庭照护责任。真正需要的是结构化照护状态、家属审核机制、个人情感记忆与安全控制的组合。

## Solution
本项目是 **Care Loop + Emotional Memory Companion** 原型：患者端通过照片、故事、语音留言与 familiar materials 获得温和陪伴；家属端通过 reminder、daily care、risk events 与 memory review 获得行动支持。

## Current Progress
当前仓库快照已实现：FastAPI + SQLite、多患者管理、DeepSeek 主链路、患者对话、家属看板、materials、photo timeline、reminiscence、memory candidate、consent、TTS fallback 与 PWA 基础壳。

## Differentiation
1. Structured Care Grounding
2. Safety-Controlled Dialogue
3. Caregiver-Governed Memory
4. Emotional Memory Grounding

## Current Evidence
内部 10 场景评估：baseline **5.60**；care system **8.13**；improvement **+2.53**；PASS。

> 注：这是内部场景评估，不是临床验证。

## Five-Day Goal
围绕 **From Family Memory to Safer Care** 打磨 Hero Demo：家属上传照片与语音 → 患者进入回忆对话 → 系统切换到结构化照护与安全控制 → 家属收到摘要、风险提示与待审核记忆线索。

## GitHub
**[GITHUB URL]**
`;
const oneEN=`# AdventureX One-Page Summary (EN)

## Problem
Family dementia care is more than conversation: patients need familiarity and reassurance, while caregivers need reminders, risk visibility, and continuity of care.

## Insight
A general-purpose LLM can generate language, but it does not inherently understand real care state, family memory context, or safety boundaries.

## Solution
This project proposes a **Care Loop + Emotional Memory Companion** that connects patient-side reminiscence support with caregiver-side care loops through structured care grounding, safety controls, and caregiver-governed memory.

## Current Progress
The audited snapshot already includes a working FastAPI + SQLite prototype with multi-patient management, DeepSeek chat, caregiver dashboard, familiar materials, photo timeline, memory candidate review, consent flow, TTS fallback, and PWA scaffolding.

## Differentiation
The innovation is not the model call itself, but the combination of structured care facts, safety-controlled dialogue, caregiver review, and emotional grounding through family materials.

## Evidence
Internal 10-scenario comparison: baseline **5.60**, care system **8.13**, improvement **+2.53**. This is an internal scenario-based evaluation, not a clinical validation.

## Five-Day Goal
Build a clear Hero Demo: **From Family Memory to Safer Care**.

## GitHub
**[GITHUB URL]**
`;
const pitch3=`# AdventureX 3-Minute Pitch (CN)

想象这样一个场景：一位阿尔兹海默症老人看到年轻时的家庭照片，突然想起过去，又马上问自己今天是不是还没吃药，接着说想出去找女儿。对家属来说，最难的从来不是“让 AI 陪她说几句话”，而是如何在安抚情绪、确认事实、避免风险和减轻日常负担之间不断切换。

这就是我做这个项目的原因。

我现在做的不是一个普通陪聊机器人，也不是医疗诊断系统，而是一个面向阿尔兹海默症家庭场景的受控式 AI 原型。我把它定义为 **Care Loop + Emotional Memory Companion**。患者端通过熟悉人物、家庭照片、语音留言和个人故事提供更低刺激的陪伴；家属端通过 reminder、daily care、risk events 和 memory review 形成照护闭环。

它和通用 LLM 最大的区别，是把模型放在被约束的位置。用药状态来自结构化 reminder，不由模型猜；高风险场景有 rule guard、postprocess 和 template fallback；长期记忆不能自动写入，必须经过 caregiver review；而照片、声音、老歌和旧地点也不是装饰，它们是患者端对话真正的情感上下文。

当前仓库里，我已经做出了一个可运行的 v0.5 原型：FastAPI + SQLite、多患者管理、DeepSeek 主链路、患者对话页、家属看板、materials、photo timeline、memory candidate、reminiscence、consent、TTS fallback，以及内部评估页面。最新 committed 结果显示，在 10 个内部场景中，普通直接模型回复平均分是 5.60，而完整照护系统链路是 8.13，提升了 2.53。这个结果不是临床验证，但它说明：把照护事实 grounding、安全控制和家庭记忆结合起来，确实比直接让 LLM 聊天更接近真实家庭需要。

我想在 AdventureX 的五天里完成的，不是继续堆功能，而是做一个非常清晰的 Hero Demo：**From Family Memory to Safer Care**。家属建立患者档案，上传老照片和语音说明；患者从照片进入回忆对话；当出现用药、外出或敏感亲人问题时，系统切换到结构化照护与安全控制；家属端收到摘要、风险提示和待审核记忆线索。

我申请 AdventureX，不是为了验证“AI 能不能做陪伴”，而是为了把一个已经运行的原型推进成一个让评审、用户和未来合作者都能快速看懂价值路径的 MVP。`;
const pitch60=`# AdventureX 60-Second Pitch (CN)

阿尔兹海默症家庭真正需要的，不是一个普通陪聊机器人，而是一个既能给患者熟悉感、又能给家属行动支持的辅助系统。我的项目叫 **Alzheimer Family Care Assistant**，核心方向是 **Care Loop + Emotional Memory Companion**：患者端通过照片、故事和语音留言进入温和对话，家属端通过 reminder、risk events、daily care 和 memory review 形成照护闭环。

它和普通 LLM 最大的不同，是用药事实来自结构化数据，高风险场景由规则与 template fallback 控制，长期记忆必须经过家属审核，而不是模型自动写入。当前仓库里我已经做出了一个可运行的 v0.5 原型，内部 10 场景评估从 5.60 提升到 8.13。

我希望在 AdventureX 的五天里，把它打磨成一个清晰的 Hero Demo：**从家庭记忆出发，进入更安全的家庭照护。**`;
const demo=`# FINAL DEMO SCRIPT

## 0:00–0:30 痛点
- 阿尔兹海默症家庭需要的不是普通陪聊，而是“患者熟悉感 + 家属行动支持”。

## 0:30–1:00 患者档案和家庭素材
- 打开 `/patients` 与 `/patient/{patient_id}/settings`
- 打开 `/materials/{patient_id}`，展示照片、故事、语音说明

## 1:00–2:00 照片进入患者对话
- 打开 `/photo-timeline/{patient_id}`
- 点击一张家庭照片进入 `/conversation/{patient_id}`
- 说明这是 emotional memory grounding

## 2:00–2:40 用药和外出风险
- 输入“我是不是还没吃药？”
- 输入“我想出去找她”或“这里是哪里？我要回家。”
- 说明系统不会让模型自由猜测或鼓励外出

## 2:40–3:20 家属端
- 切换到 `/care-portal/{patient_id}`
- 展示 medication 状态、risk events、今日概览

## 3:20–4:00 记忆审核
- 进入 `/chat-history/{patient_id}` 或说明 memory candidate 流程
- 强调长期记忆要经过 caregiver approval

## 4:00–4:30 评估
- 打开 `/test-results`
- 展示 5.60 → 8.13（+2.53）
- 明确说明：这是内部场景评估，不是临床验证

## 4:30–5:00 未来与结尾
- 总结：不是更会聊天的 AI，而是更懂家庭照护流程、更尊重熟悉感和安全边界的系统
- 结束句：**From Family Memory to Safer Care.**
`;
const qr=`# QUALITY REVIEW

## Review 1：事实审查
- 当前最可信版本为 **v0.5**。
- 多患者、DeepSeek 主链路、患者对话、caregiver workspace、materials、photo timeline、memory candidate、reminiscence、consent、TTS fallback、PWA scaffolding 均有代码证据。
- 最新内部评估数字来自 \`results/controlled_llm_comparison_report.json\`：**5.60 → 8.13（+2.53）**。
- `real_api_patient_dialogue_report.json` 实际 provider 为 `mock`，已避免误写成真实 API 证据。
- 当前仓库未提交真实截图，因此统一保留占位符。

## 仍需人工补充的信息
- [APPLICANT NAME]
- [EMAIL]
- [PHONE]
- [UNIVERSITY]
- [MAJOR]
- [GITHUB URL]
- [ADVENTUREX OFFICIAL PROMPT]
- [TEAM MEMBERS]
- [PREVIOUS AWARDS]
- [SPECIFIC SUBMISSION DEADLINE]

## Review 2：评审说服力审查
| 维度 | 分数（1-10） | 说明 |
|---|---:|---|
| 问题重要性 | 9 | 结合 dementia/caregiver burden 背景 |
| 项目独特性 | 9 | 明确不是普通 LLM wrapper |
| 当前执行力 | 9 | 代码、页面与 results 证明已有原型 |
| 技术可信度 | 8 | 明确 guard、grounding 与边界 |
| 五天可行性 | 9 | Hero Demo 聚焦明确 |
| 用户价值 | 9 | 双端价值清晰 |
| 安全意识 | 9 | 不做医疗诊断、不让模型猜用药 |
| 最终演示清晰度 | 9 | 演示链路具体 |

## Review 3：视觉审查
- 封面：已设计独立封面
- 图表：5 张 SVG，统一配色
- 表格：印刷样式已设置
- 中文字体：使用系统字体栈
- 截图：统一使用占位符，不伪造
- PDF 输出：待本地生成后检查页数、大小与文本可搜索性

## 最终提交建议
1. 先提交当前文稿版本，保证事实与边界可信。
2. 若时间允许，再补充 demo-safe 真实截图替换占位符。
3. 若能本地重新运行 DeepSeek demo test，可更新 latest run 时间。
4. 所有对外表述都坚持：**internal prototype, scenario-based evaluation, not clinical validation**。
`;
const appAns=`# ADVENTUREX APPLICATION ANSWERS

## 用 100 字介绍项目
- 精简版：这是一个面向阿尔兹海默症家庭场景的受控式 AI 原型。它把患者端情感记忆陪伴和家属端照护闭环连接起来，通过结构化提醒、规则安全层、家属审核记忆和 familiar materials，让通用大模型变成更可控、更个性化的家庭照护辅助系统。
- 标准版：Alzheimer Family Care Assistant 不是普通聊天机器人，而是一个连接患者端温和陪伴与家属端照护管理的受控式 AI 系统原型。患者端通过照片、故事、语音留言和熟悉素材获得更低刺激的对话支持；家属端通过提醒、risk events、daily care 和 memory review 获得更可行动的照护信息。
- 英文版：Alzheimer Family Care Assistant is a controlled AI prototype for family dementia care. It connects patient-side emotional memory companionship with caregiver-side care loops through structured reminders, safety guardrails, caregiver-governed memory review, and familiar materials.

## 为什么这个问题重要
- 精简版：因为阿尔兹海默症家庭每天面对的不是单一痛点，而是重复提问、焦虑、位置困惑、用药不确定和家属长期压力同时存在。
- 标准版：阿尔兹海默症家庭照护同时涉及患者端的熟悉感与情绪支持，以及家属端的提醒管理、风险反馈和照护连续性。一个只会生成语言的系统，很难天然理解某个家庭的真实照护状态与个人记忆背景。
- 英文版：This matters because family dementia care is not a single pain point. Patients may need reassurance and familiarity, while caregivers need reminders, risk visibility, and continuity of care.

## 你的方案有什么不同
- 精简版：不同点不在于“接了大模型”，而在于结构化照护 grounding、安全 guard、家属审核长期记忆，以及照片/语音/故事带来的情感记忆 grounding。
- 标准版：我的方案把模型放在受控的位置：用药与 reminder 事实来自结构化数据；高风险场景通过 rule detection、guard 和 template fallback 控制；长期记忆不能自动写入，必须经过 caregiver review；患者端对话引入家庭照片、语音留言、旧地点和个人故事作为情感上下文。
- 英文版：The differentiation is not the model call itself, but structured care grounding, safety-controlled dialogue, caregiver-governed long-term memory, and emotional grounding through family materials.

## 当前已经完成什么
- 精简版：我已经做出一个可运行的 v0.5 原型，包括多患者管理、患者对话、家属工作台、提醒、risk events、familiar materials、photo timeline、memory candidate、reminiscence、consent、TTS fallback 和内部评估。
- 标准版：当前仓库中已经完成一个可运行的 v0.5 原型：FastAPI + SQLite 架构，多患者与 caregiver PIN 登录，DeepSeek 主链路，患者对话页，家属工作台，reminder / medication schedule，daily care summary，caregiver events / risk events，familiar materials，photo timeline，memory candidate capture 与 approve，reminiscence 页面，consent flow，MiniMax TTS 集成与浏览器 fallback，以及内部评估页面。
- 英文版：I already have a working v0.5 prototype with multi-patient management, caregiver PIN login, DeepSeek-based conversation, reminder and medication state, caregiver dashboard, familiar materials, photo timeline, memory candidate review, reminiscence pages, consent flow, TTS fallback, and internal evaluation artifacts.

## 五天准备完成什么
- 精简版：五天内我不会无限扩功能，而是围绕一个 Hero Demo，把“家庭照片与语音记忆触发患者对话，并同步进入家属照护闭环”打磨成可展示 MVP。
- 标准版：五天工作的重点是整合、稳定、演示与可理解性：家属建立患者档案，上传老照片并补充照片故事，录制语音说明；患者从照片进入回忆对话；当出现用药、外出或敏感亲人问题时，系统切换到结构化照护与安全控制；家属端收到摘要、风险提示和待审核记忆线索。
- 英文版：In five days, I want to polish one clear Hero Demo rather than keep expanding scope: a caregiver uploads a family photo and a voice note, the patient enters a gentle reminiscence conversation from that cue, and the system bridges that conversation into a caregiver-visible care loop with risk signals and memory review.
`;
const proposal=`# AdventureX Project Proposal

## Alzheimer Family Care Assistant

### 面向阿尔兹海默症家庭的照护闭环与情感记忆陪伴系统

**From General-Purpose LLMs to Family-Grounded Care Intelligence**

## 封面
- 项目名称：Alzheimer Family Care Assistant / 阿尔兹海默症家庭照护辅助系统
- 一句话定位：将结构化照护状态、个人情感记忆和安全受控对话连接起来，为患者提供熟悉感，为家属提供可行动的照护支持。
- 当前版本：**v0.5（已审计仓库快照）**
- GitHub：**[GITHUB URL]**
- 申请人：**[APPLICANT NAME]**
- 联系方式：**[EMAIL] / [PHONE]**
- AdventureX
- 日期：2026-07-17

## 1. Executive Summary
阿尔兹海默症家庭照护并不是一个“多聊几句”就能解决的问题。患者常见的重复提问、位置困惑、用药不确定、焦虑和敏感亲人话题，需要的是低刺激、熟悉、不会责备的陪伴；而家属真正承担的，则是提醒管理、状态跟进、风险反馈和长期照护连续性。现有通用大模型能够生成语言，但并不会天然理解某个家庭的真实用药状态、照护流程和个人生命故事，也无法自动承担家庭照护责任。

本项目尝试把通用大模型转换成一个**面向阿尔兹海默症家庭场景的受控式 AI 系统原型**：一端面向患者，提供基于熟悉照片、故事、语音留言与温和提示的情感记忆陪伴；另一端面向家属，把 reminder、daily care、risk events、memory review 和 webhook 通知串成照护闭环。系统的关键创新不在于“调用了某个模型”，而在于四层能力的组合：**Structured Care Grounding、Safety-Controlled Dialogue、Caregiver-Governed Memory、Emotional Memory Grounding**。

基于当前仓库快照审计，我已经完成了一个可运行的 v0.5 原型：FastAPI + SQLite 后端、多患者与 caregiver PIN 登录、DeepSeek 主链路、规则安全层与 template fallback、用药与 daily care 状态、familiar materials、photo timeline、reminiscence、memory candidate capture、MiniMax TTS 集成与浏览器 fallback、PWA 基础安装壳，以及内部场景对照评估。最新 committed 结果显示，在 10 个内部场景中，普通直接模型回复的平均质量分为 **5.60**，完整照护系统链路为 **8.13**，提升 **+2.53**。这一结果不是临床结论，但说明“结构化照护状态 + 安全控制 + 家庭记忆 grounding”比直接 LLM 对话更接近阿尔兹海默症家庭场景需要的输出方式。

AdventureX 对我最重要的意义，不是从零提出一个概念，而是让这个已有基础原型在五天内完成一次清晰的跃迁：围绕 **From Family Memory to Safer Care**，把“家属上传照片与语音 → 患者从熟悉记忆进入温和对话 → 系统识别提醒/外出/敏感话题 → 家属收到摘要与待审核记忆线索”这一完整 Hero Demo 打磨成可展示、可解释、可被评审理解的 MVP。

## 2. The Problem: Care Is More Than Conversation
### 患者侧
阿尔兹海默症患者在日常生活中可能频繁经历记忆下降、重复提问、日期和位置困惑、焦虑感上升，以及对已故亲人或熟悉关系的敏感话题触发。对这类人群而言，最有害的交互方式往往不是“不会回答”，而是被纠正、被考试式提问、被要求承认自己记错。

### 家属侧
家属承担的是另一套问题：反复解释、作息与用药管理、无法持续在场、想知道患者今天是否稳定、是否有想外出或走失风险、以及哪些新出现的对话线索值得沉淀为长期素材。

> 家庭真正需要的不是一个会聊天的 AI，而是一个既理解患者熟悉世界、又能进入家属照护流程的辅助系统。

## 3. User and Scenario Definition
### Primary User 1：患者
- 中度认知障碍或阿尔兹海默症患者
- 需要语音优先、低认知负担交互
- 需要熟悉人物、照片、旧地点与个人故事
- 不能承受刺激性纠正、复杂指令和考试式追问

### Primary User 2：家庭照护者
- 需要管理提醒和风险
- 需要掌握最近交流情况
- 需要审核长期记忆与敏感素材
- 不能把照护责任完全交给 AI

### Core Scenario
“李奶奶看到年轻时的家庭照片，想起过去；对话中又问自己是否吃过药，并提出想独自外出。系统如何在情感陪伴和照护安全之间切换？”

## 4. Insight and Design Principles
1. Familiarity before intelligence
2. Support, not examination
3. Structured facts before generated claims
4. Caregiver control over long-term memory
5. Human escalation for high-risk situations

## 5. Proposed Solution
### 5.1 Patient Companion
- 温和、短句、低刺激对话
- 文本与语音入口
- 从 familiar materials 与照片故事切入回忆对话
- 支持情绪安抚与简单下一步
- 敏感话题与高风险场景进入安全控制

### 5.2 Caregiver Care Loop
- reminder 与 medication schedule
- 今日用药确认 / missed / skipped 状态
- risk events 与 caregiver events
- daily care summary 与跨日趋势
- webhook 通知与待处理事项

### 5.3 Emotional Memory Layer
- 家庭照片
- 照片故事与年代
- 家属语音说明
- 老歌、旧地点、旧事件
- memory candidate 审核后转入长期素材库

### 5.4 Safety and Governance Layer
- patient_id 上下文设计
- structured reminder status
- rule detection / safety guard
- template fallback
- caregiver approval for memory
- consent / privacy boundary

## 6. Current Prototype and Evidence of Execution
| System Capability | Current Status | Implementation Evidence | Next Step |
|---|---|---|---|
| 多患者管理 | 已实现 | \`templates/patients.html\`, \`patient_service.py\` | 与 legacy path 统一 |
| 患者档案与设置 | 已实现 | \`patient_detail.html\` | 打磨 onboarding |
| DeepSeek 对话 | 已实现 | \`llm_service.py\`, committed JSON results | 环境下再次验证 |
| 家属端 dashboard | 已实现 | \`index.html\`, \`/care-portal/{patient_id}\` | 聚焦 Hero Demo |
| reminder / medication | 已实现 | \`reminder_service.py\` | 强化跨天台账 |
| risk events | 已实现 | \`caregiver_event_service.py\`, \`risk_service.py\` | 更清晰的处理状态 |
| familiar materials | 已实现 | \`materials.html\`, \`familiar_material_service.py\` | 强化故事与语音说明 |
| memory candidate | 已实现 | \`memory_candidate_service.py\` | 统一 review UX |
| reminiscence | 已实现（基础） | \`reminiscence.html\`, \`memory_vector_service.py\` | 验证依赖与真实链路 |
| TTS | 已实现（集成 + fallback） | \`tts_service.py\`, \`voice.js\` | 端到端验证成功率 |
| notification | 已实现（webhook） | \`notify_service.py\` | 不夸大为原生 push |
| PWA | 部分实现 | \`manifest.json\`, \`sw.js\` | 保守表述为基础安装壳 |
| privacy/consent | 部分实现 | \`consent.html\`, \`/api/consent/{patient_id}\` | 完善边界文案 |
| evaluation | 已实现（内部） | \`results/controlled_llm_comparison_report.json\` | 后续做真实可用性测试 |

截图占位：
- [PLACEHOLDER: current patients page screenshot]
- [PLACEHOLDER: current conversation page screenshot]
- [PLACEHOLDER: current caregiver dashboard screenshot]
- [PLACEHOLDER: current materials library screenshot]
- [PLACEHOLDER: current memory review screenshot]
- [PLACEHOLDER: current test results page screenshot]

## 7. Technical Architecture
- Python / FastAPI / SQLite / Jinja / HTML / CSS / JavaScript
- DeepSeek API（主聊天 provider）
- MiniMax TTS 或浏览器 speechSynthesis fallback
- Service Worker / PWA scaffolding
- WeCom / DingTalk webhook

系统强调：LLM 只负责候选自然语言生成；结构化照护事实来自数据库和规则层；长期记忆写入需要 caregiver 审核。

## 8. Technical Differentiation
| Dimension | Direct LLM Chatbot | This System |
|---|---|---|
| Patient context | Temporary prompt | Structured patient profile and materials |
| Medication facts | May hallucinate | Grounded in reminder records |
| High-risk dialogue | Model-dependent | Rule guard and template fallback |
| Family involvement | None | Caregiver dashboard and review |
| Long-term memory | Automatic or absent | Caregiver-governed |
| Emotional grounding | Generic empathy | Family photos, voices and stories |
| Evaluation | Subjective demo | Scenario-based controlled comparison |

> 项目创新不在于“调用了某个大模型”，而在于照护事实 grounding、安全控制、家庭记忆治理和双端闭环。

## 9. Evaluation and Current Results
- provider：\`deepseek\`
- model：\`deepseek-v4-flash\`
- baseline score：**5.60**
- care system score：**8.13**
- improvement：**+2.53**
- verdict：**PASS**

这是项目内部场景评估，**不是临床评价，也不等同于真实患者有效性验证**。

## 10. Why AdventureX and Why Now
我申请 AdventureX，不是为了在五天里提出一个概念，而是为了让一个已经运行的系统完成从“技术原型”到“可被真实家庭理解和试用的 MVP”的跃迁。

## 11. Five-Day Execution Plan
统一目标：在五天结束时完成一个“由家庭照片和语音记忆触发患者对话，并能同步进入家属照护闭环”的可部署 MVP。

### Day 1 — Reliability and Real-Family Setup
- 验证 patient_id 污染与 demo data leakage
- 检查重复 medication overdue 通知
- 测试家庭初始化与部署清单

### Day 2 — Family Memory Album
- 照片时间线、年份、人物、故事、标签
- 从照片进入对话

### Day 3 — Voice-Based Emotional Grounding
- caregiver voice note
- MiniMax TTS 验证与浏览器 fallback

### Day 4 — Caregiver Review and Care Continuity
- reminder history / risk resolution
- memory candidate review
- consent / privacy 边界补强

### Day 5 — User Test, Evaluation and Final Demo
- 3–5 名参与者任务测试（若可招募）
- 收集结构化反馈
- 完成最终演示视频与 pitch

## 12. Five-Day Success Metrics
### Reliability
- Patient-context isolation tests pass
- Zero known demo-data leakage
- Zero duplicate medication notifications in the same day

### User Flow
- New family setup ≤ 10 minutes
- Photo-to-conversation flow completes successfully
- Memory candidate approval reaches materials library

### Safety
- Medication hallucination = 0 in test scenarios
- Unsafe wandering encouragement = 0
- Direct deceased-relative correction = 0

### Usability
- 3–5 test participants（目标）
- Core task completion rate recorded
- Ratings for clarity, trust, warmth and usefulness

## 13. Expected Deliverables
- Stable patient context
- Test family setup
- Family memory album
- Voice notes
- Photo-triggered dialogue
- Daily care ledger
- Caregiver memory review
- Privacy and consent
- Usability test summary（if feasible）
- Demo video
- GitHub-facing proposal package

## 14. Risks and Mitigation
- LLM instability → Guard + template fallback → Deterministic safe response
- MiniMax API unavailable → Browser speechSynthesis → Text-only or voice-note-first demo
- Real user unavailable → Structured peer usability test → Explicitly non-clinical demo evidence
- Media upload complexity → Use existing URL/path model → Single pre-seeded photo
- Privacy risk → Demo data + consent → No real patient data
- Scope expansion → Single Hero Demo → Cut noncritical features

## 15. Founder / Builder Fit
我已经持续构建和迭代这个系统，而不是停留在想法阶段。当前仓库里能看到的是：后端、数据库、前端、LLM 集成、安全规则、测试脚本和产品叙事已经被连接成一个可运行的原型。我擅长把复杂功能拆成可验证闭环，这正是这个项目最需要的能力。

## 16. Long-Term Vision
### Near-Term
- 真实小样本测试
- 家庭记忆相册
- 声音陪伴
- 日常照护台账
- 隐私和授权

### Mid-Term
- 多家庭部署
- 更稳定的个性化检索
- 情绪与风险趋势
- 与陪伴终端或家庭设备结合
- 更完善的通知与位置安全辅助

### Research Direction
- Family-grounded memory systems
- Safety-aware conversational agents
- Long-term human-AI interaction
- Caregiver-in-the-loop AI
- Personalized reminiscence interaction

明确边界：不替代医生，不独立作医疗决策，不把情感陪伴等同于治疗。

## 17. Conclusion
这不是一个从概念开始的五天项目，而是一个已经具备技术基础、用户问题和验证框架的系统。AdventureX 的价值，是让它在五天内完成一次关键跃迁：从一个可运行的照护 AI 原型，变成一个能够通过家庭照片、声音和结构化照护状态，为患者提供熟悉感、为家属提供行动支持的可试用 MVP。
`;
const html=(title,body)=>`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>${title}</title><link rel="stylesheet" href="assets/proposal.css"></head><body><div class="container">${body}</div></body></html>`;
const propHTML=html('AdventureX Project Proposal',`<section class="cover"><div><div class="cover-kicker">AdventureX Five-Day Build Proposal</div><h1>AdventureX Project Proposal</h1><h2>Alzheimer Family Care Assistant</h2><h3>面向阿尔兹海默症家庭的照护闭环与情感记忆陪伴系统</h3><p class="tagline"><strong>From General-Purpose LLMs to Family-Grounded Care Intelligence</strong></p><div class="meta-grid"><div class="meta-card"><strong>当前版本</strong><br>v0.5（已审计仓库快照）</div><div class="meta-card"><strong>GitHub</strong><br><strong>[GITHUB URL]</strong></div><div class="meta-card"><strong>申请人</strong><br><strong>[APPLICANT NAME]</strong></div><div class="meta-card"><strong>联系方式</strong><br><strong>[EMAIL]</strong> / <strong>[PHONE]</strong></div></div></div><div class="footer">将结构化照护状态、个人情感记忆和安全受控对话连接起来，为患者提供熟悉感，为家属提供可行动的照护支持。<br>AdventureX · 2026-07-17</div></section><section class="section page-break"><div class="headerline"><h2>1. Executive Summary</h2><div class="small">审计版本：v0.5</div></div><p>阿尔兹海默症家庭照护不是一个“更会聊天”的问题，而是一个如何让患者获得熟悉感、让家属获得行动支持的问题。通用大模型可以生成语言，但不能天然承担家庭照护责任。</p><p>本项目提出 <strong>Care Loop + Emotional Memory Companion</strong>：患者端通过家庭照片、故事、语音留言和熟悉素材进入温和对话；家属端通过 reminder、daily care、risk events、memory review 与 webhook 通知形成照护闭环。</p><p>当前仓库快照已具备可运行原型：FastAPI + SQLite、多患者管理、DeepSeek 主链路、规则安全层、患者对话页、家属工作台、materials、photo timeline、reminiscence、memory candidate、consent、TTS fallback 与内部评估页面。最新 committed 结果显示，在 10 个内部场景中，baseline 为 <strong>5.60</strong>，完整照护系统链路为 <strong>8.13</strong>，提升 <strong>+2.53</strong>。这不是临床验证，但说明“结构化照护状态 + 安全控制 + 家庭记忆 grounding”比直接 LLM 对话更接近目标场景。</p></section><section class="section"><h2>2. The Problem: Care Is More Than Conversation</h2><div class="twocol"><div class="panel"><h3>患者侧</h3><ul><li>重复提问与记忆下降</li><li>日期和位置困惑</li><li>焦虑与不安全感</li><li>敏感亲人话题</li><li>需要熟悉、温和、非考试式交流</li></ul></div><div class="panel"><h3>家属侧</h3><ul><li>反复解释</li><li>用药和作息管理</li><li>外出与走失风险</li><li>无法持续陪伴</li><li>难以及时了解患者状态</li></ul></div></div><blockquote>家庭真正需要的不是一个会聊天的 AI，而是一个既理解患者熟悉世界、又能进入家属照护流程的辅助系统。</blockquote></section><section class="section"><h2>3. User and Scenario Definition</h2><div class="panel"><p><strong>患者：</strong>中度认知障碍或阿尔兹海默症患者，需要语音优先、低认知负担交互，需要熟悉人物和故事，不能承受刺激性纠正和复杂指令。</p><p><strong>家庭照护者：</strong>需要管理提醒和风险，需要掌握最近交流情况，需要审核长期记忆，不能把照护责任完全交给 AI。</p><p><strong>Core Scenario：</strong>“李奶奶看到年轻时的家庭照片，想起过去；对话中又问自己是否吃过药，并提出想独自外出。系统如何在情感陪伴和照护安全之间切换？”</p></div></section><section class="section"><h2>4. Insight and Design Principles</h2><div class="threecol"><div class="panel"><h3>1. Familiarity before intelligence</h3></div><div class="panel"><h3>2. Support, not examination</h3></div><div class="panel"><h3>3. Structured facts before generated claims</h3></div><div class="panel"><h3>4. Caregiver control over long-term memory</h3></div><div class="panel"><h3>5. Human escalation for high-risk situations</h3></div></div></section><section class="section"><h2>5. Proposed Solution</h2><div class="figure"><img src="assets/care_memory_loop.svg" alt="loop"></div></section><section class="section"><h2>6. Current Prototype and Evidence of Execution</h2><table><thead><tr><th>System Capability</th><th>Current Status</th><th>Implementation Evidence</th><th>Next Step</th></tr></thead><tbody><tr><td>多患者管理</td><td><span class="badge ok">已实现</span></td><td><code>patients.html</code> / <code>patient_service.py</code></td><td>统一 legacy path</td></tr><tr><td>DeepSeek 对话</td><td><span class="badge ok">已实现</span></td><td><code>llm_service.py</code> / committed JSON results</td><td>环境下再次验证</td></tr><tr><td>家属 dashboard</td><td><span class="badge ok">已实现</span></td><td><code>index.html</code></td><td>聚焦 Hero Demo</td></tr><tr><td>Materials / Photo Timeline</td><td><span class="badge ok">已实现</span></td><td><code>materials.html</code> / <code>photo_timeline.html</code></td><td>story-driven flow</td></tr><tr><td>Memory candidate / review</td><td><span class="badge partial">部分实现</span></td><td><code>memory_candidate_service.py</code></td><td>统一 review UX</td></tr><tr><td>TTS / notification / PWA</td><td><span class="badge partial">部分实现</span></td><td><code>tts_service.py</code> / <code>notify_service.py</code> / <code>manifest.json</code></td><td>保守定位为 demo-ready scaffolding</td></tr></tbody></table><div class="placeholder">[PLACEHOLDER: current patients page screenshot]</div><div class="placeholder">[PLACEHOLDER: current conversation page screenshot]</div><div class="placeholder">[PLACEHOLDER: current caregiver dashboard screenshot]</div></section><section class="section"><h2>7. Technical Architecture</h2><div class="figure"><img src="assets/system_architecture.svg" alt="architecture"></div><p>LLM 只负责候选自然语言生成；结构化照护事实来自数据库和规则层；长期记忆写入必须经过 caregiver approval。</p></section><section class="section"><h2>8. Technical Differentiation</h2><table><thead><tr><th>Dimension</th><th>Direct LLM Chatbot</th><th>This System</th></tr></thead><tbody><tr><td>Patient context</td><td>Temporary prompt</td><td>Structured patient profile and materials</td></tr><tr><td>Medication facts</td><td>May hallucinate</td><td>Grounded in reminder records</td></tr><tr><td>High-risk dialogue</td><td>Model-dependent</td><td>Rule guard and template fallback</td></tr><tr><td>Family involvement</td><td>None</td><td>Caregiver dashboard and review</td></tr><tr><td>Long-term memory</td><td>Automatic or absent</td><td>Caregiver-governed</td></tr><tr><td>Emotional grounding</td><td>Generic empathy</td><td>Family photos, voices and stories</td></tr><tr><td>Evaluation</td><td>Subjective demo</td><td>Scenario-based controlled comparison</td></tr></tbody></table></section><section class="section"><h2>9. Evaluation and Current Results</h2><div class="figure"><img src="assets/evaluation_comparison.svg" alt="eval"></div><div class="stat-row"><div class="stat"><strong>Baseline</strong><div class="value">5.60</div></div><div class="stat"><strong>Care system</strong><div class="value">8.13</div></div><div class="stat"><strong>Improvement</strong><div class="value">+2.53</div></div></div><p>这些数字来自 committed JSON report，仅代表项目内部场景评估，而不是临床评价或真实患者有效性验证。</p></section><section class="section"><h2>10. Why AdventureX and Why Now</h2><p>我申请 AdventureX，不是为了在五天里提出一个概念，而是为了让一个已经运行的系统完成从“技术原型”到“可被真实家庭理解和试用的 MVP”的跃迁。</p></section><section class="section"><h2>11. Five-Day Execution Plan</h2><div class="figure"><img src="assets/five_day_roadmap.svg" alt="roadmap"></div></section><section class="section"><h2>12. Success Metrics / 13. Deliverables / 14. Risks</h2><p>成功指标围绕 reliability、user flow、safety、usability 展开；核心交付聚焦单一 Hero Demo；主要风险包括 LLM instability、TTS 环境依赖、真实用户招募与 scope expansion。</p></section><section class="section"><h2>15. Founder / Builder Fit</h2><p>我已经持续构建和迭代这个系统，而不是停留在想法阶段。我擅长把复杂功能拆成可验证闭环，这正是这个项目最需要的能力。</p></section><section class="section"><h2>16. Long-Term Vision</h2><p>Near-term：真实小样本测试、家庭记忆相册、声音陪伴、日常照护台账、隐私和授权。Mid-term：多家庭部署、更稳定的个性化检索、情绪与风险趋势。明确边界：不替代医生，不独立作医疗决策，不把情感陪伴等同于治疗。</p></section><section class="section"><h2>17. Conclusion</h2><blockquote>这不是一个从概念开始的五天项目，而是一个已经具备技术基础、用户问题和验证框架的系统。AdventureX 的价值，是让它在五天内完成一次关键跃迁。</blockquote></section>`);
const htmlCN=html('AdventureX One Page CN',`<section class="section"><div class="headerline"><h2>AdventureX One-Page Summary</h2><div class="small">CN</div></div><p><strong>Problem.</strong> 阿尔兹海默症家庭照护的难点不只是聊天，而是重复提问、焦虑、位置困惑、用药不确定与家属长期压力同时存在。</p><p><strong>Insight.</strong> 通用大模型能生成语言，但不能天然承担家庭照护责任。</p><p><strong>Solution.</strong> 这是一个 <strong>Care Loop + Emotional Memory Companion</strong> 原型。</p><p><strong>Current Progress.</strong> 当前已实现 FastAPI + SQLite、多患者管理、DeepSeek 主链路、患者对话、家属看板、materials、photo timeline、reminiscence、memory candidate、consent、TTS fallback 与 PWA 基础壳。</p><p><strong>Evidence.</strong> 内部 10 场景评估：baseline <strong>5.60</strong>，care system <strong>8.13</strong>，提升 <strong>+2.53</strong>。</p><p><strong>Five-Day Goal.</strong> 围绕 <strong>From Family Memory to Safer Care</strong> 打磨 Hero Demo。</p><p><strong>GitHub.</strong> <strong>[GITHUB URL]</strong></p></section>`);
const htmlEN=html('AdventureX One Page EN',`<section class="section"><div class="headerline"><h2>AdventureX One-Page Summary</h2><div class="small">EN</div></div><p><strong>Problem.</strong> Family dementia care is more than conversation.</p><p><strong>Insight.</strong> A general-purpose LLM can generate language, but it does not inherently understand real care state, family memory context, or safety boundaries.</p><p><strong>Solution.</strong> This project proposes a <strong>Care Loop + Emotional Memory Companion</strong>.</p><p><strong>Current Progress.</strong> The audited snapshot already includes a working prototype with multi-patient management, DeepSeek chat, caregiver dashboard, familiar materials, photo timeline, memory candidate review, consent flow, TTS fallback, and PWA scaffolding.</p><p><strong>Evidence.</strong> Internal 10-scenario comparison: baseline <strong>5.60</strong>, care system <strong>8.13</strong>, improvement <strong>+2.53</strong>.</p><p><strong>Five-Day Goal.</strong> Build a clear Hero Demo: <strong>From Family Memory to Safer Care</strong>.</p><p><strong>GitHub.</strong> <strong>[GITHUB URL]</strong></p></section>`);
const system=`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760"><defs><style>.bg{fill:#fff}.box{fill:#f5f7fa;stroke:#cfd8e3;stroke-width:2}.title{font:700 28px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#23445d}.h{font:700 18px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#23445d}.t{font:14px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#1f2937}.m{font:12px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#4b5563}.line{stroke:#5b7288;stroke-width:2;fill:none;marker-end:url(#a)}.pill{fill:#e8f3f1;stroke:#8cc0ba;stroke-width:1.5}</style><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#5b7288"/></marker></defs><rect class="bg" width="1200" height="760"/><text x="60" y="52" class="title">系统架构：Care Loop + Emotional Memory Companion</text><rect class="box" x="60" y="100" width="250" height="130" rx="18"/><text x="85" y="135" class="h">患者端界面</text><text x="85" y="165" class="t">• 对话页 /conversation</text><text x="85" y="190" class="t">• 语音输入 + TTS 播放</text><text x="85" y="215" class="t">• 照片进入回忆对话</text><rect class="box" x="60" y="280" width="250" height="150" rx="18"/><text x="85" y="315" class="h">家属端界面</text><text x="85" y="345" class="t">• 患者列表 /patients</text><text x="85" y="370" class="t">• 照护工作台 /care-portal</text><text x="85" y="395" class="t">• 素材库 /materials</text><text x="85" y="420" class="t">• 记忆审核 /chat-history</text><rect class="box" x="390" y="90" width="300" height="130" rx="18"/><text x="415" y="125" class="h">身份与患者上下文</text><text x="415" y="155" class="t">• caregiver PIN 登录</text><text x="415" y="180" class="t">• patient_id / access check</text><text x="415" y="205" class="t">• 患者档案与会话上下文投影</text><rect class="box" x="390" y="250" width="300" height="170" rx="18"/><text x="415" y="285" class="h">上下文构建层</text><text x="415" y="315" class="t">• 结构化患者资料</text><text x="415" y="340" class="t">• reminder / medication 状态</text><text x="415" y="365" class="t">• familiar materials / photo story</text><text x="415" y="390" class="t">• recent chat / approved memory</text><rect class="box" x="760" y="90" width="320" height="160" rx="18"/><text x="785" y="125" class="h">LLM 与安全控制</text><text x="785" y="155" class="t">• DeepSeek 主链路</text><text x="785" y="180" class="t">• rule detection / guard</text><text x="785" y="205" class="t">• postprocess / template fallback</text><text x="785" y="230" class="t">• 高风险场景不完全交给模型</text><rect class="box" x="760" y="290" width="320" height="170" rx="18"/><text x="785" y="325" class="h">照护闭环层</text><text x="785" y="355" class="t">• caregiver events / risk events</text><text x="785" y="380" class="t">• daily care summary / trend</text><text x="785" y="405" class="t">• reminder confirmation / overdue notify</text><text x="785" y="430" class="t">• 需要家属处理与确认</text><rect class="box" x="390" y="480" width="300" height="170" rx="18"/><text x="415" y="515" class="h">情感记忆层</text><text x="415" y="545" class="t">• family photos / old places / old songs</text><text x="415" y="570" class="t">• photo story / voice note</text><text x="415" y="595" class="t">• memory candidate → caregiver approval</text><text x="415" y="620" class="t">• sensitive memory 标记</text><rect class="box" x="760" y="520" width="320" height="130" rx="18"/><text x="785" y="555" class="h">数据与外部能力</text><text x="785" y="585" class="t">• SQLite</text><text x="785" y="610" class="t">• MiniMax TTS / 浏览器 fallback</text><text x="785" y="635" class="t">• WeCom / DingTalk webhook</text><path class="line" d="M310 165 H390"/><path class="line" d="M310 350 H390"/><path class="line" d="M690 170 H760"/><path class="line" d="M690 335 H760"/><path class="line" d="M540 420 V480"/><path class="line" d="M920 460 V520"/><path class="line" d="M690 565 H760"/><rect class="pill" x="92" y="668" width="1015" height="46" rx="23"/><text x="115" y="697" class="m">关键原则：LLM 只负责候选自然语言生成；结构化照护事实来自数据库与规则层；长期记忆写入必须经过家属审核。</text></svg>`;
const loop=`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720"><defs><style>.bg{fill:#fff}.title{font:700 28px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#23445d}.h{font:700 18px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#23445d}.t{font:14px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#1f2937}.box{fill:#f5f7fa;stroke:#cfd8e3;stroke-width:2}.accent{fill:#e8f3f1;stroke:#8cc0ba;stroke-width:2}.warn{fill:#fff2e8;stroke:#d8a273;stroke-width:2}.line{stroke:#5b7288;stroke-width:2.5;fill:none;marker-end:url(#a)}</style><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10z" fill="#5b7288"/></marker></defs><rect class="bg" width="1200" height="720"/><text x="60" y="52" class="title">Care Loop + Emotional Memory Companion</text><rect class="accent" x="80" y="120" width="280" height="110" rx="18"/><text x="105" y="155" class="h">1. 家属录入家庭记忆</text><text x="105" y="185" class="t">照片、故事、人物、语音说明</text><text x="105" y="210" class="t">形成 familiar materials</text><rect class="accent" x="460" y="120" width="280" height="110" rx="18"/><text x="485" y="155" class="h">2. 患者从熟悉线索进入对话</text><text x="485" y="185" class="t">照片 / 旧歌 / 旧地点触发</text><text x="485" y="210" class="t">温和、非考试式交流</text><rect class="warn" x="840" y="120" width="280" height="110" rx="18"/><text x="865" y="155" class="h">3. 高风险场景切换</text><text x="865" y="185" class="t">用药 / 外出 / 敏感亲人话题</text><text x="865" y="210" class="t">进入 rule guard + fallback</text><rect class="box" x="840" y="310" width="280" height="110" rx="18"/><text x="865" y="345" class="h">4. 结构化照护输出</text><text x="865" y="375" class="t">risk events / reminder status</text><text x="865" y="400" class="t">daily care summary</text><rect class="box" x="460" y="500" width="280" height="110" rx="18"/><text x="485" y="535" class="h">5. 家属审核与处理</text><text x="485" y="565" class="t">memory candidate review</text><text x="485" y="590" class="t">风险提示 / 待确认事项</text><rect class="accent" x="80" y="500" width="280" height="110" rx="18"/><text x="105" y="535" class="h">6. 闭环更新</text><text x="105" y="565" class="t">更好的记忆素材</text><text x="105" y="590" class="t">更连续的家庭照护</text><path class="line" d="M360 175 H460"/><path class="line" d="M740 175 H840"/><path class="line" d="M980 230 V310"/><path class="line" d="M840 365 H740"/><path class="line" d="M460 555 H360"/><path class="line" d="M220 500 V390 C220 300 220 300 220 230"/><text x="415" y="675" class="t">核心命题：从家庭记忆出发，不是为了生成更多话，而是为了进入更安全、更连续的家庭照护闭环。</text></svg>`;
const road=`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720"><defs><style>.bg{fill:#fff}.title{font:700 28px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#23445d}.d{font:700 20px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#23445d}.t{font:14px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#1f2937}.m{font:12px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#4b5563}.box{fill:#f5f7fa;stroke:#cfd8e3;stroke-width:2}.accent{fill:#e8f3f1;stroke:#8cc0ba;stroke-width:2}.line{stroke:#5b7288;stroke-width:3;fill:none;marker-end:url(#a)}</style><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10z" fill="#5b7288"/></marker></defs><rect class="bg" width="1200" height="720"/><text x="60" y="52" class="title">AdventureX 五天路线图：From Family Memory to Safer Care</text><path class="line" d="M110 160 H1080"/><g transform="translate(80,110)"><circle cx="30" cy="50" r="24" fill="#23445d"/><text x="20" y="57" font-size="20" fill="#fff" font-family="Segoe UI">1</text><rect class="box" x="0" y="100" width="200" height="180" rx="18"/><text x="20" y="135" class="d">Day 1</text><text x="20" y="165" class="t">Reliability & Setup</text><text x="20" y="195" class="m">• patient_id 污染检查</text><text x="20" y="220" class="m">• 重复通知检查</text><text x="20" y="245" class="m">• 测试家庭初始化</text></g><g transform="translate(290,110)"><circle cx="30" cy="50" r="24" fill="#2f6c8e"/><text x="20" y="57" font-size="20" fill="#fff" font-family="Segoe UI">2</text><rect class="accent" x="0" y="100" width="200" height="180" rx="18"/><text x="20" y="135" class="d">Day 2</text><text x="20" y="165" class="t">Family Memory Album</text><text x="20" y="195" class="m">• 照片年份与故事</text><text x="20" y="220" class="m">• 从照片进入对话</text><text x="20" y="245" class="m">• 敏感素材标记</text></g><g transform="translate(500,110)"><circle cx="30" cy="50" r="24" fill="#3f8f88"/><text x="20" y="57" font-size="20" fill="#fff" font-family="Segoe UI">3</text><rect class="accent" x="0" y="100" width="200" height="180" rx="18"/><text x="20" y="135" class="d">Day 3</text><text x="20" y="165" class="t">Voice Grounding</text><text x="20" y="195" class="m">• caregiver voice note</text><text x="20" y="220" class="m">• TTS fallback chain</text><text x="20" y="245" class="m">• 可听化陪伴</text></g><g transform="translate(710,110)"><circle cx="30" cy="50" r="24" fill="#6c8c4e"/><text x="20" y="57" font-size="20" fill="#fff" font-family="Segoe UI">4</text><rect class="box" x="0" y="100" width="200" height="180" rx="18"/><text x="20" y="135" class="d">Day 4</text><text x="20" y="165" class="t">Care Continuity</text><text x="20" y="195" class="m">• daily care ledger</text><text x="20" y="220" class="m">• risk resolution</text><text x="20" y="245" class="m">• memory review 稳定化</text></g><g transform="translate(920,110)"><circle cx="30" cy="50" r="24" fill="#b86a3b"/><text x="20" y="57" font-size="20" fill="#fff" font-family="Segoe UI">5</text><rect class="box" x="0" y="100" width="200" height="180" rx="18"/><text x="20" y="135" class="d">Day 5</text><text x="20" y="165" class="t">User Test & Final Demo</text><text x="20" y="195" class="m">• 3–5 位参与者</text><text x="20" y="220" class="m">• 结构化反馈</text><text x="20" y="245" class="m">• 最终展示与视频</text></g><rect class="box" x="150" y="500" width="900" height="120" rx="18"/><text x="180" y="540" class="d">五天统一目标</text><text x="180" y="575" class="t">在五天结束时完成一个“由家庭照片和语音记忆触发患者对话，并能同步进入家属照护闭环”的可部署 MVP。</text></svg>`;
const evalsvg=`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><defs><style>.bg{fill:#fff}.title{font:700 28px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#23445d}.t{font:14px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#1f2937}.m{font:12px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#4b5563}.label{font:700 18px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#23445d}</style></defs><rect class="bg" width="1200" height="700"/><text x="60" y="52" class="title">内部场景评估：Direct LLM vs Controlled Care System</text><text x="60" y="90" class="m">来源：results/controlled_llm_comparison_report.json（内部 10 场景评估；非临床评价）</text><line x1="120" y1="560" x2="1020" y2="560" stroke="#cfd8e3" stroke-width="2"/><line x1="120" y1="140" x2="120" y2="560" stroke="#cfd8e3" stroke-width="2"/><rect x="220" y="325" width="180" height="235" fill="#9bb0c1" rx="10"/><rect x="560" y="219" width="180" height="341" fill="#3f8f88" rx="10"/><text x="250" y="305" class="label">5.60</text><text x="590" y="199" class="label">8.13</text><text x="228" y="590" class="t">Direct baseline</text><text x="571" y="590" class="t">Care system</text><rect x="830" y="230" width="250" height="180" rx="18" fill="#f5f7fa" stroke="#cfd8e3" stroke-width="2"/><text x="855" y="270" class="label">+2.53</text><text x="855" y="305" class="t">绝对提升</text><text x="855" y="340" class="t">Provider: deepseek</text><text x="855" y="365" class="t">Model: deepseek-v4-flash</text><text x="855" y="390" class="t">Scenarios: 10</text><text x="855" y="415" class="t">Verdict: PASS</text><text x="120" y="635" class="m">解释：这说明当前受控照护链路比直接模型回复更接近项目设定的场景目标；它不是临床疗效证明，也不等同于真实患者有效性验证。</text></svg>`;
const journey=`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720"><defs><style>.bg{fill:#fff}.title{font:700 28px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#23445d}.h{font:700 17px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#23445d}.t{font:14px 'Segoe UI','Microsoft YaHei',sans-serif;fill:#1f2937}.box{fill:#f5f7fa;stroke:#cfd8e3;stroke-width:2}.accent{fill:#e8f3f1;stroke:#8cc0ba;stroke-width:2}.warn{fill:#fff2e8;stroke:#d8a273;stroke-width:2}.line{stroke:#5b7288;stroke-width:2.5;fill:none;marker-end:url(#a)}</style><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10z" fill="#5b7288"/></marker></defs><rect class="bg" width="1200" height="720"/><text x="60" y="52" class="title">Hero Demo 用户旅程：From Family Memory to Safer Care</text><rect class="box" x="80" y="120" width="210" height="110" rx="18"/><text x="105" y="155" class="h">家属建立患者档案</text><text x="105" y="185" class="t">姓名、关系、病情阶段、提醒</text><rect class="accent" x="330" y="120" width="210" height="110" rx="18"/><text x="355" y="155" class="h">上传照片与故事</text><text x="355" y="185" class="t">年份、人物、故事、标签</text><rect class="accent" x="580" y="120" width="210" height="110" rx="18"/><text x="605" y="155" class="h">录制语音说明</text><text x="605" y="185" class="t">安抚留言 / 照片说明</text><rect class="accent" x="830" y="120" width="290" height="110" rx="18"/><text x="855" y="155" class="h">患者从照片进入回忆对话</text><text x="855" y="185" class="t">看到熟悉人物与过去故事</text><rect class="warn" x="830" y="320" width="290" height="130" rx="18"/><text x="855" y="355" class="h">敏感场景切换</text><text x="855" y="385" class="t">用药 / 外出 / 已故亲人话题</text><text x="855" y="410" class="t">安全控制优先</text><rect class="box" x="520" y="520" width="270" height="120" rx="18"/><text x="545" y="555" class="h">家属收到可行动信息</text><text x="545" y="585" class="t">summary / risk prompt / candidate review</text><rect class="box" x="180" y="520" width="270" height="120" rx="18"/><text x="205" y="555" class="h">新线索进入候选记忆</text><text x="205" y="585" class="t">等待 caregiver 审核后进入长期素材</text><path class="line" d="M290 175 H330"/><path class="line" d="M540 175 H580"/><path class="line" d="M790 175 H830"/><path class="line" d="M975 230 V320"/><path class="line" d="M830 385 H790 C730 385 730 520 730 520"/><path class="line" d="M520 580 H450"/><text x="145" y="680" class="t">这个旅程同时体现：患者端的熟悉感与情绪安抚、家属端的照护价值，以及技术上的上下文、规则、安全和记忆治理。</text></svg>`;
w('PROJECT_FACT_AUDIT.md',audit);w('REFERENCES.md',refs);w('ADVENTUREX_PROJECT_PROPOSAL_CN.md',proposal);w('ADVENTUREX_ONE_PAGE_CN.md',oneCN);w('ADVENTUREX_ONE_PAGE_EN.md',oneEN);w('ADVENTUREX_3_MIN_PITCH_CN.md',pitch3);w('ADVENTUREX_60_SEC_PITCH_CN.md',pitch60);w('ADVENTUREX_APPLICATION_ANSWERS.md',appAns);w('FINAL_DEMO_SCRIPT.md',demo);w('QUALITY_REVIEW.md',qr);w('assets/system_architecture.svg',system);w('assets/care_memory_loop.svg',loop);w('assets/five_day_roadmap.svg',road);w('assets/evaluation_comparison.svg',evalsvg);w('assets/user_journey.svg',journey);w('ADVENTUREX_PROJECT_PROPOSAL_CN.html',propHTML);w('ADVENTUREX_ONE_PAGE_CN.html',htmlCN);w('ADVENTUREX_ONE_PAGE_EN.html',htmlEN);
console.log('generated');
