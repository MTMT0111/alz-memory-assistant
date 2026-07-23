# 🚀 5分钟快速开始 - 成本控制验证

## 1️⃣ 安装和配置 (2分钟)

```bash
# 进入项目目录
cd /root/alz-memory-assistant
source venv/bin/activate

# 复制环境文件
cp .env.example .env

# 编辑.env选择提供商 (选择一个)
# 选项A: 最低成本
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key

# 选项B: 成本平衡
LLM_PROVIDER=minimax
MINIMAX_API_KEY=your-key

# 选项C: 高质量
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key

# 或测试回退机制
LLM_PROVIDER=mock
```

## 2️⃣ 验证测试 (2分钟)

```bash
# 测试所有提供商配置
python scripts/test_llm_providers.py
# 期望: 8/8 tests passed ✅

# 测试对话成本控制
python scripts/test_chat_llm_routing.py
# 期望: 10/10 tests passed ✅

# 测试真实聊天流程
python scripts/test_real_chat_flow.py
# 期望: 所有验证通过 ✅
```

## 3️⃣ 启动应用 (1分钟)

```bash
# 启动Fapython app/main.pystAPI服务器


# 打开浏览器
# http://localhost:8000/conversation
```

## 📊 成本控制一览

### 什么时候会调用LLM? ✅
- 情感支持 (我很害怕)
- 一般聊天 (天气真好)
- 复杂对话 (讲个故事)

### 什么时候不调用LLM? 🚫 (成本节省)
- 重复问题 (我是谁? × 2)
- 澄清请求 (我该吃什么药?)
- 当前需求 (我该喝水了吗?)
- 投诉修复 (为什么只有一句话?)
- 直接记忆查询 (我女儿叫什么?)

### 成本对比

```
原始: 100条消息 = 100次LLM调用 = 基础成本
优化: 100条消息 = 50次LLM调用 = 基础成本 × 0.5
节省: 50% ✨
```

## 🔍 验证成本控制

### 快速检查命令

```bash
# 1. 运行完整测试套件
python scripts/test_chat_llm_routing.py | grep "Total"
# 期望: Total: 10/10 tests passed

# 2. 检查日志中的LLM调用
python app/main.py 2>&1 | grep "using.*llm"
# 期望: 混合的 "using mock llm" 和 "using real llm"

# 3. 模拟真实对话
python scripts/test_real_chat_flow.py | grep "Cost Control"
# 期望: 显示50%+的优化覆盖率
```

### 查看诊断信息

```python
# 在app/services/llm_service.py中查看日志
# 每条消息返回的诊断信息:

result = service.generate_reply_result(conversation)
print(f"实际提供商: {result.actual_provider}")
print(f"使用了回退: {result.fallback_used}")
print(f"回退原因: {result.fallback_reason}")
print(f"守卫触发: {result.guard_triggered}")
```

## 📁 关键文件位置

| 文件 | 用途 |
|------|------|
| `app/services/llm_service.py` | LLM路由和成本控制 |
| `scripts/test_chat_llm_routing.py` | 对话场景测试 |
| `scripts/test_real_chat_flow.py` | 真实流程验证 |
| `docs/COST_CONTROL_VERIFICATION.md` | 详细指南 |
| `COST_CONTROL_SUMMARY.md` | 项目总结 |

## ⚙️ 配置参考

### 高级配置

```bash
# 响应超时 (防止卡住)
LLM_TIMEOUT_SECONDS=30    # 超过30秒自动回退

# 输出限制 (控制成本)
LLM_MAX_OUTPUT_CHARS=120  # 最多120字符回复

# 选择最便宜的模型
DEEPSEEK_MODEL=deepseek-v4-flash  # 推荐

# 或选择高质量
DEEPSEEK_MODEL=deepseek-v4-pro    # 更贵但更好
```

## ❓ 常见问题

### Q: 如何验证成本控制是否工作?
```bash
python scripts/test_chat_llm_routing.py
# 查看是否有 "10/10 tests passed"
```

### Q: 如何切换提供商?
```bash
# 编辑.env文件
LLM_PROVIDER=deepseek  # 或其他: minimax, zhipu, openai, mock
DEEPSEEK_API_KEY=your-key
```

### Q: 如果API密钥缺失会怎样?
```
自动回退到Mock → 使用本地模板 → 无成本 ✅
```

### Q: 支持哪些对话场景?
```
优化: 重复问题, 澄清, 需求, 投诉, 记忆查询
允许: 情感支持, 聊天, 回忆引导
```

## 📞 故障排除

### 测试失败?
```bash
# 1. 检查Python版本
python --version  # 需要3.11+

# 2. 检查依赖
pip install -r requirements.txt

# 3. 检查环境变量
cat .env | grep LLM

# 4. 查看完整日志
python scripts/test_chat_llm_routing.py 2>&1 | head -50
```

### 成本控制没有工作?
```bash
# 1. 检查conversation_style_engine
python -c "from app.services.conversation_style_engine import *; print('OK')"

# 2. 运行真实流程测试
python scripts/test_real_chat_flow.py

# 3. 查看详细指南
cat docs/COST_CONTROL_VERIFICATION.md | grep "故障排除"
```

## 🎯 下一步

1. ✅ 运行测试验证功能
2. 📖 阅读 [docs/COST_CONTROL_VERIFICATION.md](docs/COST_CONTROL_VERIFICATION.md)
3. 🚀 配置合适的提供商
4. 💻 启动应用
5. 📊 监控成本指标

## 📚 完整文档

- [COST_CONTROL_SUMMARY.md](COST_CONTROL_SUMMARY.md) - 项目总结
- [docs/COST_CONTROL_VERIFICATION.md](docs/COST_CONTROL_VERIFICATION.md) - 详细验证
- [README.md#cost-control](README.md) - 概览
- [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md) - 完整清单

---

**时间**: ~5分钟  
**难度**: ⭐ 很容易  
**结果**: ✅ 100% 验证通过  

**现在就试试**: `python scripts/test_chat_llm_routing.py` 🚀
