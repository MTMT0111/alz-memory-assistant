# 功能导航与测试说明

> 当前版本基于 FastAPI + Jinja/HTML/CSS/JS + SQLite。没有创建 Android 项目，也没有推倒重做 UI。

## 1. 页面入口在哪里

| 分类 | 页面 | 用途 |
|---|---|---|
| 首页目录 | `/app` 或 `/app_home` | 查看患者端、家属端、资料管理、测试调试和后续扩展入口。 |
| 患者端 | `/conversation` | 李奶奶陪伴对话主页面。 |
| 患者端调试 | `/conversation?debug=1` | 聊天页显示最近一次 provider、model、fallback、状态识别和家属事件。 |
| 熟悉素材 | `/materials` | 维护家人照片 URL、语音留言路径、熟悉音乐、旧地点、旧事件和敏感回忆提示。 |
| 聊天记录 | `/chat-history` | 按日期查看聊天记录、风险/回忆标签和可沉淀素材候选。 |
| 回忆陪伴 | `/reminiscence` | 以家人、老歌、旧地点、旧事件分组查看 familiar materials。 |
| 家属端 | `/analysis` | 今日照护摘要、风险提醒、建议家属操作、事件列表和素材配置状态。 |
| 档案 | `/profile-editor` | 维护患者资料、家庭关系、经历、偏好和照护备注。 |
| 模型状态 | `/debug-dashboard` | 查看当前 provider/model/base_url、API key 是否配置、最近聊天诊断和常用测试命令。 |
| 场景测试 | `/llm-eval` | 选择 deepseek/minimax/mock 跑场景，查看 raw/final/template 结果。 |
| 测试结果 | `/test-results` | 查看 `results/` 下的 DeepSeek、真实 API、provider 对比报告。 |

## 2. 如何确认 DeepSeek 真正在页面端被使用

1. 打开 `/conversation?debug=1`。
2. 发送一句测试，例如“小雨什么时候回来？”。
3. 看顶部或调试卡片：
   - `requested_provider` 应为 `deepseek`。
   - `actual_provider` 为 `deepseek` 表示真实 API 回复通过。
   - `actual_provider` 为 `template_fallback` 表示真实或高风险链路被安全模板接管。
   - `actual_provider` 为 `mock` 时必须有明确 `fallback_reason`，例如缺 key、超时、client 不可用。

也可以打开 `/debug-dashboard`，查看“当前 provider”“当前 model”和“最近一次聊天 actual_provider”。

## 3. 如何查看 raw_llm_reply 和 final_assistant_reply

打开 `/llm-eval`：

1. Provider 默认选择 `deepseek`。
2. 选择一个场景，例如“询问旧经历 / 回忆引导”。
3. 点击运行。
4. 页面会分三块显示：
   - `raw_llm_reply`：DeepSeek / MiniMax 原始回复。
   - `safe_template_reply` 或 `postprocess_reply`：安全模板或后处理回复。
   - `final_assistant_reply`：最终给患者看的回复。

同一区域也会显示 `requested_provider`、`actual_provider`、`model`、`fallback_reason`、`postprocess_used`、`template_used`、`template_name`、`detected_state`、`strategy` 和 `response_time_ms`。

聊天页 `/conversation?debug=1` 还会显示 `context_items_count`、`memory_used`、`materials_used`、`material_match_reason`、`history_turns_used`，用于确认熟悉素材和压缩上下文是否进入本轮聊天。

## 4. 如何查看测试结果

打开 `/test-results` 查看这些文件是否存在、更新时间、PASS/FAIL、平均质量分、fallback 次数和 postprocess 次数：

- `results/deepseek_demo_patient_report.md/json`
- `results/real_api_patient_dialogue_report.md/json`
- `results/llm_provider_comparison.md/json`

命令行可重新跑：

```bash
venv/bin/python scripts/test_deepseek_demo_patient.py --provider deepseek
```

## 5. 如何维护熟悉素材

打开 `/materials`：

