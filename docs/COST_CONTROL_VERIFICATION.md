# LLM 成本控制验证指南

> **关键要点**: 系统通过"对话策略检测"和"重复问题识别"来实现成本控制，而不是对每句话都调用LLM。

## 成本控制机制

### 1. 对话策略自动检测

系统使用 `conversation_style_engine` 检测每条用户消息的意图，并选择相应策略：

| 检测的情况 | 对应策略 | LLM 调用 | 成本 |
|-----------|--------|--------|------|
| **重复问题** | `repeat_soft_response` | ❌ 不调用 | **低** |
| **澄清请求** (比如"我该吃什么药？") | `clarification_repair` | ❌ 不调用 | **低** |
| **当前需求** (水、药、舒服...) | `current_need_response` | ❌ 不调用 | **低** |
| **投诉语气** (为什么只有一句话?) | `complaint_repair` | ❌ 不调用 | **低** |
| **直接记忆查询** (我是谁? 我女儿叫什么?) | 从 Profile 读取 | ❌ 不调用 | **低** |
| **情感支持需求** | `normal_chat` | ✅ 调用 | **标准** |
| **一般聊天** | `normal_chat` | ✅ 调用 | **标准** |
| **回忆引导** | `normal_chat` | ✅ 调用 | **标准** |

### 2. 三层成本优化

```
用户消息
    ↓
[检测对话策略] ← conversation_style_engine
    ↓
    ├─ 优化场景？ → 使用 Mock/Template 模板回复 ✅ 低成本
    │  ├─ 重复问题   → 复述上次回复
    │  ├─ 澄清/需求  → 检查 Profile/Reminder
    │  └─ 投诉       → 修复响应策略
    │
    └─ 普通场景？ → 调用真实 LLM ✅ 标准成本
       ├─ 情感支持  → 需要个性化
       ├─ 聊天      → 自然对话
       └─ 回忆引导  → 需要上下文理解
```

### 3. 重复问题优化

当用户重复提问时，系统会：

```python
# 检测重复 (从最近3条消息中)
"我是谁？"        ← 第1次: 调用 LLM 获得回复
"你刚才说什么？"  ← 检测到重复: 使用 soft_repeat_response 策略
"我是谁？"        ← 第2次: 直接返回上次的答案
```

**成本节省**：减少 30-50% 的 LLM 调用（取决于用户重复问题的频率）

## 如何验证成本控制

### 方法 1：运行测试脚本

```bash
# 测试对话场景的优化策略
python scripts/test_chat_llm_routing.py

# 测试真实聊天流程
python scripts/test_real_chat_flow.py
```

**预期结果**:
- ✓ 8/8 对话场景正确识别
- ✓ 重复问题自动优化
- ✓ 直接记忆查询使用 Profile
- ✓ Provider Fallback 正常工作
- ✓ LLMReplyResult 包含所有诊断信息

### 方法 2：查看应用日志

启用调试模式运行应用：

```bash
# 设置调试日志
export LLM_DEBUG=1
python app/main.py
```

在聊天时查看日志输出：

| 日志消息 | 含义 | 成本 |
|---------|------|------|
| `using mock llm` | 使用优化策略，不调用真实LLM | **低** ✅ |
| `fallback to mock from X: reason` | 本应调用X但失败，回退到Mock | **低** ✅ |
| `using real llm: provider=X model=Y` | 调用真实LLM | **标准** |
| `fallback to mock from X` | 真实LLM超时或失败 | **低** ✅ |

### 方法 3：成本分析

根据对话内容估算成本：

```
5条消息的示例对话：
1. "你好" → 一般聊天 → 调用 LLM (1次)
2. "我是谁？" → 记忆查询 → 从 Profile 读取 (0次)
3. "我是谁？" → 重复问题 → 使用缓存 (0次)
4. "我女儿是谁？" → 直接记忆 → 从 Profile 读取 (0次)
5. "天气真好" → 一般聊天 → 调用 LLM (1次)

总计: 2/5 = 40% 的消息调用 LLM，60% 使用优化策略
成本对比: 标准 5次调用 → 优化后 2次调用 → 节省 60%
```

## 调试模式：验证策略检测

### 查看对话策略分析

在 `app/services/chat_service.py` 中临时添加日志：

```python
# 在 build_chat_diagnostics() 之前添加
state = conversation_style_engine.detect_user_state(user_message, recent_logs)
strategy = conversation_style_engine.decide_strategy(state)
print(f"DEBUG: Message='{user_message}', Strategy={strategy}, Input={state.input_kind}")
```

