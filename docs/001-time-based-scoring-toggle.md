# PRD: Time-Based Scoring Toggle

## Metadata

- **Document ID**: 001
- **Status**: Draft
- **Feature**: Quiz-level toggle for time-based score decay
- **Created**: 2026-05-09
- **Owner**: TBD
- **Target Release**: TBD
- **Primary Areas**: Quiz editor, quiz persistence, live scoring, controller scoring, results verification

## Summary

ClassQuiz currently rewards speed automatically: a correct answer can receive up to 1000 points, and the score decreases as the player takes more time. This feature adds a quiz-level setting that lets quiz creators choose whether correct answers should use time-based score decay or award a fixed score.

The default must preserve existing behavior for current and newly created quizzes unless a quiz creator explicitly changes the setting.

## Problem

Teachers use quizzes for different learning goals. Some sessions should reward quick recall and competition, while others should reward correctness without penalizing students for taking time to think. Today, the scoring behavior is always time-based in the live answer paths, so quiz creators cannot match scoring behavior to their classroom intent.

## Goals

- Allow quiz creators to enable or disable time-based score decay per quiz.
- Allow quiz creators to set each question's maximum point value.
- Preserve existing scoring behavior by default.
- Apply the setting consistently across normal live play and controller-based play.
- Keep result displays and saved game results compatible with existing score fields.
- Preserve the setting through native quiz import/export flows.
- Make the setting understandable in the quiz editor without redesigning scoring.

## Non-Goals

- Adding custom scoring formulas or multiple decay curves.
- Reworking leaderboard, ranking, or result export UX beyond ensuring scores are correct.
- Recalculating historical game results.
- Changing correctness rules for question types.

## Current Behavior

- `classquiz/socket_server/__init__.py` defines `calculate_score(z, t)`, which returns a value based on elapsed time and a maximum score of 1000.
- `submit_answer` in `classquiz/socket_server/__init__.py` calls `calculate_score(...)` for correct answers and adds the result to Redis `player_scores`.
- `submit_answer_fn` in `classquiz/routers/box_controller/embedded/socket.py` uses the same `calculate_score(...)` helper for controller answers.
- `Quiz`, `QuizInput`, and `PlayGame` originally did not expose a quiz-level score-decay setting.
- `QuizQuestion` originally did not expose a per-question maximum point value.
- Frontend quiz data types in `frontend/src/lib/quiz_types.ts` and editor validation in `frontend/src/lib/yupSchemas.ts` originally did not include scoring mode or question point fields.

## Proposed Solution

Add a quiz-level boolean setting, tentatively named `time_based_scoring`, with default value `true`, and a per-question `points` field with default value `1000`.

- When `time_based_scoring` is `true`, correct answers use the existing time-based score decay, with each question's `points` value as the maximum score.
- When `time_based_scoring` is `false`, correct answers receive the question's full `points` value and incorrect answers receive 0.

The setting should be stored on the quiz, copied into the active `PlayGame`, and used by every live answer submission path. Question point values should travel with the existing question JSON.

## User Stories

- As a teacher, I want to disable time-based scoring so that students are scored only on correctness.
- As a teacher, I want to keep time-based scoring enabled so that faster correct answers are rewarded in competitive quizzes.
- As a student, I want scoring rules to remain consistent during a live game so that the leaderboard feels fair.
- As a quiz creator, I want the setting to persist when I edit an existing quiz so that saved behavior does not unexpectedly change.
- As a quiz creator, I want harder questions to be worth more points so that score weighting matches quiz design.

## Functional Requirements

1. Quiz creators can toggle time-based score decay in the quiz settings screen.
2. The setting is persisted with the quiz and returned by quiz get/list APIs where full quiz data is returned.
3. Existing quizzes without the stored setting behave as if `time_based_scoring` is `true`.
4. Existing questions without stored points behave as if `points` is `1000`.
5. New quizzes default to `time_based_scoring: true`; new questions default to `points: 1000`.
6. Starting a game copies the quiz setting and question point values into `PlayGame` so scoring does not change mid-game if the quiz is edited.
7. Normal Socket.IO answer submission uses the setting and question points when assigning points.
8. Embedded box controller answer submission uses the same setting and question point behavior.
9. Result storage continues to save numeric per-answer `score` and aggregate `player_scores` without schema changes to historical result shape.
10. Native `.cqa` export/import preserves `time_based_scoring` and question points.
11. Kahoot and Excel imports default imported quizzes to `time_based_scoring: true` and questions to `points: 1000`.
12. The UI label and helper text explain the behavior in plain language.

## UX Requirements

The time-based scoring setting should live in the existing quiz settings area. The point value should live in each question card near the existing time limit input.

Suggested copy:

- Label: `Time-based scoring`
- Helper text: `When enabled, faster correct answers earn more points. When disabled, every correct answer earns its full point value.`

Default UI state:

- Enabled for new quizzes.
- Reflects the saved value for existing quizzes.

## Technical Scope

### Backend