1. 选择素材类型：家人照片、语音留言、熟悉音乐、旧地点、旧事件、日常物品、敏感记忆。
2. 填标题、描述、关联人物、URL/path、缩略图、语音文字、歌手、使用场景、相关时间、标签、安全提示。
3. 敏感素材勾选“是否敏感”，例如已故老伴相关话题。
4. 保存后会出现在素材卡片列表，也会影响患者端 prompt 摘要。

当前先支持 URL/path 录入，不强行做文件上传。语音留言和 MiniMax 朗读仍是后续接入模块。

## 6. 聊天上下文与熟悉素材如何参与 LLM 回复

每次 `/chat` 会把上下文压缩后交给 DeepSeek：

- 当前患者 profile 和家属信息。
- 今日提醒/作息摘要。
- 最近 4 轮原文。
- 更早聊天 summary。
- 当前风险规则，例如用药、外出、已故亲人敏感话题。
- 本轮命中的 familiar materials 摘要。

匹配规则：

- “小雨/女儿/回来”匹配家人照片或语音留言。
- “老歌/音乐/听歌”匹配熟悉音乐。
- “以前/年轻/做衣服/服装厂”匹配旧事件。
- 焦虑表达会优先推荐语音留言或熟悉音乐。
- 敏感素材只在明确触发时进入安全提示，不主动刺激患者。

## 7. 如何查看家属端事件

打开 `/analysis`：

- “今日照护摘要”显示当天风险和互动概况。
- “风险提醒”显示高/中风险事件。
- “建议家属操作”列出下一步建议。
- 事件列表显示 `severity`、事件类型、患者原话、建议动作、是否处理、创建时间。
- “熟悉素材配置状态”显示照片、语音、音乐、旧地点、旧事件和敏感素材是否已配置。

可以在患者端测试这些句子触发事件：

- “我想出去走走。”
- “这里是哪里？我要回家。”
- “我是不是还没吃药？”
- “老王怎么还没回来？”

## 8. 聊天记录和回忆陪伴页面

- `/chat-history`：查看最近聊天记录，按日期分组，自动标记普通聊天、重复提问、焦虑、用药不确定、回忆内容和风险事件。
- `/reminiscence`：按家人、老歌、旧地点、旧事件、敏感内容提醒分组查看 familiar materials。
- `/materials`：真正维护素材内容。

## 9. mock 什么时候才会出现

mock 只应该出现在这些情况：

- 手动选择 provider=`mock`。
- API key 缺失。
- provider client 不可用。
- 上游 API 超时或失败。
- 非高风险场景低层 provider 失败，需要保证页面继续可用。

高风险场景，例如已故亲人敏感话题，被 guard 拒绝后应显示 `actual_provider=template_fallback`，不应静默降级为普通 mock。

## 10. 如果页面显示 mock 怎么排查

1. 打开 `/debug-dashboard`，确认当前 provider 是 `deepseek`，model 是 `deepseek-v4-flash`。
2. 确认 `.env` 中设置了 `LLM_PROVIDER=deepseek`。
3. 确认 `DEEPSEEK_API_KEY` 已配置，但不要把 key 写进代码或文档。
4. 看 `fallback_reason`：缺 key、client unavailable、timeout、request error 分别对应不同问题。
5. 在 `/llm-eval` 选择 DeepSeek 跑一个普通场景，确认 requested/actual provider。
6. 如果只有高风险场景显示 `template_fallback`，这是安全兜底，不是错误。

## 11. 后续如何接 MiniMax TTS

当前 `.env.example` 已预留：

```dotenv
MINIMAX_TTS_MODEL=speech-2.8-turbo
MINIMAX_TTS_VOICE_ID=Chinese_female_young
```

下一步建议：

1. 保留浏览器 `speechSynthesis` fallback，不破坏现有语音按钮。
2. 给 `/voice/speak` 或新的 TTS service 增加 MiniMax 分支。
3. 在 `/device-settings` 显示 TTS provider、voice id 和 fallback 状态。
4. 在 `/materials` 的语音留言中继续只保存 URL/path，不把真实音频上传复杂化。
