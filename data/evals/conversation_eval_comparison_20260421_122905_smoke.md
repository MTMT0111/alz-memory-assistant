# Conversation Eval Comparison

生成时间：2026-04-21T12:29:05
run_tag: `smoke`

## Provider 列表

- `mock`
- `zhipu`

## Provider 可用性

| provider | available | model | base_url | reason |
| --- | --- | --- | --- | --- |
| mock | yes | mock |  | mock provider is always available |
| zhipu | no | glm-4 | https://open.bigmodel.cn/api/paas/v4/ | zhipu API key missing |

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
| zhipu | mock | yes | glm-4 |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 我不绕，接着你这句说。我刚刚提到的是你女儿小雨在上海工作。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 我换个说法接你这句。刚才那句说的是你女儿小雨在上海工作。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

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
| zhipu | mock | yes | glm-4 |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 刚才那句说的是你以前喜欢热汤面。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 刚才那句说的是你以前喜欢热汤面。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `need_request_001`

- case_type: `need_request`
- input_text: `我饿了`
- evaluation_focus: 是否优先回应当前需求；是否没有被旧记忆锚点拖走；是否给出自然的下一步承接

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 那先吃点东西更要紧。你想先吃口软一点的，还是先喝点热的？要是想到喜欢热汤，我们就先从那个开始。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 先让自己垫一口吧。你想先吃口软一点的，还是先喝点热的？要是想到喜欢热汤，我们就先从那个开始。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `need_request_003`

- case_type: `need_request`
- input_text: `我不舒服`
- evaluation_focus: 是否优先回应不适；是否避免空泛安抚；是否没有脚本化提问

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 那先让自己缓一缓。你想先缓一缓，还是先喝点水？先把这会儿安顿好，别的等会儿再说。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 那先顾着舒服一点。是想先坐一会儿，还是先叫身边的人来看看？先把这会儿安顿好，别的等会儿再说。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `memory_question_001`

- case_type: `memory_question`
- input_text: `我是谁`
- evaluation_focus: 是否直接回答身份问题；是否不绕弯子；是否符合 Alzheimer 场景的温和表达

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 我这边记着别人叫你王阿姨。一听到这个称呼，脑子里最先冒出来的是谁？

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 在我这里记着的称呼是王阿姨。一听到这个称呼，脑子里最先冒出来的是谁？

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `memory_question_002`

- case_type: `memory_question`
- input_text: `我女儿是谁`
- evaluation_focus: 是否直接回答家人关系；是否没有字段腔；是否不把后台资料整段念出来

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 在我这里留着的线索是女儿小雨在上海工作。这个人平时最常陪你做什么？

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 我这边记着女儿小雨在上海工作。要不就从这个人说起。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `memory_question_003`

- case_type: `memory_question`
- input_text: `我以前做什么的`
- evaluation_focus: 是否能利用 profile 回答；是否表达自然；是否不过度文学化

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 我刚刚提到的是刚刚那句。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 刚才那句说的是刚刚那句。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `short_input_001`

- case_type: `short_input`
- input_text: `嗯`
- evaluation_focus: 是否能自然接住短输入；是否在合适时才轻引导；是否没有模板腔

### 最近对话上下文

- assistant: 你刚刚提到过小雨，我在想你们以前一起吃饭的时候。

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 我刚刚想到的是女儿小雨在上海工作。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 女儿小雨在上海工作，是你很熟的人。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `short_input_003`

- case_type: `short_input`
- input_text: `不知道`
- evaluation_focus: 是否在不施压的前提下轻引导；是否没有测试感；是否保持简短

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 我刚刚想到的是女儿小雨在上海工作。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 我刚刚想到的是女儿小雨在上海工作。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `emotional_001`

- case_type: `emotional`
- input_text: `你在说什么`
- evaluation_focus: 是否先接住不满或困惑；是否能回到清楚短答；是否不继续脚本式引导

### 最近对话上下文

- assistant: 我刚刚提到你以前喜欢下班后喝热汤。

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 刚才那句说的是我刚刚提到你以前喜欢下班后喝热汤。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 我刚刚说的是我刚刚提到你以前喜欢下班后喝热汤。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