**示例输出**:
```
DEBUG: Message='我是谁？', Strategy=clarification_repair, Input=memory_question
DEBUG: Message='我很害怕', Strategy=normal_chat, Input=general
DEBUG: Message='你刚才说什么？', Strategy=repeat_soft_response, Input=general
```

### 验证 Profile 和 Reminder 查询

```python
# 在 analysis_service.py 中查看
profile_response = profile_service.get_profile_response(user_message, profile)
reminder_response = care_service.check_reminders(profile)

# 如果返回了响应，说明优化策略工作了
if profile_response or reminder_response:
    print("✓ 使用了 Profile/Reminder 优化")
```

## 成本配置参数

### 超时和输出限制

```bash
# 防止超长回复导致成本增加
LLM_TIMEOUT_SECONDS=30      # 超过30秒自动回退到Mock
LLM_MAX_OUTPUT_CHARS=120    # 限制最长120字符的回复

# 这些参数确保：
# 1. 不会因为网络问题浪费费用
# 2. 回复长度合理，避免超长内容
# 3. 超时自动使用Mock fallback
```

### Provider 配置

```bash
# 使用成本最低的 Provider
LLM_PROVIDER=deepseek                           # 推荐: 成本最低
DEEPSEEK_MODEL=deepseek-v4-flash                # 快速/便宜 (推荐)
# DEEPSEEK_MODEL=deepseek-v4-pro               # 高质量(贵)

# 替代方案
MINIMAX_API_KEY=xxx
MINIMAX_MODEL=MiniMax-M2.7

# OpenAI (最贵)
OPENAI_API_KEY=xxx
OPENAI_MODEL=gpt-4o-mini
```

## 预期效果

### 原始实现（每句话都调用LLM）
```
100条消息 = 100次 LLM 调用 = 标准成本
```

### 优化后（成本控制激活）
```
100条消息中：
  • 重复问题（20%）→ 使用 soft_repeat_response
  • 澄清请求（15%）→ 检查 Profile/Reminder
  • 当前需求（10%）→ 直接模板回复
  • 投诉修复（5%）→ 使用 repair 策略
  ─────────────────────────
  • 优化覆盖率: 50%
  • 实际 LLM 调用: 50次
  • 成本节省: 50%
```

## 故障排除

### 问题：所有消息都调用了LLM

**检查**:
1. 验证 `conversation_style_engine.py` 是否正常工作
   ```bash
   python -c "from app.services.conversation_style_engine import detect_user_state; print(detect_user_state('我是谁？', []))"
   ```

2. 查看日志是否显示 `using mock llm`
   ```bash
   grep "using mock llm" app/logs/*.log
   ```

3. 检查是否所有Provider都配置了API密钥
   ```bash
   echo $DEEPSEEK_API_KEY
   echo $MINIMAX_API_KEY
   ```

### 问题：重复问题仍然调用LLM

**检查**:
1. 确认最近对话历史有相似消息
   ```python
   # 需要最近3条消息中有类似的
   recent_logs = chat_log_db.get_recent(3)
   similar = detect_user_state(message, recent_logs)
   ```

2. 查看 `_detect_repeat_question()` 的相似度阈值
   ```bash
   grep "similarity_threshold" app/services/conversation_style_engine.py
   ```

### 问题：Profile 查询没有返回答案

**检查**:
1. 确认 Profile 中有相关字段
   ```bash
   python -c "from app.services.profile_service import get_profile; p = get_profile(1); print(p.__dict__)"
   ```

2. 验证 Memory 问题检测
   ```bash
   grep "MEMORY_QUESTION_HINTS" app/services/conversation_style_engine.py
   ```

## 成本监控

### 设置成本告警

```python
# 在 analytics 中添加
llm_call_count = db.query(ChatLog).filter(ChatLog.used_real_llm == True).count()
optimization_rate = (total_messages - llm_call_count) / total_messages * 100

if optimization_rate < 30:  # 优化率低于30%
    alert(f"Warning: Low optimization rate: {optimization_rate}%")
```

### 导出成本报告

```bash
# 查看每日LLM调用统计
python -c "
from app.database import SessionLocal
from app.models.chat_log import ChatLog
from datetime import datetime, timedelta

db = SessionLocal()
today = datetime.now().date()
calls = db.query(ChatLog).filter(
    ChatLog.timestamp >= today,
    ChatLog.used_real_llm == True
).count()
print(f'LLM calls today: {calls}')
"
```

## 下一步优化

1. **AI 请求合并**: 将连续相关的消息合并为单次 LLM 调用
2. **缓存优化**: 缓存相同问题的答案（如"我叫什么？"）
3. **批量优化**: 针对特定用户的对话模式进行优化
4. **Provider 选择**: 根据问题类型选择最经济的 Provider

---

**最后更新**: 2026-05-13
