# Conversation Eval Comparison

生成时间：2026-04-20T23:10:55

## Provider 列表

- `mock`
- `zhipu`
- `deepseek`
- `openai`

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
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 我换个说法接你这句。我刚刚提到的是你女儿小雨在上海工作。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 刚才那句说的是你女儿小雨在上海工作。

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 这回我说得再直接一点。刚才那句说的是你女儿小雨在上海工作。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 刚才那句说的是你女儿小雨在上海工作。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

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
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 我刚刚提到的是你以前喜欢热汤面。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 我刚刚提到的是你以前喜欢热汤面。

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 这回我说得再直接一点。刚才那句说的是你以前喜欢热汤面。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 我换个说法接你这句。刚才那句说的是你以前喜欢热汤面。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

## Case: `clarification_003`

- case_type: `clarification`
- input_text: `什么意思`
- evaluation_focus: 是否围绕上一句做短解释；是否不过度延展；是否保持自然对话感

### 最近对话上下文

- assistant: 我刚刚提到你以前在南京商场上班。

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 刚才那句说的是我刚刚提到你以前在南京商场上班。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 刚才那句说的是我刚刚提到你以前在南京商场上班。

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 我刚刚提到的是我刚刚提到你以前在南京商场上班。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 我刚刚说的是我刚刚提到你以前在南京商场上班。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

## Case: `need_request_001`

- case_type: `need_request`
- input_text: `我饿了`
- evaluation_focus: 是否优先回应当前需求；是否没有被旧记忆锚点拖走；是否给出自然的下一步承接

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 先让自己垫一口吧。要不要先找点你平时顺口的东西？要是想到喜欢热汤，我们就先从那个开始。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 先让自己垫一口吧。你想先吃口软一点的，还是先喝点热的？要是想到喜欢热汤，我们就先从那个开始。

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 那先顾着肚子。要不要先找点你平时顺口的东西？要是想到喜欢热汤，我们就先从那个开始。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 那先吃点东西更要紧。你想先吃口软一点的，还是先喝点热的？要是想到喜欢热汤，我们就先从那个开始。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

## Case: `need_request_002`

- case_type: `need_request`
- input_text: `我累了`
- evaluation_focus: 是否先照顾眼前状态；是否不跳去回忆引导；是否语气温和简短

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 先坐稳一点，缓口气。你想先坐一坐，还是先闭眼歇会儿？等缓过来，再说熟悉的人和事也不迟。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 那先让自己松一松。你想先坐一坐，还是先闭眼歇会儿？等缓过来，再说熟悉的人和事也不迟。

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 先坐稳一点，缓口气。要不要先靠一会儿，我们等会儿再接着说。等缓过来，再说熟悉的人和事也不迟。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 那先歇一歇。要不要先靠一会儿，我们等会儿再接着说。等缓过来，再说熟悉的人和事也不迟。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

## Case: `need_request_003`

- case_type: `need_request`
- input_text: `我不舒服`
- evaluation_focus: 是否优先回应不适；是否避免空泛安抚；是否没有脚本化提问

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 那先让自己缓一缓。哪里不得劲，你只说一点点也行。先把这会儿安顿好，别的等会儿再说。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 那先顾着舒服一点。是想先坐一会儿，还是先叫身边的人来看看？先把这会儿安顿好，别的等会儿再说。

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 那先让自己缓一缓。哪里不得劲，你只说一点点也行。先把这会儿安顿好，别的等会儿再说。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 那先让自己缓一缓。哪里不得劲，你只说一点点也行。先把这会儿安顿好，别的等会儿再说。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

## Case: `memory_question_001`

- case_type: `memory_question`
- input_text: `我是谁`
- evaluation_focus: 是否直接回答身份问题；是否不绕弯子；是否符合 Alzheimer 场景的温和表达

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 在我这里记着的称呼是王阿姨。这个称呼一出来，你先想到的是谁？

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 我这边记着别人叫你王阿姨。这个称呼一出来，你先想到的是谁？

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 在我这里记着的称呼是王阿姨。要不就从这个称呼带出来的人说起。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 在我这里记着的称呼是王阿姨。要不就从这个称呼带出来的人说起。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

## Case: `memory_question_002`

