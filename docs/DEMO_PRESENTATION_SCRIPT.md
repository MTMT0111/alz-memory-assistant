# Demo Presentation Script

## Goal

Use this script to present v0.5 as a controlled Alzheimer family-care LLM prototype. The main message is that the system is not just a chatbot: it connects patient-side companionship, caregiver-side daily care, and reviewed personal memory support.

## 1. Opening

This project is an Alzheimer family care assistant prototype. It is not a medical device and does not provide diagnosis or treatment. Its purpose is to make daily companionship safer, calmer, and more useful for family caregivers.

Mention the survey evidence:

- 33 valid responses
- 87.88% considered such a device necessary
- 84.84% accepted caregiver-entered profile/materials
- 81.82% preferred voice interaction

## 2. App Home

Open `/app_home`.

Explain the three system lines:

- patient-side stable companionship
- caregiver-side daily care loop
- personal memory and reminiscence support

## 3. Demo Flow

Open `/demo-flow`.

Use it as the presentation map. This keeps the demo stable and avoids jumping between pages randomly.

## 4. Patient-side Conversation

Open `/conversation?debug=1`.

Recommended demo prompts:

- 小雨什么时候回来？
- 我是不是还没吃药？
- 我想出去找她。
- 我有点害怕。

Point out:

- DeepSeek is the primary provider.
- High-risk scenes can trigger guard/template fallback.
- Medication answers use reminder status.
- Familiar materials can be used as context.
- Browser TTS fallback is available; MiniMax TTS is configurable.

## 5. Caregiver Dashboard

Open `/analysis`.

Show:

- reminder status
- daily care summary
- caregiver events
- risk level
- suggested actions

Emphasize that medication facts are not guessed by the LLM.

## 6. Materials and Memory Capture

Open `/materials`, then `/chat-history`.

Show:

- familiar materials library
- family/person/place/music/event context
- pending memory candidates
- caregiver approval/rejection

Explain that sensitive or uncertain memory is reviewed before becoming long-term material.

## 7. Reminiscence

Open `/reminiscence`.

Explain that the page uses confirmed materials for gentle recall. It is not a memory test and should avoid pressure or correction.

## 8. Evaluation Evidence

Open `/test-results`.

Current controlled comparison:

- direct baseline LLM score: `5.60`
- care system score: `8.13`
- improvement: `+2.53`
- verdict: `PASS`

Explain that the comparison uses direct DeepSeek responses versus the complete care-system pipeline.

## Closing

v0.5 demonstrates a controlled care loop: patient conversation creates safe replies, caregiver-visible signals, and reviewed memory candidates. v0.6 should focus on small-sample usability testing, privacy/consent pages, and MiniMax TTS end-to-end validation.
