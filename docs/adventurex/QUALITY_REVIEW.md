# QUALITY REVIEW

## Review 1：事实审查

### 已确认事实
- 当前最可信版本为 **v0.5**。
- 多患者、DeepSeek 主链路、患者对话、caregiver workspace、materials、photo timeline、memory candidate、reminiscence、consent、TTS fallback、PWA scaffolding 均有代码证据。
- 最新内部评估数字来自 `results/controlled_llm_comparison_report.json`：**5.60 → 8.13（+2.53）**。
- `real_api_patient_dialogue_report.json` 实际 provider 为 `mock`，已避免误写成真实 API 证据。
- 当前仓库未提交真实截图，因此统一保留占位符。

### 仍需人工补充的信息
- [APPLICANT NAME]
- [EMAIL]
- [PHONE]
- [UNIVERSITY]
- [MAJOR]
- [GITHUB URL]
- [ADVENTUREX OFFICIAL PROMPT]
- [TEAM MEMBERS]
- [PREVIOUS AWARDS]
- [SPECIFIC SUBMISSION DEADLINE]
- 若需要真实页面截图：需运行系统后使用 demo data 安全截图
- 若需要最新真实 DeepSeek / MiniMax 可用性：需在本地环境手动验证

## Review 2：评审说服力审查

| 维度 | 分数（1-10） | 说明 |
|---|---:|---|
| 问题重要性 | 9 | 结合 dementia / caregiver burden 背景 |
| 项目独特性 | 9 | 明确不是普通 LLM wrapper |
| 当前执行力 | 9 | 代码、页面与 results 证明已有原型 |
| 技术可信度 | 8 | 明确 guard、grounding 与边界 |
| 五天可行性 | 9 | Hero Demo 聚焦明确 |
| 用户价值 | 9 | 双端价值清晰 |
| 安全意识 | 9 | 不做医疗诊断、不让模型猜用药 |
| 最终演示清晰度 | 9 | 演示链路具体 |

## Review 3：视觉审查

- 封面：已设计独立封面
- 图表：5 张 SVG，统一配色
- 表格：印刷样式已设置
- 中文字体：使用系统字体栈
- 截图：统一使用占位符，不伪造
- PDF 输出：待本地生成后检查页数、大小与文本可搜索性

## 已做修订
- 将当前版本统一收束为 v0.5
- 将 survey 与 usability 结果统一降级为“探索性摘要 / 测试计划”
- 将 PWA、location safety、memory review UI 等能力统一降级为 partial 或 placeholder
- 将 screenshot 统一改为显式 placeholder
- 将外部来源仅用于背景论证，不用于证明项目效果

## 最终提交建议
1. 先提交当前文稿版本，保证事实与边界可信。
2. 若时间允许，再补充 demo-safe 真实截图替换占位符。
3. 若能本地重新运行 DeepSeek demo test，可更新 latest run 时间。
4. 所有对外表述都坚持：**internal prototype, scenario-based evaluation, not clinical validation**。
