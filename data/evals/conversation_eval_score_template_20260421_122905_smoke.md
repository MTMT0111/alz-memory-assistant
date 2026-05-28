# Conversation Eval Score Template

生成时间：2026-04-21T12:29:05
run_tag: `smoke`

## 评分维度

- 当前输入是否被正确接住
- 是否自然
- 是否没有脚本腔
- 是否没有后台材料泄漏
- 是否符合 Alzheimer 陪伴场景

## Case: `clarification_001`

- input_text: `那是谁`
- case_type: `clarification`
- evaluation_focus: 是否优先澄清上一句；是否没有切新话题；是否短答且自然

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `clarification_002`

- input_text: `你再说什么`
- case_type: `clarification`
- evaluation_focus: 是否能重说上一句；是否没有机械复读整段长话；是否避免脚本腔

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `need_request_001`

- input_text: `我饿了`
- case_type: `need_request`
- evaluation_focus: 是否优先回应当前需求；是否没有被旧记忆锚点拖走；是否给出自然的下一步承接

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `need_request_003`

- input_text: `我不舒服`
- case_type: `need_request`
- evaluation_focus: 是否优先回应不适；是否避免空泛安抚；是否没有脚本化提问

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `memory_question_001`

- input_text: `我是谁`
- case_type: `memory_question`
- evaluation_focus: 是否直接回答身份问题；是否不绕弯子；是否符合 Alzheimer 场景的温和表达

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `memory_question_002`

- input_text: `我女儿是谁`
- case_type: `memory_question`
- evaluation_focus: 是否直接回答家人关系；是否没有字段腔；是否不把后台资料整段念出来

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `memory_question_003`

- input_text: `我以前做什么的`
- case_type: `memory_question`
- evaluation_focus: 是否能利用 profile 回答；是否表达自然；是否不过度文学化

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `short_input_001`

- input_text: `嗯`
- case_type: `short_input`
- evaluation_focus: 是否能自然接住短输入；是否在合适时才轻引导；是否没有模板腔

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `short_input_003`

- input_text: `不知道`
- case_type: `short_input`
- evaluation_focus: 是否在不施压的前提下轻引导；是否没有测试感；是否保持简短

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |

## Case: `emotional_001`

- input_text: `你在说什么`
- case_type: `emotional`
- evaluation_focus: 是否先接住不满或困惑；是否能回到清楚短答；是否不继续脚本式引导

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |
| zhipu |  |  |  |  |  |  |
