# Conversation Eval Comparison

生成时间：2026-04-27T16:34:27
run_tag: `readmecheck`

## Provider 列表

- `mock`

## Provider 可用性

| provider | available | model | base_url | reason |
| --- | --- | --- | --- | --- |
| mock | yes | mock |  | mock provider is always available |

## 人工评估维度

- 当前输入是否被正确接住
- 是否自然
- 是否没有脚本腔
- 是否没有后台材料泄漏
- 是否符合 Alzheimer 陪伴场景

## Case: `clarification_001`

- case_type: `clarification`
- input_text: `那是谁`
- evaluation_focus: 是否优先澄清上一句；是否没有切新话题；是否短答且自然

### 最近对话上下文

- assistant: 我刚刚说到你女儿小雨在上海工作。

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 我换个说法接你这句。我刚刚提到的是你女儿小雨在上海工作。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |

## Case: `clarification_002`

- case_type: `clarification`
- input_text: `你再说什么`
- evaluation_focus: 是否能重说上一句；是否没有机械复读整段长话；是否避免脚本腔

### 最近对话上下文

- assistant: 我刚刚说到你以前喜欢热汤面。

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 我不绕，接着你这句说。我刚刚提到的是你以前喜欢热汤面。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
