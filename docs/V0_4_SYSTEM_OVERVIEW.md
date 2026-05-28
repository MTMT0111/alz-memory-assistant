# v0.4 System Overview：DeepSeek 主模型 + 提醒闭环 + 熟悉素材 + 对照评估

> 说明：本文件保留为 v0.4 基线说明。当前项目已继续升级到 v0.5，新增“每日照护闭环”“家属审核式记忆沉淀”和 `/demo-flow`。最新说明见 `docs/V0_5_DAILY_CARE_AND_MEMORY_CAPTURE.md`。

## 1. 当前版本定位

v0.4 不是普通聊天机器人，也不是泛化的 AI 对话网站，而是面向阿尔兹海默症家庭照护场景的软件原型。系统围绕患者端低刺激陪伴、家属端风险反馈、提醒状态闭环、熟悉素材辅助和可验证的 LLM 安全控制来设计。目标不是让模型自由发挥，而是让模型在规则、结构化数据和家属协作边界内工作，帮助家庭更稳定地处理重复提问、用药不确定、位置困惑、焦虑、外出风险和敏感回忆话题。

## 2. 核心系统闭环

患者端输入  
-> DeepSeek 主模型  
-> 规则层风险识别  
-> postprocess / template fallback  
-> 最终患者回复  
-> 家属端事件  
-> 提醒状态 / 熟悉素材 / 聊天记录沉淀

更具体地说，当前闭环由这些层组成：

1. 患者在 `/conversation` 输入文字或语音。
2. `chat_service` 读取患者档案、近期聊天、提醒状态、熟悉素材和风险规则。
3. DeepSeek 作为默认主模型生成候选回复。
4. 规则层和 guard 检查高风险场景，如用药不确定、已故亲人、外出意图、位置困惑。
5. 必要时通过 `postprocess` 或 `template_fallback` 修正，而不是直接放行原始回复。
6. 最终患者回复写入聊天记录。
7. `caregiver_event_service` 根据患者原话触发家属端事件与建议动作。
8. 提醒状态、聊天记录、熟悉素材和测试结果继续沉淀为后续照护依据。

## 3. 已完成模块

- 患者端对话
- DeepSeek 主模型
- mock fallback
- template fallback
- 熟悉素材库
- 回忆陪伴
- 聊天记录
- 提醒完成状态
- 家属端风险摘要
- MiniMax TTS 接口准备
- 对照评估
- 测试结果页
- debug dashboard

## 4. 页面入口清单

| 页面 | 作用 |
|---|---|
| `/app_home` | 首页功能入口，按患者端、家属端、测试调试分组 |
| `/conversation` | 患者端主对话页面 |
| `/conversation?debug=1` | 查看 provider、fallback、context、materials、reminder 状态等调试信息 |
| `/analysis` | 家属端摘要页，显示风险、建议操作、提醒状态和事件列表 |
| `/materials` | 熟悉素材库，管理照片、语音留言、音乐、旧地点、旧事件等 |
| `/reminiscence` | 回忆陪伴页面，按素材类型分组展示 |
| `/chat-history` | 按日期查看聊天记录和可沉淀回忆线索 |
| `/test-results` | 查看 DeepSeek 报告、对照评估报告等 results 文件 |
| `/debug-dashboard` | 查看当前模型状态、最近聊天诊断和测试可见性 |

## 5. API 清单

### Chat

- `POST /chat`
- `GET /chat_logs`

### Materials

- `GET /api/materials/{patient_id}`
- `POST /api/materials/{patient_id}`
- `PUT /api/materials/{patient_id}/{material_id}`
- `DELETE /api/materials/{patient_id}/{material_id}`

### Reminders

- `GET /reminders`
- `POST /reminders`
- `PATCH /reminders/{reminder_id}`
- `GET /api/reminders/{patient_id}`
- `POST /api/reminders/{patient_id}`
- `PUT /api/reminders/{patient_id}/{reminder_id}`
- `POST /api/reminders/{patient_id}/{reminder_id}/confirm`
- `POST /api/reminders/{patient_id}/{reminder_id}/miss`

### TTS

- `POST /api/tts/speak`
- `POST /voice/speak`
- `POST /voice/transcribe`

### Caregiver Summary / Events

