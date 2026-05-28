# LLM Provider Layer Upgrade - Implementation Summary

## Overview

成功完成了FastAPI项目的LLM接入层升级。项目现在支持**多provider切换**（DeepSeek V4、MiniMax、Zhipu、OpenAI、Mock），具有**最小侵入式架构**、**健壮的fallback机制**、和**患者隐私保护**。

## Modified Files

### 1. `app/services/llm_service.py` ✓ 核心升级

**主要改动：**

- ✓ 添加MiniMax支持到 `DEFAULT_PROVIDER_BASE_URLS` 和 `DEFAULT_PROVIDER_MODELS`
- ✓ 更新DeepSeek默认模型从 `deepseek-chat` → `deepseek-v4-flash`
- ✓ 在 `_normalize_provider_name()` 中添加minimax验证
- ✓ 在 `_resolve_provider_config()` 中添加minimax分支
- ✓ 添加 `LLM_TIMEOUT_SECONDS` 和 `LLM_MAX_OUTPUT_CHARS` 环境变量支持
- ✓ 在 `_generate_real_reply_result()` 中添加timeout处理和异常捕获

**代码位置：**
```python
DEFAULT_PROVIDER_BASE_URLS = {
    "zhipu": "https://open.bigmodel.cn/api/paas/v4/",
    "deepseek": "https://api.deepseek.com/v1",
    "minimax": "https://api.minimax.io/v1",  # NEW
    "openai": "https://api.openai.com/v1",
}

DEFAULT_PROVIDER_MODELS = {
    "zhipu": "glm-4",
    "deepseek": "deepseek-v4-flash",  # UPDATED
    "minimax": "MiniMax-M2.7",  # NEW
    "openai": "gpt-4o-mini",
}

# 环境变量支持 (NEW)
MAX_REPLY_CHARS = int(os.getenv("LLM_MAX_OUTPUT_CHARS", "120"))
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
```

### 2. `.env.example` ✓ 配置模板

**主要改动：**

- ✓ 添加 `LLM_TIMEOUT_SECONDS` 和 `LLM_MAX_OUTPUT_CHARS` 配置
- ✓ 添加MiniMax完整配置块
- ✓ 更新DeepSeek模型为 `deepseek-v4-flash`

**新配置项：**
```dotenv
# LLM timeout and output length settings
LLM_TIMEOUT_SECONDS=30
LLM_MAX_OUTPUT_CHARS=120

# MiniMax OpenAI-compatible configuration
MINIMAX_API_KEY=
MINIMAX_BASE_URL=https://api.minimax.io/v1
MINIMAX_MODEL=MiniMax-M2.7
```

### 3. `README.md` ✓ 文档更新

**主要改动：**

- ✓ 更新provider列表，添加minimax
- ✓ 添加DeepSeek V4配置说明（v4-flash和v4-pro）
- ✓ 添加MiniMax配置说明
- ✓ 添加"Output and Timeout Configuration"部分
- ✓ 更新"Fallback Behavior"说明，包含timeout

### 4. `scripts/test_llm_providers.py` ✓ 新测试脚本

**功能：**

- ✓ 验证所有provider的正确配置
- ✓ 检查provider可用性
- ✓ 测试mock fallback机制
- ✓ 验证超时和输出长度设置

**测试项目：**
```
✓ PASSED: DeepSeek V4
✓ PASSED: MiniMax
✓ PASSED: Zhipu
✓ PASSED: OpenAI
✓ PASSED: Mock
✓ PASSED: Provider Availability
✓ PASSED: Mock Fallback
✓ PASSED: Timeout Config
```

### 5. `docs/LLM_PROVIDER_SETUP.md` ✓ 新增完整指南

**包含内容：**

- ✓ 快速开始指南
- ✓ 各provider详细配置说明
- ✓ 测试步骤和期望输出
- ✓ Fallback行为解释
- ✓ 成本优化建议
- ✓ 隐私和安全说明
- ✓ 故障排查指南
- ✓ 环境变量参考表

## Architecture - 最小侵入式设计

### 保留的现有功能（无改动）

