# Conversation Eval Score Template

生成时间：2026-04-27T20:18:24
run_tag: `care_refactor_check`

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
- model_reply: 我换个说法接你这句。刚才那句说的是你女儿小雨在上海工作。

### 人工评分

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 总体推荐度（1-5） | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |  |

## Case: `clarification_002`

- input_text: `你再说什么`
- case_type: `clarification`
- evaluation_focus: 是否能重说上一句；是否没有机械复读整段长话；是否避免脚本腔

### Provider 回复

#### `mock`

- actual_provider: `mock`
- fallback_used: `no`
- model_reply: 刚才那句说的是你以前喜欢热汤面。

### 人工评分

| provider | 是否接住当前输入 | 是否自然 | 是否没有脚本腔 | 是否没有后台材料泄漏 | 是否适合 Alzheimer 陪伴场景 | 总体推荐度（1-5） | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mock |  |  |  |  |  |  |  |
