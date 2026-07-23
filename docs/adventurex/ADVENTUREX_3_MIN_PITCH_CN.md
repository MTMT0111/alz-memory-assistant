# AdventureX 3-Minute Pitch (CN)

想象这样一个场景：一位阿尔兹海默症老人看到年轻时的家庭照片，突然想起过去，又马上问自己今天是不是还没吃药，接着说想出去找女儿。对家属来说，最难的从来不是“让 AI 陪她说几句话”，而是如何在安抚情绪、确认事实、避免风险和减轻日常负担之间不断切换。

这就是我做这个项目的原因。

我现在做的不是一个普通陪聊机器人，也不是医疗诊断系统，而是一个面向阿尔兹海默症家庭场景的受控式 AI 原型。我把它定义为 **Care Loop + Emotional Memory Companion**。患者端通过熟悉人物、家庭照片、语音留言和个人故事提供更低刺激的陪伴；家属端通过 reminder、daily care、risk events 和 memory review 形成照护闭环。

它和通用 LLM 最大的区别，是把模型放在被约束的位置。用药状态来自结构化 reminder，不由模型猜；高风险场景有 rule guard、postprocess 和 template fallback；长期记忆不能自动写入，必须经过 caregiver review；而照片、声音、老歌和旧地点也不是装饰，它们是患者端对话真正的情感上下文。

当前仓库里，我已经做出了一个可运行的 v0.5 原型：FastAPI + SQLite、多患者管理、DeepSeek 主链路、患者对话页、家属看板、materials、photo timeline、memory candidate、reminiscence、consent、TTS fallback，以及内部评估页面。最新 committed 结果显示，在 10 个内部场景中，普通直接模型回复平均分是 5.60，而完整照护系统链路是 8.13，提升了 2.53。这个结果不是临床验证，但它说明：把照护事实 grounding、安全控制和家庭记忆结合起来，确实比直接让 LLM 聊天更接近真实家庭需要。

我想在 AdventureX 的五天里完成的，不是继续堆功能，而是做一个非常清晰的 Hero Demo：**From Family Memory to Safer Care**。家属建立患者档案，上传老照片和语音说明；患者从照片进入回忆对话；当出现用药、外出或敏感亲人问题时，系统切换到结构化照护与安全控制；家属端收到摘要、风险提示和待审核记忆线索。

我申请 AdventureX，不是为了验证“AI 能不能做陪伴”，而是为了把一个已经运行的原型推进成一个让评审、用户和未来合作者都能快速看懂价值路径的 MVP。