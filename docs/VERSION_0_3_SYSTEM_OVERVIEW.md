# VERSION 0.3 SYSTEM OVERVIEW

## 1. 版本名称

**v0.3 DeepSeek 主模型 + 熟悉素材 + 回忆陪伴原型**

本版本基于 FastAPI + Jinja/HTML/CSS/JS + SQLite，以阿尔兹海默症家庭陪伴与照护辅助为核心场景。当前重点不是做“通用聊天网站”，而是形成一个可聊天、可观察、可维护素材、可触发家属端事件的原型系统。

## 2. 当前核心能力

1. **DeepSeek 作为默认主聊天模型**
   - `/conversation` 和 `/chat` 默认走 `deepseek`
   - 默认模型为 `deepseek-v4-flash`
   - debug 模式可查看 `requested_provider`、`actual_provider`、`model`、`fallback_reason`

2. **高风险场景的安全回复链路**
   - 用药不确定、反复问家人、位置困惑、想独自外出、已故亲人等场景优先走规则层判断
   - 真实模型输出被 guard 拒绝时，优先使用 `template_fallback`
   - `mock` 只作为 provider 失败或手动调试时的后备路径

3. **熟悉素材库**
   - 支持家人照片、语音留言、熟悉音乐、旧地点、旧事件、日常物品、敏感记忆
   - 支持增删改查、筛选、搜索和敏感标记
   - 当前以 URL/path 方式录入，不依赖复杂上传链路

4. **回忆陪伴与上下文增强**
   - 聊天时会带入患者 profile、家属信息、提醒摘要、最近几轮对话、回忆摘要和熟悉素材摘要
   - 对“老歌”“小雨”“服装厂”“以前”等话题可命中素材并进入 prompt
   - 敏感素材不会主动进入普通回忆引导

5. **家属端事件与摘要**
   - 患者端对话可触发家属事件
   - `/analysis` 提供今日照护摘要、风险提醒、建议操作、素材配置状态和事件列表
   - 支持对事件做 resolved 标记

6. **调试、场景测试和结果查看**
   - `/conversation?debug=1`：看最近一次聊天 provider/fallback/context diagnostics
   - `/llm-eval`：按场景测试 DeepSeek / MiniMax / Mock
   - `/debug-dashboard`：查看当前模型状态和最近一次聊天诊断
   - `/test-results`：查看 `results/` 下的测试报告文件

## 3. 页面入口清单

| 页面 | 用途 |
|---|---|
| `/app` / `/app_home` | 首页功能导航，分患者端、家属端、测试调试 |
| `/conversation` | 患者端陪伴聊天主页面 |
| `/conversation?debug=1` | 聊天页调试模式，显示 provider/fallback/context 诊断 |
| `/materials` | 熟悉素材库，维护照片、语音、音乐、旧地点、旧事件等 |
| `/reminiscence` | 回忆陪伴页面，按素材类型分组展示 |
| `/chat-history` | 最近聊天记录与回忆摘要候选 |
| `/analysis` | 家属端分析页，含摘要、风险提醒、建议操作、事件、素材状态 |
| `/profile-editor` | 患者资料编辑 |
| `/memory-notes` | 记忆与照护相关笔记入口 |
| `/debug-dashboard` | 模型状态面板和最近聊天诊断 |
| `/test-results` | 查看生成的测试报告和结果摘要 |
| `/llm-eval` | 场景评测页，支持 DeepSeek / MiniMax / Mock |
| `/device-settings` | 设备与语音设置，保留浏览器朗读与 MiniMax TTS 待接入说明 |
| `/location-safety` | 定位安全相关占位页 |
| `/care-portal` | 家属入口页 |
| `/login` | 登录页原型 |

## 4. API 清单

### 页面相关数据 API

| API | 说明 |
|---|---|
| `GET /profile` | 获取当前患者资料 |
| `GET /app-summary` | 获取首页/总览数据摘要 |
| `GET /chat_logs` | 获取聊天记录 |
| `GET /reminders` | 获取提醒列表 |
| `POST /reminders` | 新建提醒 |
| `GET /event_logs` | 获取事件日志 |
| `POST /event_logs` | 新建事件日志 |
| `GET /caregivers` | 获取家属列表 |
| `POST /caregivers` | 新建家属 |
| `POST /save_profile` | 保存患者资料 |