- Add `time_based_scoring: bool = True` to `QuizInput`.
- Add `points: int = 1000` with non-negative validation to `QuizQuestion`.
- Add a non-null boolean `time_based_scoring` column to the `quiz` table with default `true`.
- Add `time_based_scoring: bool = True` to the `Quiz` model.
- Add `time_based_scoring: bool = True` to `PlayGame`.
- No database column migration is required for per-question points because questions are stored in the existing quiz JSON field.
- In `classquiz/routers/quiz.py`, copy `quiz.time_based_scoring` into `PlayGame` when starting a quiz.
- In `classquiz/socket_server/__init__.py`, only apply time decay when `game_data.time_based_scoring` is true; use `question.points` as the maximum score.
- In `classquiz/routers/box_controller/embedded/socket.py`, apply the same scoring branch and per-question point behavior for controller answers.
- Add an Alembic migration under `migrations/versions/` for the new quiz column.

### Frontend

- Add `time_based_scoring: boolean` to `QuizData` and `EditorData` in `frontend/src/lib/quiz_types.ts`.
- Add `points: number` to each `Question` in `frontend/src/lib/quiz_types.ts`.
- Add validation in `frontend/src/lib/yupSchemas.ts` with default/required boolean behavior and non-negative integer points.
- Initialize new quiz data in `frontend/src/routes/create/+page.svelte` with `time_based_scoring: true`.
- Ensure edit flow in `frontend/src/routes/edit/+page.svelte` defaults missing values to `true` for old quizzes.
- Add a toggle to `frontend/src/lib/editor/settings-card.svelte` bound to `data.time_based_scoring`.
- Add a point input to each question card bound to `data.questions[selected_question].points`.
- Add or reuse localization keys for the label/helper text if the editor uses localized strings for comparable settings.

### Import and Export

- Ensure `.cqa` export in `classquiz/routers/eximport.py` includes the persisted setting and question points through `quiz.model_dump()`.
- Ensure `.cqa` import accepts older files that do not contain the field by applying backend defaults.
- Ensure Excel import in `classquiz/helpers/__init__.py` creates quizzes with default `time_based_scoring: true` and question points of `1000`.
- Ensure Kahoot import in `classquiz/kahoot_importer/import_quiz.py` creates quizzes with default `time_based_scoring: true` and question points of `1000`.

### Tests and Verification

- Backend scoring test: correct answer with `time_based_scoring=true` uses time-based score and remains capped at 1000.
- Backend scoring test: correct answer with `time_based_scoring=false` awards exactly the question point value.
- Backend scoring test: correct answer with `time_based_scoring=true` decays from the question point value.
- Backend scoring test: wrong answer remains 0 in both modes.
- Controller scoring test or equivalent verification for the embedded controller path.
- Frontend validation/build check for editor data with and without the new field.
- Import/export verification for old `.cqa` files missing the setting and new `.cqa` files preserving it.
- Migration verification using the repository's backend test path, not plain `pytest` alone.

## Acceptance Criteria

- A quiz creator can enable or disable time-based scoring from quiz settings.
- Saving and reopening a quiz preserves the selected setting and each question's point value.
- Existing quizzes continue to use time-based scoring unless changed.
- A live game started from a quiz with time-based scoring disabled awards each question's point value for every correct answer regardless of response time.
- A live game started from a quiz with time-based scoring enabled decays from each question's point value.
- Controller-based play matches normal live play for both setting values.
- Native `.cqa` export/import preserves the selected scoring mode and question point values, and older imports default safely.
- Result screens display the computed scores without requiring historical result migration.
- Tests/build checks pass according to project-specific frontend and backend verification rules.

## Milestones

- [ ] Data model and migration support the quiz-level scoring setting with safe defaults.
- [ ] Question model and editor flows support per-question point values with safe defaults.
- [ ] Editor create/edit flows can display, modify, validate, save, and reload the setting.
- [ ] Game start flow carries the setting into active live game state.
- [ ] Normal live play and controller play both apply the setting consistently.
- [ ] Result display and storage are verified against both scoring modes.
- [ ] Import/export paths preserve or default the setting correctly.
- [ ] Regression tests and project-specific validation pass.
- [ ] User-facing documentation or release notes are updated if this setting is exposed beyond the editor UI.

## Risks and Mitigations

- **Risk**: Existing quizzes may not have the scoring setting or question point fields in JSON/API responses.
  - **Mitigation**: Default missing scoring settings to `true` and missing question points to `1000` in backend models and edit flow.

- **Risk**: Normal play and controller play could diverge.
  - **Mitigation**: Cover both scoring paths and consider extracting a small shared helper for score selection.

- **Risk**: Historical results might be interpreted under the new setting.
  - **Mitigation**: Do not recalculate historical results; saved result scores remain authoritative.

- **Risk**: Migration/test setup may fail if run with plain `pytest`.
  - **Mitigation**: Follow repository backend validation guidance and use the project test script with required environment.

## Open Questions

1. Should the setting name exposed to users be `Time-based scoring`, `Speed bonus`, or another phrase?
2. Should public quiz detail pages show the scoring mode and question point values before a host starts the quiz?

## Progress Log

- 2026-05-09: Draft PRD created from codebase analysis and current scoring behavior discussion.
- 2026-05-09: Implemented quiz-level `time_based_scoring` model, migration, editor UI, normal play scoring, controller scoring, and targeted scoring tests. Full backend test script could not run locally because `podman` and `pipenv` are unavailable.
- 2026-05-09: Extended implementation with per-question `points`, default `1000`, editor point input, and scoring from each question's maximum point value.
