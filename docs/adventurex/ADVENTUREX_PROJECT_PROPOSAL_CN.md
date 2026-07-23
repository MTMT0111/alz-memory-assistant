# AdventureX Project Proposal

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
| 多患者管理 | 已实现 | `templates/patients.html`, `patient_service.py` | 与 legacy path 统一 |
| 患者档案与设置 | 已实现 | `patient_detail.html` | 打磨 onboarding |
| DeepSeek 对话 | 已实现 | `llm_service.py`, committed JSON results | 环境下再次验证 |
| 家属端 dashboard | 已实现 | `index.html`, `/care-portal/{patient_id}` | 聚焦 Hero Demo |
| reminder / medication | 已实现 | `reminder_service.py` | 强化跨天台账 |
| risk events | 已实现 | `caregiver_event_service.py`, `risk_service.py` | 更清晰的处理状态 |
| familiar materials | 已实现 | `materials.html`, `familiar_material_service.py` | 强化故事与语音说明 |
| memory candidate | 已实现 | `memory_candidate_service.py` | 统一 review UX |
| reminiscence | 已实现（基础） | `reminiscence.html`, `memory_vector_service.py` | 验证依赖与真实链路 |
| TTS | 已实现（集成 + fallback） | `tts_service.py`, `voice.js` | 端到端验证成功率 |
| notification | 已实现（webhook） | `notify_service.py` | 不夸大为原生 push |
| PWA | 部分实现 | `manifest.json`, `sw.js` | 保守表述为基础安装壳 |
| privacy/consent | 部分实现 | `consent.html`, `/api/consent/{patient_id}` | 完善边界文案 |
| evaluation | 已实现（内部） | `results/controlled_llm_comparison_report.json` | 后续做真实可用性测试 |

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
- provider：`deepseek`
- model：`deepseek-v4-flash`
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
