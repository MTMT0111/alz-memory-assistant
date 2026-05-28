# 快速参考卡 - LLM Provider配置

## 立即开始 (2分钟)

```bash
cd /root/alz-memory-assistant
source venv/bin/activate
cp .env.example .env
python scripts/test_llm_providers.py  # 验证配置
python -m uvicorn app.main:app --reload  # 启动应用
```

## 3种配置方式

### 方式1: Mock (推荐开发测试)
```bash
# .env
LLM_PROVIDER=mock
```
✓ 无需API key  
✓ 完全免费  
✓ 基于规则生成回复  

### 方式2: DeepSeek V4 Flash (推荐生产)
```bash
# .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key
# 其他配置使用默认值
```
✓ 成本低: ¥0.001/请求  
✓ 质量好  
✓ 速度快  

### 方式3: MiniMax (新增支持)
```bash
# .env
LLM_PROVIDER=minimax
MINIMAX_API_KEY=your-minimax-api-key
```
✓ 中文优化  
✓ 价格合理  
✓ 性能稳定  

## 可选配置

```bash
# .env
# API超时 (秒)
LLM_TIMEOUT_SECONDS=30

# 最大回复长度 (字符)
LLM_MAX_OUTPUT_CHARS=120

# 更换模型
DEEPSEEK_MODEL=deepseek-v4-pro  # 代替flash
```

## 测试脚本

```bash
python scripts/test_llm_providers.py

# 预期输出
✓ PASSED: DeepSeek V4
✓ PASSED: MiniMax
✓ PASSED: Zhipu
✓ PASSED: OpenAI
✓ PASSED: Mock
✓ PASSED: Provider Availability
✓ PASSED: Mock Fallback
✓ PASSED: Timeout Config

Total: 8/8 tests passed
```

## 查看日志

### 确认使用了哪个provider
```
使用real llm: provider=deepseek model=deepseek-v4-flash  # 真实API
使用mock llm  # Mock provider
```

### 检查是否触发fallback
```
fallback to mock from deepseek: request timeout or error
fallback to mock from minimax: response guard rejected real output
```

## 全部Provider参考

| Provider | 默认模型 | 成本 | 速度 | 质量 |
|----------|--------|------|------|------|
| Mock | mock | ✓免费 | ✓快 | ◐中 |
| DeepSeek Flash | deepseek-v4-flash | ¥0.001/请求 | ✓快 | ◐中 |
| DeepSeek Pro | deepseek-v4-pro | 更贵 | ✓快 | ✓好 |
| MiniMax | MiniMax-M2.7 | ¥0.002/请求 | ◐中 | ✓好 |
| Zhipu | glm-4 | 更贵 | ◐中 | ✓好 |
| OpenAI | gpt-4o-mini | 最贵 | ◐中 | ✓最好 |

## 常见问题

### Q: 怎样从一个provider切换到另一个?
A: 只需修改.env中的LLM_PROVIDER变量,重启应用即可。

### Q: 没有API key能工作吗?
A: 可以,使用mock provider(LLM_PROVIDER=mock)。

### Q: 如何降低成本?
A: 使用deepseek-v4-flash或调整LLM_MAX_OUTPUT_CHARS。

### Q: 如果API超时怎么办?
A: 系统自动fallback到mock provider,用户不会感受到错误。

### Q: 能用其他模型吗?
A: 可以,修改provider对应的*_MODEL环境变量。

## 环境变量完整列表

必需:
- `LLM_PROVIDER` = mock/zhipu/deepseek/minimax/openai

可选(带默认值):
- `LLM_TIMEOUT_SECONDS` = 30
- `LLM_MAX_OUTPUT_CHARS` = 120

DeepSeek专用:
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL` = https://api.deepseek.com/v1
- `DEEPSEEK_MODEL` = deepseek-v4-flash

MiniMax专用:
- `MINIMAX_API_KEY`
- `MINIMAX_BASE_URL` = https://api.minimax.io/v1
- `MINIMAX_MODEL` = MiniMax-M2.7

Zhipu专用:
- `ZHIPU_API_KEY`
- `ZHIPU_BASE_URL` = https://open.bigmodel.cn/api/paas/v4/
- `ZHIPU_MODEL` = glm-4

OpenAI专用:
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL` = https://api.openai.com/v1
- `OPENAI_MODEL` = gpt-4o-mini

## 文件位置

- 核心代码: `app/services/llm_service.py`
- 测试脚本: `scripts/test_llm_providers.py`
- 完整指南: `docs/LLM_PROVIDER_SETUP.md`
- 实现文档: `IMPLEMENTATION_SUMMARY.md`
- 此快速卡: `QUICK_REFERENCE.md`

## 获取API密钥

- **DeepSeek**: https://platform.deepseek.com
- **MiniMax**: https://www.minimax.io  
- **Zhipu**: https://open.bigmodel.cn
- **OpenAI**: https://platform.openai.com

## 架构要点

✓ **最小侵入式** - 只修改了llm_service.py  
✓ **100%兼容** - 旧配置仍然工作  
✓ **隐私优先** - Profile和memory最小化传输  
✓ **安全可靠** - Mock永远可用作fallback  
✓ **配置灵活** - 全部通过环境变量  

---

更多信息请查看:
- 📖 `docs/LLM_PROVIDER_SETUP.md` - 完整指南
- 📋 `IMPLEMENTATION_SUMMARY.md` - 实现细节
- 📋 `UPGRADE_CHECKLIST.md` - 验证清单