✓ `chat_service.py` - 对话主链路保留
✓ `conversation_style_engine.py` - 状态检测和安全策略保留
✓ `memory_context_service.py` - 内存管理保留
✓ `profile_service.py` - 档案管理保留
✓ Response guard系统 - 输出质量控制保留
✓ Mock fallback基础 - 只添加了provider支持

### Provider Abstraction

现有架构已经是provider-agnostic的，新增功能只是扩展：

```python
class ProviderSwitchingLLMService:
    """Use the configured provider when possible, otherwise fall back to mock."""
    
    def generate_reply_result(self, conversation: LLMConversationInput) -> LLMReplyResult:
        config = _resolve_provider_config(self._provider_override)
        # 1. 配置确定 (现有 + 新增minimax)
        # 2. 检查可用性 (现有逻辑)
        # 3. 调用API (新增timeout支持)
        # 4. Response guard (现有逻辑)
        # 5. Fallback (现有 + 改进)
```

## Configuration Support

### 环境变量层级 (Priority Order)

1. **提供者特定变量**（最高优先级）
   ```
   DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
   MINIMAX_API_KEY, MINIMAX_BASE_URL, MINIMAX_MODEL
   ```

2. **通用OpenAI兼容变量**（后备）
   ```
   OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
   ```

3. **默认值**（最低优先级）
   ```
   DEFAULT_PROVIDER_BASE_URLS, DEFAULT_PROVIDER_MODELS
   ```

### .env 配置示例

#### DeepSeek V4 (Flash - 低成本)
```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key
# 其他配置使用默认值
```

#### DeepSeek V4 (Pro - 高质量)
```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key
DEEPSEEK_MODEL=deepseek-v4-pro
```

#### MiniMax
```bash
LLM_PROVIDER=minimax
MINIMAX_API_KEY=your-key
# 其他配置使用默认值
```

#### Mock (开发/测试，无需API key)
```bash
LLM_PROVIDER=mock
```

## Privacy & Safety Implementation

### 1. Profile最小化（已有）

```python
def _profile_text(profile: UserProfile) -> str:
    """Turn profile into short factual lines without script-like phrasing."""
    # 只发送必要的字段摘要，限制5行
    # 清理了脚本化措辞，只保留事实信息
    return "\n".join(lines[:5]) if lines else "暂无资料。"
```

### 2. Memory摘要（已有）

```python
def _memory_summary_text(summary: str) -> str:
    """Keep only a few factual long-term summary lines."""
    # 从长期记忆提取关键点
    # 限制4个要点，每个36字符
    return "\n".join(f"- {line}" for line in compact_lines)
```

### 3. 最近对话精简（已有）

```python
def _history_text(logs: Sequence[ChatLog]) -> str:
    """Convert only a few recent turns into a compact context block."""
    # 只发送最近4句对话
    recent_logs = list(logs[-4:])
```

### 4. 输出长度限制（新增）

```python
LLM_MAX_OUTPUT_CHARS = int(os.getenv("LLM_MAX_OUTPUT_CHARS", "120"))
# 默认120字符，可配置
# 自动截断过长回复
```

### 5. Response Guard（已有）

多层安全检查：
- Meta回复检测 - 过滤系统语言
- 脚本化回复检测 - 过滤模板化语言
- 字段泄露检测 - 过滤后台信息
- 相似度检测 - 避免重复回复
- 相关性检测 - 确保回答匹配用户输入

## Fallback Mechanism - 完整链路

```
用户输入
    ↓
[Mock参考回复] ← 作为安全基准
    ↓
选择Provider ← LLM_PROVIDER环境变量
    ↓
检查API Key ← 缺失→fallback
    ↓
调用API ← 超时(30s)→fallback
         ← 错误→fallback
    ↓
Response Guard ← 质量检查失败→fallback
    ↓
相关性Guard ← 不相关→fallback
    ↓
返回最佳回复（真实或mock）
    ↓
记录日志（provider、model、是否fallback、耗时）
```

## Testing - 完整验证

### 运行测试

```bash
cd /root/alz-memory-assistant
source venv/bin/activate
python scripts/test_llm_providers.py
```

### 测试覆盖

