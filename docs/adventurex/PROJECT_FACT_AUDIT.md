# PROJECT FACT AUDIT

> 审计范围：当前仓库快照（代码、模板、静态资源、results、docs、scripts）。
> 事实优先级：代码与数据库结构 > 测试脚本与 `results/*.json` > README/docs > 旧版本文档。
> 所有结论仅代表当前仓库快照，不代表已完成真实部署、临床验证或真实家庭测试。

## 当前版本结论

- **当前最可信版本：v0.5**
- 证据：`README.md`、`CHANGELOG.md`、`docs/V0_5_SYSTEM_OVERVIEW.md`、`app/main.py`
- 说明：仓库中存在部分 v0.6 / v0.7 方向能力雏形，但没有足够发布证据把当前系统正式定义为 v0.6、v0.7 或 v0.8。
- Git 历史：**Needs manual confirmation**（当前仓库快照不可审计有效 git log/tag）。

## 当前页面与 API 摘要

### 页面（代表性）
- `/login`：caregiver PIN 登录
- `/patients`：患者列表与多患者管理
- `/care-portal/{patient_id}`：家属照护工作台
- `/conversation/{patient_id}`：患者端对话
- `/patient/{patient_id}/settings`：患者设置 / 用药 / 团队 / 导出
- `/materials/{patient_id}`：熟悉素材库
- `/photo-timeline/{patient_id}`：家庭记忆相册 / 照片时间线
- `/chat-history/{patient_id}`：会话质量历史
- `/reminiscence/{patient_id}`：回忆陪伴页
- `/care-trend/{patient_id}`：跨日照护趋势
- `/consent/{patient_id}`：知情同意
- `/settings`：通知 / 存储 / PWA 状态
- `/location-safety`：位置安全占位页

### 代表性 API
- `/api/login`, `/api/logout`
- `/api/patients`, `/api/patients/{patient_id}`
- `/chat`, `/api/chat-history/{patient_id}`, `/api/chat-history/{patient_id}/sessions`
- `/api/reminders/{patient_id}`, `/api/medication-taken/{patient_id}`
- `/api/daily-care/{patient_id}/today`, `/api/daily-summary/{patient_id}`
- `/api/materials/{patient_id}`, `/api/materials/{patient_id}/timeline`
- `/api/memory-candidates/{patient_id}`, `/api/memory-candidates/{patient_id}/{candidate_id}/approve`
- `/api/caregiver/{patient_id}/events`, `/api/caregiver/{patient_id}/summary`
- `/api/consent/{patient_id}`
- `/api/tts`, `/api/stt`
- `/api/settings/test-notify`, `/api/settings/notify-webhook`

## A. 已实现功能

| 模块 | 证据文件 | 页面/API | 测试证据 | 当前状态 |
|---|---|---|---|---|
| FastAPI + SQLite 原型 | `app/main.py`, `app/init_db.py` | 全站 | `scripts/run_v05_acceptance_check.py` | 已实现 |
| Caregiver PIN 登录 | `templates/login.html`, `app/main.py` | `/login`, `/api/login` | 代码证据 | 已实现 |
| 多患者管理 | `templates/patients.html`, `app/services/patient_service.py` | `/patients`, `/api/patients/*` | 代码证据 | 已实现 |
| 患者设置 / 用药 / 团队 | `templates/patient_detail.html`, `app/services/reminder_service.py` | `/patient/{patient_id}/settings` | 代码证据 | 已实现 |
| DeepSeek 主链路 | `app/services/llm_service.py` | `/chat` | `results/controlled_llm_comparison_report.json`, `results/deepseek_demo_patient_report.json` | 已实现 |
| 规则安全层 + template fallback | `app/services/llm_service.py`, `app/services/conversation_style_engine.py` | `/chat` | `results/controlled_llm_comparison_report.json` | 已实现 |
| 患者端对话 | `templates/conversation.html`, `static/script.js`, `static/voice.js` | `/conversation/{patient_id}` | `scripts/test_page_chat_deepseek.py` | 已实现 |
| reminder / medication schedule | `app/services/reminder_service.py`, `templates/index.html` | `/api/reminders/{patient_id}` | `scripts/test_reminder_status.py` | 已实现 |
| daily care / trend | `app/services/daily_summary_service.py`, `templates/care_trend.html` | `/api/daily-care/{patient_id}/today`, `/care-trend/{patient_id}` | `scripts/test_daily_care_loop.py` | 已实现 |
| caregiver events / risk events | `app/services/caregiver_event_service.py`, `app/services/risk_service.py` | `/api/caregiver/{patient_id}/events` | `results/deepseek_demo_patient_report.json` | 已实现 |
| familiar materials | `templates/materials.html`, `app/services/familiar_material_service.py` | `/materials/{patient_id}` | `scripts/test_materials_module.py` | 已实现 |
| photo timeline | `templates/photo_timeline.html` | `/photo-timeline/{patient_id}` | 代码证据 | 已实现 |
| memory candidate capture/approve | `app/services/memory_candidate_service.py` | `/api/memory-candidates/*` | `scripts/test_memory_candidate_flow.py` | 已实现 |
| reminiscence | `templates/reminiscence.html`, `app/services/memory_vector_service.py` | `/reminiscence/{patient_id}` | `scripts/test_reminiscence_page.py` | 已实现（基础） |
| consent gate | `templates/consent.html`, `app/services/consent_service.py` | `/consent/{patient_id}` | 代码证据 | 已实现 |
| MiniMax TTS + browser fallback | `app/services/tts_service.py`, `static/voice.js` | `/api/tts` | `scripts/test_tts_service.py` | 已实现（环境依赖） |
| webhook 通知 | `app/services/notify_service.py` | `/api/settings/test-notify` | 代码证据 | 已实现 |
| PWA scaffolding / SW | `static/manifest.json`, `static/sw.js`, `templates/base.html` | 全站 | 代码证据 | 已实现 |
| 测试结果展示 | `templates/test_results.html`, `app/main.py` | `/test-results` | `results/*.json` | 已实现 |

## B. 部分实现功能

| 功能 | 已完成部分 | 尚未完成部分 | 风险 |
|---|---|---|---|
| patient_id 上下文隔离 | 非 demo prompt 防污染规则；多患者 patient_id 已进入部分链路；有 `scripts/test_patient_context.py` | 鉴权与 access check 不一致；legacy profile 与 UUID patient 双模型并存 | 不可夸大为完整隔离 |
| Demo 数据不污染真实患者 | 有专门 prompt 规则与脚本 | 脚本只构造 prompt，不发真实请求 | 只能写成“已有防污染设计” |
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