- `GET /api/caregiver/{patient_id}/events`
- `GET /api/caregiver/{patient_id}/summary`
- `POST /api/caregiver/{patient_id}/events/{event_id}/resolve`

## 6. 测试脚本清单

- `scripts/test_page_chat_deepseek.py`
- `scripts/test_reminder_status.py`
- `scripts/test_tts_service.py`
- `scripts/evaluate_controlled_llm_comparison.py`
- `scripts/test_deepseek_demo_patient.py`
- `scripts/test_materials_module.py`
- `scripts/test_chat_context_materials.py`
- `scripts/test_chat_history_page.py`
- `scripts/test_reminiscence_page.py`
- `scripts/test_scene_eval_page.py`

## 7. DeepSeek 主聊天验证

当前页面端主聊天已经验证为默认真实使用 DeepSeek，而不是默认 mock。验收依据来自 `scripts/test_page_chat_deepseek.py`，关键结果为：

- `actual_provider=deepseek`
- `model=deepseek-v4-flash`
- `fallback_used=false`

这说明在正常配置和网络条件下，患者端主回复链路由 DeepSeek 承担；只有缺 key、超时、底层请求失败或安全修复需要时，系统才会进入 fallback 路径。

## 8. 提醒闭环如何避免用药幻觉

v0.4 的关键改进之一，是把“我是不是还没吃药？”从普通自然语言问题，转成结构化提醒状态问题处理。当前系统不会让 LLM 自己猜测用药完成情况，而是优先读取 `reminder_status`：

- `confirmed`：回复“今天早上的药已经确认过了……”
- `pending / unknown`：回复“还没有看到确认记录……”
- `missed`：回复“今天的药还没有确认，先别自己乱吃……”

也就是说，用药事实来自 reminder 数据，不来自模型推断。这样可以明显减少用药幻觉风险，并把家属确认动作纳入闭环。

## 9. 对照评估结果

当前最新一次 `results/controlled_llm_comparison_report.md` 的核心结果为：

- `baseline_direct_llm = 5.71/10`
- `care_system = 7.91/10`
- 结论：`PASS`

这说明普通 DeepSeek 直连在部分温和场景下也能聊天，但完整照护系统在以下方面更强：

- 更少用药幻觉
- 更少对已故亲人的直接刺激性纠正
- 更稳地压住外出风险
- 能带入患者档案和熟悉素材
- 能形成家属端事件和后续动作

因此，本系统的价值不只是“有一个模型在回答”，而是“模型 + 规则 + 提醒状态 + 熟悉素材 + 家属反馈”构成了更适合阿尔兹海默症照护的控制型链路。

## 10. 当前不足

- MiniMax TTS 还没有完成真实 key 的端到端验证
- 文件上传仍以 URL/path 为主
- 提醒状态还可以进一步做成每日闭环
- 真实用户测试尚未开展
- 权限、隐私和授权说明仍需加强

## 11. 下一版 v0.5 建议

- MiniMax TTS 真实端到端
- 每日照护闭环
- 家属审核式记忆沉淀
- 真实小样本可用性测试
- 隐私授权说明页

## 12. 导师汇报版摘要

本项目 v0.4 已从“可展示的功能原型”推进到“更强的照护系统原型”。系统以阿尔兹海默症家庭照护为目标场景，采用 DeepSeek 作为默认主模型，并通过规则层、安全 guard、template fallback、熟悉素材库、提醒状态和家属端事件机制，对模型输出进行约束和补强。患者端可进行低刺激陪伴对话，家属端可查看风险摘要、事件记录、提醒完成状态和回忆素材。与普通 DeepSeek 直连相比，当前完整系统在 10 个典型照护场景中的平均得分从 5.71/10 提升到 7.91/10，证明其在安全性、个性化、家属反馈和照护适配性方面更有优势。尤其是在“我是不是还没吃药”这类高风险场景中，系统不再让 LLM 猜测事实，而是直接读取 reminder 状态，减少用药幻觉。当前版本仍属于系统原型，不是医疗系统，不能替代医生和家属，但已经形成了“患者输入 - 模型回复 - 风险控制 - 家属反馈 - 资料沉淀”的基础闭环，为下一步的语音陪伴、每日照护闭环和真实小样本测试奠定了基础。
