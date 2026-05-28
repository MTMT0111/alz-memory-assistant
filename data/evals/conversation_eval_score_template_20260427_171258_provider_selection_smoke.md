# Conversation Eval Score Template

生成时间：2026-04-27T17:12:58
run_tag: `provider_selection_smoke`

## 评分维度

- 当前输入是否被正确接住
- 是否自然
- 是否没有脚本腔
- 是否没有后台材料泄漏
- 是否符合 Alzheimer 陪伴场景
- 总体推荐度（1-5）

说明：建议每项用 1-5 或简短文字记录，最后根据总体推荐度和备注选择主力 provider。

## Case: `clarification_001`

- input_text: `那是谁`
- case_type: `clarification`
- evaluation_focus: 是否优先澄清上一句；是否没有切新话题；是否短答且自然

### Provider 回复

#### `mock`

- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 刚才那句说的是你女儿小雨在上海工作。

#### `zhipu`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 这回我说得再直接一点。我刚刚提到的是你女儿小雨在上海工作。

#### `deepseek`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 我不绕，接着你这句说。我刚刚说的是你女儿小雨在上海工作。

#### `openai`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 我换个说法接你这句。刚才那句说的是你女儿小雨在上海工作。

### 人工评分

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 总体推荐度（1-5） | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |  |

## Case: `clarification_002`

- input_text: `你再说什么`
- case_type: `clarification`
- evaluation_focus: 是否能重说上一句；是否没有机械复读整段长话；是否避免脚本腔

### Provider 回复

#### `mock`

- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 刚才那句说的是你以前喜欢热汤面。

#### `zhipu`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 这回我说得再直接一点。刚才那句说的是你以前喜欢热汤面。

#### `deepseek`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 我刚刚提到的是你以前喜欢热汤面。

#### `openai`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 刚才那句说的是你以前喜欢热汤面。

### 人工评分

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 总体推荐度（1-5） | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |  |

## Case: `need_request_001`

- input_text: `我饿了`
- case_type: `need_request`
- evaluation_focus: 是否优先回应当前需求；是否没有被旧记忆锚点拖走；是否给出自然的下一步承接

### Provider 回复

#### `mock`

- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 先让自己垫一口吧。要不要先找点你平时顺口的东西？要是想到喜欢热汤，我们就先从那个开始。

#### `zhipu`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 那先顾着肚子。想吃点热的，还是先喝口水？要是想到喜欢热汤，我们就先从那个开始。

#### `deepseek`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 那先吃点东西更要紧。想吃点热的，还是先喝口水？要是想到喜欢热汤，我们就先从那个开始。

#### `openai`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 先让自己垫一口吧。要不要先找点你平时顺口的东西？要是想到喜欢热汤，我们就先从那个开始。

### 人工评分

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 总体推荐度（1-5） | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |  |

## Case: `need_request_002`

- input_text: `我累了`
- case_type: `need_request`
- evaluation_focus: 是否先照顾眼前状态；是否不跳去回忆引导；是否语气温和简短

### Provider 回复

#### `mock`

- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 那先歇一歇。先休息一下，等舒服点我们再聊。等缓过来，再说熟悉的人和事也不迟。

#### `zhipu`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 那先歇一歇。要不要先靠一会儿，我们等会儿再接着说。等缓过来，再说熟悉的人和事也不迟。

#### `deepseek`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 先坐稳一点，缓口气。要不要先靠一会儿，我们等会儿再接着说。等缓过来，再说熟悉的人和事也不迟。

#### `openai`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 那先让自己松一松。要不要先靠一会儿，我们等会儿再接着说。等缓过来，再说熟悉的人和事也不迟。

### 人工评分

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 总体推荐度（1-5） | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |  |

## Case: `memory_question_001`

- input_text: `我是谁`
- case_type: `memory_question`
- evaluation_focus: 是否直接回答身份问题；是否不绕弯子；是否符合 Alzheimer 场景的温和表达

### Provider 回复

#### `mock`

- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 大家常叫你王阿姨。要不就从这个称呼带出来的人说起。

#### `zhipu`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 我这边记着别人叫你王阿姨。一听到这个称呼，脑子里最先冒出来的是谁？

#### `deepseek`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 我这边记着别人叫你王阿姨。要不就从这个称呼带出来的人说起。

#### `openai`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 在我这里记着的称呼是王阿姨。这个称呼一出来，你先想到的是谁？

### 人工评分

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 总体推荐度（1-5） | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |  |

## Case: `memory_question_002`

- input_text: `我女儿是谁`
- case_type: `memory_question`
- evaluation_focus: 是否直接回答家人关系；是否没有字段腔；是否不把后台资料整段念出来

### Provider 回复

#### `mock`

- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 我记得女儿小雨在上海工作。这个人平时最常陪你做什么？

#### `zhipu`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 我这边记着女儿小雨在上海工作。这个人平时最常陪你做什么？

#### `deepseek`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 在我这里留着的线索是女儿小雨在上海工作。要不就从这个人说起。

#### `openai`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 在我这里留着的线索是女儿小雨在上海工作。这个人平时最常陪你做什么？

### 人工评分

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 总体推荐度（1-5） | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |  |

## Case: `short_input_001`

- input_text: `嗯`
- case_type: `short_input`
- evaluation_focus: 是否能自然接住短输入；是否在合适时才轻引导；是否没有模板腔

### Provider 回复

#### `mock`

- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 女儿小雨在上海工作这件事，我们可以接着说。

#### `zhipu`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 女儿小雨在上海工作这件事，我们可以接着说。

#### `deepseek`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 女儿小雨在上海工作这件事，我们可以接着说。

#### `openai`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 女儿小雨在上海工作，是你很熟的人。

### 人工评分

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 总体推荐度（1-5） | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |  |

## Case: `emotional_001`

- input_text: `你在说什么`
- case_type: `emotional`
- evaluation_focus: 是否先接住不满或困惑；是否能回到清楚短答；是否不继续脚本式引导

### Provider 回复

#### `mock`

- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 刚才那句说的是我刚刚提到你以前喜欢下班后喝热汤。

#### `zhipu`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 刚才那句说的是我刚刚提到你以前喜欢下班后喝热汤。

#### `deepseek`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 我刚刚说的是我刚刚提到你以前喜欢下班后喝热汤。

#### `openai`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 我刚刚提到的是我刚刚提到你以前喜欢下班后喝热汤。

### 人工评分

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 总体推荐度（1-5） | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |  |

## Case: `emotional_003`

- input_text: `我是不是忘了什么`
- case_type: `emotional`
- evaluation_focus: 是否避免测试感；是否不过度安抚；是否给出温和承接

### Provider 回复

#### `mock`

- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 我刚刚说的是刚刚那句。

#### `zhipu`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 刚才那句说的是刚刚那句。

#### `deepseek`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 我刚刚说的是刚刚那句。

#### `openai`

- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 我刚刚说的是刚刚那句。

### 人工评分

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 总体推荐度（1-5） | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |  |