### 熟悉素材 API

| API | 说明 |
|---|---|
| `GET /api/materials/{patient_id}` | 获取患者熟悉素材列表 |
| `POST /api/materials/{patient_id}` | 新增熟悉素材 |
| `PUT /api/materials/{patient_id}/{material_id}` | 更新熟悉素材 |
| `DELETE /api/materials/{patient_id}/{material_id}` | 删除熟悉素材 |

### 家属端事件 API

| API | 说明 |
|---|---|
| `GET /api/caregiver/{patient_id}/events` | 获取家属事件列表 |
| `GET /api/caregiver/{patient_id}/summary` | 获取家属端摘要 |
| `POST /api/caregiver/{patient_id}/events/{event_id}/resolve` | 标记事件已处理 |

### 聊天与调试 API

| API | 说明 |
|---|---|
| `POST /chat` | 患者端聊天主接口 |
| `GET /api/debug/llm-status` | 当前 provider/model/base_url/fallback 状态 |
| `GET /api/debug/last-chat` | 最近一次聊天 diagnostics |
| `GET /api/debug/test-results` | 测试结果摘要 |

### 语音与评测 API

| API | 说明 |
|---|---|
| `POST /voice/transcribe` | 语音转文字入口 |
| `POST /voice/speak` | 朗读入口，当前保留浏览器 fallback |
| `GET /llm_eval/scenarios` | 获取场景测试清单 |
| `POST /llm_eval/run` | 运行预设场景测试 |
| `POST /llm_eval/custom` | 运行自定义场景测试 |

## 5. 测试脚本清单

### 本轮直接相关脚本

| 脚本 | 用途 |
|---|---|
| `scripts/seed_demo_patient.py` | 初始化 Demo 患者与基础资料 |
| `scripts/test_page_chat_deepseek.py` | 验证页面聊天默认真实走 DeepSeek |
| `scripts/test_materials_module.py` | 验证熟悉素材 seed 与 CRUD |
| `scripts/test_chat_context_materials.py` | 验证材料命中后进入聊天 diagnostics |
| `scripts/test_chat_history_page.py` | 验证 `/chat-history` 返回 200 |
| `scripts/test_reminiscence_page.py` | 验证 `/reminiscence` 返回 200 |
| `scripts/test_scene_eval_page.py` | 验证场景评测页 diagnostics 与安全 fallback |
| `scripts/test_deepseek_demo_patient.py` | 跑 Demo 患者 10 轮 DeepSeek 对话报告 |

### 现有扩展脚本

| 脚本 | 用途 |
|---|---|
| `scripts/test_llm_providers.py` | 多 provider 基础能力与 fallback 验证 |
| `scripts/test_chat_llm_routing.py` | 聊天路由和 fallback 路径验证 |
| `scripts/test_real_chat_flow.py` | 真实聊天流联调验证 |
| `scripts/test_real_api_patient_dialogue.py` | 真实 API 患者多轮对话评测 |

## 6. DeepSeek 主聊天验证结果

### 页面链路验证

`scripts/test_page_chat_deepseek.py` 的目标是验证页面聊天不是默认 mock，而是默认使用 DeepSeek 主模型。当前验收标准为：

- `actual_provider=deepseek`
- `model=deepseek-v4-flash`
- `fallback_used=false`

本轮已通过该验证，说明 `/conversation` 对应的 `/chat` 主链路在正常情况下使用真实 DeepSeek 回复。

### Demo 患者多轮测试结果

根据当前 `results/deepseek_demo_patient_report.md`：

- 总对话轮数：10
- 平均质量分：9.80 / 10
- Fallback 次数：4
- Postprocess 次数：4
- 家属事件总数：8
- 整体结论：`PASS`

这里的 `fallback` 主要不是普通 mock 兜底，而是高风险场景或 guard 修复导致的 `template_fallback`。这符合当前系统“真实模型优先、安全模板兜底”的设计目标。

## 7. 熟悉素材如何进入上下文

聊天由 [chat_service.py](/root/alz-memory-assistant/app/services/chat_service.py) 负责拼接上下文。当前每轮聊天会压缩并组合这些信息：

