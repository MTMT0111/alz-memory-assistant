# Usability Test Plan v0.5

## Purpose

Run a small-sample usability test for the Alzheimer Family Care Assistant v0.5. The goal is to evaluate whether caregivers and potential users understand the care loop, trust the safety boundaries, and find the patient-side replies gentle and useful.

## Participants

Recommended sample:

- 3 to 5 caregivers or students familiar with family care scenarios
- optional: 1 to 2 domain reviewers such as teachers, social-work students, nursing students, or HCI peers

Do not use real patient data unless consent has been obtained.

## Test Setup

Use demo patient data only.

Routes:

- `/app_home`
- `/demo-flow`
- `/conversation?debug=1`
- `/analysis`
- `/materials`
- `/chat-history`
- `/reminiscence`
- `/test-results`

## Tasks

1. Ask the patient-side chat a repeated-family question such as “小雨什么时候回来？”
2. Ask a medication-status question such as “我是不是还没吃药？”
3. Trigger a possible risk scene such as “我想出去找她。”
4. Review the caregiver dashboard and identify today’s care priority.
5. Open familiar materials and check whether the material context is understandable.
6. Review a memory candidate and decide whether to approve or reject it.
7. Use the reminiscence page and judge whether the wording feels gentle.

## Observation Points

- Can the participant understand the difference between direct LLM chat and the controlled care pipeline?
- Do patient-side replies feel short, gentle, and low-stimulation?
- Does the caregiver dashboard explain the care status clearly?
- Is medication handling trusted because it uses reminder status?
- Are memory candidates and caregiver approval easy to understand?
- Are any pages confusing or too developer-oriented?

## Rating Questions

Use a 1 to 5 scale:

- The patient-side response feels gentle.
- The medication safety boundary is clear.
- The caregiver dashboard is useful.
- The memory candidate review flow is understandable.
- I would trust this as a supportive prototype, not as medical decision-making.
- I can explain the value of this system after the demo.

## Interview Questions

- Which part felt most useful for family caregivers?
- Which response felt unsafe, confusing, or too mechanical?
- What should the system never say to a patient?
- What information should require caregiver approval?
- Would voice interaction improve the experience?
- What privacy or consent warning should be added before real use?

## Success Criteria

- Most participants understand that this is not a medical device.
- Most participants can identify why reminder status matters for medication replies.
- Most participants can complete the caregiver event and memory candidate review tasks.
- No participant believes the system should replace professional medical advice.

## Output

Save anonymized notes under `results/` only if they contain no real patient data. Prefer aggregated observations over raw dialogue transcripts.
