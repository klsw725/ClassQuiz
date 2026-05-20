# PRD: Text Answer Whitespace Matching

## Metadata

- **Document ID**: 002
- **Status**: Draft
- **Feature**: Per-question text answer whitespace matching
- **Created**: 2026-05-17
- **Owner**: TBD
- **Target Release**: TBD
- **Primary Areas**: Quiz editor, quiz persistence, live answer grading

## Summary

Text questions currently compare answers with the existing case-sensitivity option only. This feature adds a per-question text option that lets quiz creators decide whether whitespace must match exactly or should be ignored during grading.

The default must preserve the current behavior: whitespace remains significant unless the quiz creator explicitly enables whitespace-insensitive matching.

## Problem

Some text-answer questions should accept spacing variations, such as `대한민국`, `대한 민국`, or `대 한 민 국`, as the same answer. Other questions intentionally require exact spacing. Today quiz creators cannot choose between these grading modes.

## Goals

- Add a text-question setting for ignoring whitespace during grading.
- Store the setting with each text question in the existing question JSON payload.
- Keep current quizzes and newly created answers exact about whitespace by default.
- Apply the setting consistently in the live answer grading path.
- Expose the setting in the text answer editor next to the existing case-sensitivity control.

## Non-Goals

- Changing case-sensitivity behavior.
- Adding quiz-wide whitespace defaults.
- Normalizing punctuation or non-whitespace characters.
- Recalculating historical game results.

## Current Behavior

- `TextQuizAnswer` contains `answer` and `case_sensitive`.
- `check_text_question` compares text answers exactly when `case_sensitive` is true, and lowercases both sides when false.
- Text answer data is stored inside existing quiz JSON fields, so adding this option does not require a database column migration.
- `TextEditorPart.svelte` initializes and toggles `case_sensitive` for each text answer.

## Proposed Behavior

Add a boolean text question field, tentatively named `ignore_whitespace`.

- When `ignore_whitespace` is `false`, keep the current comparison behavior.
- When `ignore_whitespace` is `true`, remove whitespace from both submitted and configured answers before applying the existing case-sensitive or case-insensitive comparison.
- Treat all Unicode whitespace matched by the runtime whitespace matcher as removable whitespace.
- Existing questions without the field behave as `ignore_whitespace: false`.

## Acceptance Criteria

1. Text questions can enable or disable whitespace-insensitive matching per question.
2. Existing saved text questions without the new field still validate and grade with whitespace significant.
3. With `ignore_whitespace: true`, `대한민국`, `대한 민국`, and `대 한 민 국` can match the same configured answer.
4. With `ignore_whitespace: false`, whitespace differences remain incorrect.
5. Case-sensitivity and whitespace matching compose correctly.
6. Frontend validation accepts the new option and newly created text questions include it.

## Implementation Notes

- Backend model: add `ignore_whitespace: bool = False` to `QuizQuestion`.
- Backend grading: normalize text through a small helper in `classquiz/socket_server/helpers.py` before the existing case comparison.
- Frontend types: add `ignore_whitespace` to the question shape.
- Frontend editor: preserve existing values while defaulting missing `ignore_whitespace` to `false`, and add one toggle button for the selected text question.
- Frontend validation: require/default the boolean for text questions.

## Verification

- Add or run backend checks for `check_text_question` covering whitespace-sensitive, whitespace-insensitive, and case-sensitive combinations.
- Run frontend type/check/build validation from `frontend/` after editing Svelte/TypeScript files.
- If full backend test execution is not possible locally, document the exact blocker because this repository expects `./run_tests.sh a` with required environment and services.
