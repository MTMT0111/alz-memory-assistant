# FINAL DEMO SCRIPT

## 0:00–0:30 痛点
- 开场：阿尔兹海默症家庭真正需要的不是普通陪聊，而是“患者熟悉感 + 家属行动支持”。
- 点题：这就是 **Care Loop + Emotional Memory Companion**。

## 0:30–1:00 患者档案和家庭素材
- 打开 `/patients`，选择当前患者。
- 打开 `/patient/{patient_id}/settings`，说明家属维护患者信息、用药和团队。
- 打开 `/materials/{patient_id}`，展示照片、故事、语音说明结构。

## 1:00–2:00 照片进入患者对话
- 打开 `/photo-timeline/{patient_id}`。
- 展示一张老照片、年份、人物、故事与语音说明。
- 点击进入 `/conversation/{patient_id}`。
- 强调这是 emotional memory grounding，而不是考试式提问。

## 2:00–2:40 用药和外出风险
- 输入“我是不是还没吃药？”
- 说明系统不会让 LLM 猜测，而是优先读取 structured reminder status。
- 再输入“我想出去找她”或“这里是哪里？我要回家。”
- 说明高风险场景由 rule guard 与 template fallback 控制。

## 2:40–3:20 家属端
- 切换到 `/care-portal/{patient_id}`。
- 展示 medication 状态、risk events、今日概览、quick actions。
- 如有可用数据，可补充 `/care-trend/{patient_id}`。

## 3:20–4:00 记忆审核
- 进入 `/chat-history/{patient_id}` 或结合候选 API 说明 memory candidate 流程。
- 强调长期记忆不会自动写入，必须经过 caregiver approval。

## 4:00–4:30 评估
- 打开 `/test-results`。
- 展示 baseline 5.60 → care system 8.13（+2.53）。
- 明确说明：这是内部场景评估，不是临床验证。

## 4:30–5:00 未来与结尾
- 总结：这不是更会聊天的 AI，而是更懂家庭照护流程、更尊重熟悉感和安全边界的辅助系统。
- 结束句：**From Family Memory to Safer Care.**