1. 患者 profile 摘要
2. 家属信息
3. 今日提醒/作息摘要
4. 最近 4 轮原始对话
5. 更早对话的 summary
6. 当前风险规则摘要
7. 本轮命中的熟悉素材摘要

熟悉素材由 [familiar_material_service.py](/root/alz-memory-assistant/app/services/familiar_material_service.py) 做轻量匹配和摘要：

- “小雨 / 女儿 / 回来”优先命中家人照片、语音留言
- “老歌 / 音乐 / 听歌”优先命中熟悉音乐
- “以前 / 年轻 / 服装厂 / 做衣服”优先命中旧事件
- 焦虑表达可联动语音留言和熟悉音乐

debug 模式下可在 `/conversation?debug=1` 看到：

- `materials_used`
- `material_match_reason`
- `context_items_count`
- `history_turns_used`
- `memory_used`

敏感素材如“已故老伴”不会主动进入普通回忆 prompt，只在用户明确触发相关话题时作为安全规则参考。

## 8. 家属端事件如何触发

家属事件由 [caregiver_event_service.py](/root/alz-memory-assistant/app/services/caregiver_event_service.py) 按规则从患者原话中检测，再由 [chat_service.py](/root/alz-memory-assistant/app/services/chat_service.py) 在每轮对话后写入。

当前主要触发类型包括：

- `repeated_question`
- `medication_uncertainty`
- `disorientation`
- `wandering_intent`
- `anxiety`
- `sensitive_deceased_spouse_topic`
- `person_recognition`
- `date_time_confusion`
- `suspicion_or_delusion`

典型触发示例：

- “小雨什么时候回来？”连续多次：触发重复提问
- “我是不是还没吃药？”：触发用药不确定
- “这里是哪里？我要回家。”：触发位置困惑
- “我想出去走走。”：触发外出意图
- “我有点害怕。”：触发焦虑
- “老王怎么还没回来？”：触发已故亲人敏感话题

每个事件会带出：

- `severity`
- `event_type`
- `source_message`
- `assistant_reply`
- `suggested_action`
- `tags`
- `created_at`
- `resolved`

这些内容最终在 `/analysis` 和相关 caregiver API 中可见。

## 9. 当前不足

1. **素材上传仍是轻量占位**
   - 目前主要靠 URL/path 录入，尚未做完整文件上传和媒体管理

2. **回忆素材联动仍偏规则化**
   - 目前命中依赖关键词和轻量摘要，还没有更强的向量检索或更细粒度记忆召回

3. **聊天历史沉淀能力还比较初级**
   - `/chat-history` 已能标记回忆候选，但还没有一键转正式素材的完整闭环

4. **语音能力仍以浏览器 fallback 为主**
   - MiniMax TTS 只保留了配置和页面入口，尚未完成正式接入

5. **页面仍属于原型级照护工具**
   - 信息结构已更清楚，但还没有进入更完整的权限、登录、多人家庭协作和生产级状态

6. **真实模型质量仍需持续回归**
   - DeepSeek 主链路已稳定，但高风险场景仍需要继续用固定脚本和真实报告做回归验证

## 10. 下一版建议

1. **把回忆素材闭环做完整**
   - 从 `/chat-history` 一键沉淀为 `/materials` 素材草稿
   - 家属审核后再进入可用素材库

2. **补齐媒体能力**
   - 为照片、音频、音乐链接增加更清楚的预览区
   - 后续再引入轻量文件上传，不必一开始就做复杂云存储

3. **增强素材召回策略**
   - 在关键词规则之外，增加更稳定的 recall 机制
   - 继续严格区分普通熟悉素材与敏感素材

4. **继续强化高风险评测**
   - 增加固定 Alzheimer 场景集，持续验证 `template_fallback` 是否优先于普通 mock
   - 把高风险结果在 `/test-results` 中做更直观汇总

5. **完善家属端协作**
   - 增加事件处理状态、备注、跟进人、处理时间
   - 支持家属补充“今日已确认用药/已电话联系/已陪同外出”等反馈

6. **推进语音陪伴**
   - 保留浏览器朗读 fallback
   - 视资源情况接入 MiniMax TTS，让家属留言和回忆陪伴更自然

