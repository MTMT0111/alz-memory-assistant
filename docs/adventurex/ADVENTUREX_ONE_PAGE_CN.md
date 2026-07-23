# AdventureX One-Page Summary (CN)

## Problem
阿尔兹海默症家庭照护的难点不只是聊天，而是重复提问、焦虑、位置困惑、用药不确定与家属长期压力同时存在。

## Insight
通用大模型能生成语言，但不能天然承担家庭照护责任。真正需要的是结构化照护状态、家属审核机制、个人情感记忆与安全控制的组合。

## Solution
本项目是 **Care Loop + Emotional Memory Companion** 原型：患者端通过照片、故事、语音留言与 familiar materials 获得温和陪伴；家属端通过 reminder、daily care、risk events 与 memory review 获得行动支持。

## Current Progress
当前仓库快照已实现：FastAPI + SQLite、多患者管理、DeepSeek 主链路、患者对话、家属看板、materials、photo timeline、reminiscence、memory candidate、consent、TTS fallback 与 PWA 基础壳。

## Differentiation
1. Structured Care Grounding
2. Safety-Controlled Dialogue
3. Caregiver-Governed Memory
4. Emotional Memory Grounding

## Current Evidence
内部 10 场景评估：baseline **5.60**；care system **8.13**；improvement **+2.53**；PASS。

> 注：这是内部场景评估，不是临床验证。

## Five-Day Goal
围绕 **From Family Memory to Safer Care** 打磨 Hero Demo：家属上传照片与语音 → 患者进入回忆对话 → 系统切换到结构化照护与安全控制 → 家属收到摘要、风险提示与待审核记忆线索。

## GitHub
**[GITHUB URL]**