- case_type: `memory_question`
- input_text: `我女儿是谁`
- evaluation_focus: 是否直接回答家人关系；是否没有字段腔；是否不把后台资料整段念出来

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 我记得女儿小雨在上海工作。这个人平时最常陪你做什么？

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 我记得女儿小雨在上海工作。你先想到的，是和这个人在一起的哪件小事？

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 在我这里留着的线索是女儿小雨在上海工作。要不就从这个人说起。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 我记得女儿小雨在上海工作。你先想到的，是和这个人在一起的哪件小事？

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

## Case: `memory_question_003`

- case_type: `memory_question`
- input_text: `我以前做什么的`
- evaluation_focus: 是否能利用 profile 回答；是否表达自然；是否不过度文学化

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 刚才那句说的是刚刚那句。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 我刚刚提到的是刚刚那句。

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 刚才那句说的是刚刚那句。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 刚才那句说的是刚刚那句。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

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
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 女儿小雨在上海工作这件事，我们可以接着说。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 女儿小雨在上海工作，是你很熟的人。

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 女儿小雨在上海工作这件事，我们可以接着说。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 女儿小雨在上海工作这件事，我们可以接着说。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

## Case: `short_input_002`

- case_type: `short_input`
- input_text: `哦`
- evaluation_focus: 是否不空泛；是否顺着已有话题继续；是否不过度解释系统行为

### 最近对话上下文

- assistant: 你以前常去夫子庙那边走走。

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

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

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 女儿小雨在上海工作这件事，我们可以接着说。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 女儿小雨在上海工作这件事，我们可以接着说。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

## Case: `short_input_003`

- case_type: `short_input`
- input_text: `不知道`
- evaluation_focus: 是否在不施压的前提下轻引导；是否没有测试感；是否保持简短

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 女儿小雨在上海工作这件事，我们可以接着说。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 我刚刚想到的是女儿小雨在上海工作。

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 我刚刚想到的是女儿小雨在上海工作。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 女儿小雨在上海工作，是你很熟的人。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

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
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

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
- model_reply: 我刚刚提到的是我刚刚提到你以前喜欢下班后喝热汤。

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 刚才那句说的是我刚刚提到你以前喜欢下班后喝热汤。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 刚才那句说的是我刚刚提到你以前喜欢下班后喝热汤。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

## Case: `emotional_002`

- case_type: `emotional`
- input_text: `你是不是弄错了`
- evaluation_focus: 是否不争辩；是否不直接纠错用户；是否自然修正或缓和承接

### 最近对话上下文

- assistant: 我刚刚提到的是你儿子建国。

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 你要是嫌我刚刚说得虚了，我们就换成眼前这会儿的话。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 你要是嫌我刚刚说得虚了，我们就换成眼前这会儿的话。

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 你要是嫌我刚刚说得虚了，我们就换成眼前这会儿的话。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 你现在最想听清哪一句，我就接那一句。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |

## Case: `emotional_003`

- case_type: `emotional`
- input_text: `我是不是忘了什么`
- evaluation_focus: 是否避免测试感；是否不过度安抚；是否给出温和承接

### Provider 对比

| provider | actual_provider | fallback_used | model | notes |
| --- | --- | --- | --- | --- |
| mock | mock | no | mock |  |
| zhipu | mock | yes | glm-4 |  |
| deepseek | mock | yes | deepseek-chat |  |
| openai | mock | yes | gpt-4o-mini |  |

#### `mock` 回复

- requested_provider: `mock`
- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 刚才那句说的是刚刚那句。

#### `zhipu` 回复

- requested_provider: `zhipu`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `zhipu API key missing`
- model_reply: 刚才那句说的是刚刚那句。

#### `deepseek` 回复

- requested_provider: `deepseek`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `deepseek API key missing`
- model_reply: 我刚刚提到的是刚刚那句。

#### `openai` 回复

- requested_provider: `openai`
- actual_provider: `mock`
- fallback_used: `yes`
- fallback_reason: `openai API key missing`
- model_reply: 我刚刚提到的是刚刚那句。

### 人工评分模板

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
| deepseek |  |  |  |  |  |  |
| openai |  |  |  |  |  |  |
