# v0.5 Daily Care and Memory Capture

## Purpose

v0.5 connects patient-side conversation with caregiver-side care records. The system should not only answer a message; it should also update the caregiver view when the conversation reveals care needs or useful memory clues.

## Daily Care Loop

The daily care loop combines:

- reminder records
- medication confirmation/miss/skip status
- caregiver events
- risk level
- suggested actions
- daily care summary

Medication facts are read from structured reminder status. The LLM should not guess whether the patient has taken medication.

## Reminder Status

Supported states:

- `pending`: reminder exists but has not been handled
- `confirmed`: caregiver or patient confirmation exists
- `missed`: scheduled reminder was missed
- `skipped`: caregiver intentionally skipped it

Medication-related patient messages should use these states. If the status is uncertain or missed, the patient-side reply should encourage caregiver confirmation instead of giving a medication decision.

## Caregiver Events

Caregiver events record important signals from patient-side conversation, such as:

- wandering/location risk
- anxiety or fear
- repeated medication uncertainty
- repeated family-member questions
- need for caregiver follow-up

These events appear in `/analysis` and feed the daily care summary.

## Memory Candidate Capture

When the patient mentions a person, old place, familiar event, or emotionally meaningful memory, the system may create a memory candidate.

Candidate fields include:

- source message
- suggested title
- suggested description
- suggested material type
- related person
- sensitivity level
- status

Candidates do not become long-term familiar materials automatically.

## Caregiver Review

Caregivers can approve or reject memory candidates in `/chat-history`.

Approval means:

- the memory is considered useful enough for future conversation context
- the material can enter the familiar materials library
- it can later support reminiscence or gentle orientation

Rejection means:

- the candidate remains out of active conversation context
- sensitive, wrong, or unhelpful content is not promoted

## Familiar Materials

Approved materials can include:

- family photos
- voice messages
- old songs
- old places
- old events
- caregiver-entered notes

These materials can be used by the chat pipeline to make replies more personal and familiar.

## Safety Notes

- Sensitive memory requires caregiver review.
- Real patient data should not be used without consent.
- The system should avoid testing the patient’s memory.
- The system should avoid direct correction that increases distress.
- Medication status must come from reminder records.
