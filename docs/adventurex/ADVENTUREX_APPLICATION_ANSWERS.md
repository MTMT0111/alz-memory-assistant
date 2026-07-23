# ADVENTUREX APPLICATION ANSWERS

## 用 100 字介绍项目
- 精简版：这是一个面向阿尔兹海默症家庭场景的受控式 AI 原型。它把患者端情感记忆陪伴和家属端照护闭环连接起来，通过结构化提醒、规则安全层、家属审核记忆和 familiar materials，让通用大模型变成更可控、更个性化的家庭照护辅助系统。
- 标准版：Alzheimer Family Care Assistant 不是普通聊天机器人，而是一个连接患者端温和陪伴与家属端照护管理的受控式 AI 系统原型。患者端通过照片、故事、语音留言和熟悉素材获得更低刺激的对话支持；家属端通过提醒、risk events、daily care 和 memory review 获得更可行动的照护信息。
- 英文版：Alzheimer Family Care Assistant is a controlled AI prototype for family dementia care. It connects patient-side emotional memory companionship with caregiver-side care loops through structured reminders, safety guardrails, caregiver-governed memory review, and familiar materials.

## 为什么这个问题重要
- 精简版：因为阿尔兹海默症家庭每天面对的不是单一痛点，而是重复提问、焦虑、位置困惑、用药不确定和家属长期压力同时存在。
- 标准版：阿尔兹海默症家庭照护同时涉及患者端的熟悉感与情绪支持，以及家属端的提醒管理、风险反馈和照护连续性。一个只会生成语言的系统，很难天然理解某个家庭的真实照护状态与个人记忆背景。
- 英文版：This matters because family dementia care is not a single pain point. Patients may need reassurance and familiarity, while caregivers need reminders, risk visibility, and continuity of care.

## 你的方案有什么不同
- 精简版：不同点不在于“接了大模型”，而在于结构化照护 grounding、安全 guard、家属审核长期记忆，以及照片/语音/故事带来的情感记忆 grounding。
- 标准版：我的方案把模型放在受控的位置：用药与 reminder 事实来自结构化数据；高风险场景通过 rule detection、guard 和 template fallback 控制；长期记忆不能自动写入，必须经过 caregiver review；患者端对话引入家庭照片、语音留言、旧地点和个人故事作为情感上下文。
- 英文版：The differentiation is not the model call itself, but structured care grounding, safety-controlled dialogue, caregiver-governed long-term memory, and emotional grounding through family materials.

## 当前已经完成什么
- 精简版：我已经做出一个可运行的 v0.5 原型，包括多患者管理、患者对话、家属工作台、提醒、risk events、familiar materials、photo timeline、memory candidate、reminiscence、consent、TTS fallback 和内部评估。
- 标准版：当前仓库中已经完成一个可运行的 v0.5 原型：FastAPI + SQLite 架构，多患者与 caregiver PIN 登录，DeepSeek 主链路，患者对话页，家属工作台，reminder / medication schedule，daily care summary，caregiver events / risk events，familiar materials，photo timeline，memory candidate capture 与 approve，reminiscence 页面，consent flow，MiniMax TTS 集成与浏览器 fallback，以及内部评估页面。
- 英文版：I already have a working v0.5 prototype with multi-patient management, caregiver PIN login, DeepSeek-based conversation, reminder and medication state, caregiver dashboard, familiar materials, photo timeline, memory candidate review, reminiscence pages, consent flow, TTS fallback, and internal evaluation artifacts.

## 五天准备完成什么
- 精简版：五天内我不会无限扩功能，而是围绕一个 Hero Demo，把“家庭照片与语音记忆触发患者对话，并同步进入家属照护闭环”打磨成可展示 MVP。
- 标准版：五天工作的重点是整合、稳定、演示与可理解性：家属建立患者档案，上传老照片并补充照片故事，录制语音说明；患者从照片进入回忆对话；当出现用药、外出或敏感亲人问题时，系统切换到结构化照护与安全控制；家属端收到摘要、风险提示和待审核记忆线索。
- 英文版：In five days, I want to polish one clear Hero Demo rather than keep expanding scope: a caregiver uploads a family photo and a voice note, the patient enters a gentle reminiscence conversation from that cue, and the system bridges that conversation into a caregiver-visible care loop with risk signals and memory review.

## 为什么你适合完成它
- 精简版：因为我已经在持续构建这个系统，而不是停留在想法阶段，并且能独立完成后端、前端、LLM 集成、测试和产品叙事。
- 标准版：我适合完成它，因为我已经把这个项目从概念推进成了一个可运行原型：不仅能做产品设计，也能自己完成 FastAPI、SQLite、页面交互、LLM provider routing、安全规则、测试脚本和评估材料。我对患者体验与家属压力都保持敏感，也擅长把复杂系统拆成可验证闭环。
- 英文版：I am a strong fit to build this because I am already building it end to end. I can design the product, implement the backend and frontend, integrate LLM providers, add guardrails, run scenario-based tests, and turn a complex system into a clear, verifiable loop.

## 为什么希望参加 AdventureX
- 精简版：因为我不是想在五天里提出概念，而是想把一个已有原型推进成评审和用户都能看懂的 MVP。
- 标准版：我希望参加 AdventureX，因为这个项目现在最需要的不是更多零散功能，而是一次高强度、跨视角的整合与验证。AdventureX 的五天非常适合让我把已有原型浓缩成一个清晰、可信、可展示的 Hero Demo，同时获得产品、技术和用户体验层面的集中反馈。
- 英文版：I want to join AdventureX because I am not starting from an idea. I already have a prototype, and what I need now is a focused environment to turn it into a clearer, more credible, more demoable MVP.

## 项目最大的风险是什么
- 精简版：最大风险是把功能讲得过满，或者把部分实现能力误写成完整能力，导致评审信任下降。
- 标准版：最大的风险不是“功能不够多”，而是 scope 失控和表述失真。当前系统已经有不少能力，但其中有些是部分实现、有些仍依赖环境、有些还停留在演示级稳定性。如果不聚焦单一 Hero Demo，或者把 partial 能力写成 completed，反而会削弱可信度。
- 英文版：The biggest risk is over-claiming or over-scoping. Some capabilities are already solid, while others are partial, environment-dependent, or only demo-stable. If I try to present everything as complete, I lose credibility.

## 五天后如何验证成功
- 精简版：如果 Hero Demo 能无阻塞跑通，参与者能理解患者端与家属端的区别，并完成照片录入、对话、提醒确认和记忆审核，五天就是成功的。
- 标准版：五天后的成功验证标准是：第一，Hero Demo 可以从家庭照片和语音记忆出发，无阻塞地进入患者对话，再进入 caregiver summary 与 memory review；第二，参与者能够清楚理解这不是普通聊天机器人，而是“患者端陪伴 + 家属端照护闭环”的双端系统；第三，关键安全边界被保留，例如 medication 不由模型猜、敏感记忆需要 caregiver approval。
- 英文版：Success after five days means the Hero Demo runs end to end without blocking, observers can clearly understand the difference between the patient-side companion and the caregiver-side care loop, and the key safety boundaries remain intact.
