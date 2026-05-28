# v0.5 System Overview

## Version Positioning

v0.5 is a stable GitHub/demo version of the Alzheimer Family Care Assistant. The project is a controlled LLM prototype for family care, not a general chatbot and not a medical diagnosis system.

Primary model:

- Provider: DeepSeek
- Model: `deepseek-v4-flash`
- Mock: fallback/debug only
- Template fallback: safety repair path for high-risk or unstable outputs

## Core Capabilities

### Patient-side Stable Companionship

- `/conversation` provides the patient-facing conversation page.
- DeepSeek is used as the primary LLM provider.
- Replies are short, gentle, low-stimulation, and context-aware.
- High-risk scenarios are guarded: medication uncertainty, wandering/location confusion, anxiety, deceased relatives, and repeated questions.
- Browser TTS fallback works through `speechSynthesis`.
- MiniMax TTS configuration and wrapper are ready for end-to-end validation.

### Caregiver-side Daily Care Loop

- `/analysis` provides the caregiver dashboard.
- Reminder status supports pending, confirmed, missed, and skipped states.
- Medication-related replies use structured reminder records instead of LLM guesses.
- Caregiver events capture risk signals from patient conversations.
- Daily care summary combines reminders, events, and suggested actions.

### Personal Memory and Reminiscence

- `/materials` manages familiar materials such as family photos, voice messages, music, places, and old events.
- `/chat-history` shows dialogue history and pending memory candidates.
- `/reminiscence` uses approved materials for gentle memory support.
- Memory candidates must be reviewed by caregivers before becoming durable familiar materials.

## Main Pages

- `/app_home`: app entry and system-line overview
- `/demo-flow`: stable walkthrough for presentations
- `/conversation`: patient-side chat
- `/conversation?debug=1`: chat with provider/fallback diagnostics
- `/analysis`: caregiver daily care dashboard
- `/materials`: familiar materials library
- `/chat-history`: chat history and memory candidate review
- `/reminiscence`: memory and reminiscence support
- `/test-results`: evaluation and acceptance evidence
- `/debug-dashboard`: provider and diagnostic visibility

## Evaluation Snapshot

Current controlled comparison:

- direct baseline LLM score: `5.60`
- care system score: `8.13`
- improvement: `+2.53`
- verdict: `PASS`

The evaluation compares direct DeepSeek responses with the full care system pipeline. The care system performs better because it combines personal context, reminder status, response guards, template fallback, caregiver events, and memory candidate capture.

## Safety Boundary

- This system is not a medical device.
- It does not diagnose or treat Alzheimer’s disease.
- Medication facts are not inferred by the LLM.
- Sensitive memories require caregiver review.
- Real patient data should not be used without explicit consent.
