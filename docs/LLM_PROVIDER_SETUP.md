# LLM Provider Configuration and Testing Guide

This guide explains how to configure and test different LLM providers for the Alzheimer companion system, including the newly added MiniMax support and DeepSeek V4 models.

## Quick Start

### 1. Copy the example environment file

```bash
cp .env.example .env
```

### 2. Select a provider and add your API key

Choose one of the following options:

#### Option A: Use Mock Provider (No API Key Required)

```bash
# .env
LLM_PROVIDER=mock
```

This uses built-in fallback responses and doesn't require any API keys. Perfect for development and testing.

#### Option B: Use DeepSeek V4

```bash
# .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-flash
```

You can also use `deepseek-v4-pro` for higher quality outputs (with higher costs):

```bash
DEEPSEEK_MODEL=deepseek-v4-pro
```

#### Option C: Use MiniMax

```bash
# .env
LLM_PROVIDER=minimax
MINIMAX_API_KEY=your-minimax-api-key
MINIMAX_BASE_URL=https://api.minimax.io/v1
MINIMAX_MODEL=MiniMax-M2.7
```

#### Option D: Use Zhipu AI

```bash
# .env
LLM_PROVIDER=zhipu
ZHIPU_API_KEY=your-zhipu-api-key
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
ZHIPU_MODEL=glm-4
```

#### Option E: Use OpenAI

```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

### 3. Optional: Configure timeout and output length

```bash
# .env
# Maximum reply length in characters (default: 120)
LLM_MAX_OUTPUT_CHARS=120

# API request timeout in seconds (default: 30)
LLM_TIMEOUT_SECONDS=30
```

### 4. Start the application

```bash
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

Visit `http://localhost:8000/conversation` to test the companion.

## Testing Provider Configuration

### Run the provider configuration tests

```bash
cd /root/alz-memory-assistant
source venv/bin/activate
python scripts/test_llm_providers.py
```

This will verify:
- ✓ DeepSeek V4 configuration (deepseek-v4-flash by default)
- ✓ MiniMax configuration (MiniMax-M2.7 by default)
- ✓ Zhipu, OpenAI, and Mock configurations
- ✓ Provider availability checks
- ✓ Mock fallback behavior
- ✓ Timeout settings

### Expected test output

```
Total: 8/8 tests passed

✓ PASSED: DeepSeek V4
✓ PASSED: MiniMax
✓ PASSED: Zhipu
✓ PASSED: OpenAI
✓ PASSED: Mock
✓ PASSED: Provider Availability
✓ PASSED: Mock Fallback
✓ PASSED: Timeout Config
```

## Testing Individual Providers

### Test with DeepSeek V4

1. Set `.env`:
```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key
```

2. Start the app and try a conversation

3. Check logs for:
```
using real llm: provider=deepseek model=deepseek-v4-flash
```

### Test with MiniMax

1. Set `.env`:
```bash
LLM_PROVIDER=minimax
MINIMAX_API_KEY=your-minimax-api-key
```

2. Start the app and try a conversation

3. Check logs for:
```
using real llm: provider=minimax model=MiniMax-M2.7
```

### Test with Mock (Always Works)

1. Set `.env`:
```bash
LLM_PROVIDER=mock
```

2. Start the app and try any conversation

3. Check logs for:
```
using mock llm
```

The mock provider always returns rule-based responses without requiring an API key.

## Fallback Behavior

The system automatically falls back to mock mode if:

1. **API key is missing**: Set the environment variable for the provider you want to use
2. **Request timeout**: Increase `LLM_TIMEOUT_SECONDS` if requests are timing out
3. **API error**: The system logs the error and uses the mock response instead
4. **Response guard triggered**: If the real model output fails quality checks, mock takes over

Check the logs to see why a fallback occurred:

```
fallback to mock from deepseek: request timeout or error: Timeout
fallback to mock from minimax: response guard rejected real output
```

## Cost Optimization Tips

- Use `deepseek-v4-flash` instead of `deepseek-v4-pro` for lower costs
- Use mock provider for development and testing
- Adjust `LLM_MAX_OUTPUT_CHARS` for shorter responses (uses fewer tokens)
- Monitor usage in your provider's dashboard

## Privacy and Safety

The system implements several safeguards:

1. **Profile minimization**: Only essential profile data is sent to the LLM
2. **Memory summaries**: Long conversation history is compressed into key points
3. **Response guards**: Output is filtered for safety and quality
4. **No logging of API keys**: API keys are never written to logs
5. **Timeout protection**: Requests that take too long automatically fall back to mock

## Troubleshooting

### "API key missing" error

Check that the correct API key is set in `.env`:

```bash
# For DeepSeek
echo $DEEPSEEK_API_KEY  # Should show your API key

# For MiniMax
echo $MINIMAX_API_KEY   # Should show your API key

# For Zhipu
echo $ZHIPU_API_KEY     # Should show your API key
```

### Request timing out

Try increasing the timeout:

```bash
# .env
LLM_TIMEOUT_SECONDS=60
```

### Mock provider always being used

1. Verify your API key is set: `echo $DEEPSEEK_API_KEY`
2. Check that the provider name is correct: `echo $LLM_PROVIDER`
3. Run the test script: `python scripts/test_llm_providers.py`
4. Check the logs for fallback reasons

### Provider returns empty response

1. Check response guard settings in logs
2. Try the mock provider to see if the issue is with your provider
3. Adjust `LLM_MAX_OUTPUT_CHARS` if responses are being truncated

## Environment Variable Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `zhipu` | Provider selection: mock, zhipu, deepseek, minimax, openai |
| `LLM_TIMEOUT_SECONDS` | `30` | API request timeout in seconds |
| `LLM_MAX_OUTPUT_CHARS` | `120` | Maximum reply length in characters |
| `DEEPSEEK_API_KEY` | (none) | DeepSeek API key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | DeepSeek API base URL |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | DeepSeek model (v4-flash or v4-pro) |
| `MINIMAX_API_KEY` | (none) | MiniMax API key |
| `MINIMAX_BASE_URL` | `https://api.minimax.io/v1` | MiniMax API base URL |
| `MINIMAX_MODEL` | `MiniMax-M2.7` | MiniMax model |
| `ZHIPU_API_KEY` | (none) | Zhipu API key |
| `ZHIPU_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4/` | Zhipu API base URL |
| `ZHIPU_MODEL` | `glm-4` | Zhipu model |
| `OPENAI_API_KEY` | (none) | OpenAI API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI API base URL |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model |

## Next Steps

- Try different models and compare outputs
- Adjust output length and timeout based on your needs
- Monitor provider usage and costs
- Set up monitoring and logging in production