| 测试 | 验证项 | 结果 |
|------|--------|------|
| DeepSeek V4 | 模型为deepseek-v4-flash | ✓ |
| MiniMax | 模型为MiniMax-M2.7 | ✓ |
| Zhipu | 模型为glm-4 | ✓ |
| OpenAI | 模型为gpt-4o-mini | ✓ |
| Mock | 模型为mock | ✓ |
| Provider Availability | 缺少API key时报告不可用 | ✓ |
| Mock Fallback | 没有API key时自动fallback | ✓ |
| Timeout Config | 读取LLM_TIMEOUT_SECONDS | ✓ |

## Cost Optimization

### 1. 智能Provider选择

- 开发/测试 → `mock`（无成本）
- 生产低成本 → `deepseek-v4-flash`
- 生产高质量 → `deepseek-v4-pro`或`minimax`

### 2. 输出优化

```
LLM_MAX_OUTPUT_CHARS=120  # 默认值，足够1-3句中文
减少字符 → 减少token → 降低成本
```

### 3. 请求优化（已有）

- 最近只发4句对话（不是全部）
- Profile只发前5行摘要
- Long-term memory只发4个关键点

### 估算成本

使用DeepSeek V4 Flash：
- 平均请求：300 tokens输入 + 150 tokens输出
- 成本：约 ¥0.001 每个请求
- 300次对话/天：约 ¥0.3/天

## Deployment Checklist

- [ ] 复制 `.env.example` 到 `.env`
- [ ] 选择一个provider（推荐mock进行测试）
- [ ] 设置相应的API key
- [ ] 运行 `python scripts/test_llm_providers.py` 验证配置
- [ ] 启动应用：`python -m uvicorn app.main:app --reload`
- [ ] 访问 `http://localhost:8000/conversation` 测试
- [ ] 查看日志验证使用的provider和model

## Migration Guide - 从旧配置迁移

### 旧配置（仍然有效）

```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat  # 旧模型
```

### 升级到新配置

```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-flash  # 新模型，性能更好
```

### 完全向后兼容

✓ 旧的 `deepseek-chat` 仍然可以工作
✓ 旧的 `OPENAI_*` 后备变量仍然有效
✓ 没有breaking changes

## File Structure Changes

```
/root/alz-memory-assistant/
├── app/
│   └── services/
│       └── llm_service.py                 # ← 改动: +minimax, +timeout支持
├── docs/
│   ├── alzheimer_mode_notes.md
│   └── LLM_PROVIDER_SETUP.md             # ← 新增: 完整指南
├── scripts/
│   └── test_llm_providers.py             # ← 新增: 测试脚本
├── .env.example                           # ← 改动: +minimax, +timeout配置
└── README.md                              # ← 改动: +minimax, 更新DeepSeek说明
```

## Success Criteria - 全部达成 ✓

- ✓ 保留现有chat主链路 - 无改动
- ✓ 保留conversation_style_engine - 无改动
- ✓ 不推倒重写llm_service - 只是扩展
- ✓ 支持DeepSeek V4 - deepseek-v4-flash/pro
- ✓ 支持MiniMax - MiniMax-M2.7及自定义
- ✓ 通过.env切换provider - 5个provider支持
- ✓ API key从环境变量读取 - 零硬编码
- ✓ 患者隐私最小化传输 - 已有基础 + 新增长度限制
- ✓ 超时、重试、fallback - timeout新增，重试已有
- ✓ README说明 - 完整的LLM_PROVIDER_SETUP.md + README更新
- ✓ 测试脚本 - 8/8测试通过

## Next Steps

1. **本地测试**
   ```bash
   python scripts/test_llm_providers.py
   python -m uvicorn app.main:app --reload
   ```

2. **配置生产环境**
   - 选择provider（推荐DeepSeek V4 Flash）
   - 获取API key
   - 配置.env文件

3. **监控和优化**
   - 查看日志中的fallback情况
   - 根据需要调整LLM_TIMEOUT_SECONDS
   - 监控token使用和成本

4. **未来增强**
   - 添加其他provider（Claude、Llama等）
   - 实现provider-specific优化（如Claude的system prompt）
   - 添加metrics和cost tracking
