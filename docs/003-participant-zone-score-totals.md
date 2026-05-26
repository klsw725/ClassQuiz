# PRD: Participant Zone Score Totals

## Metadata

- **Document ID**: 003
- **Status**: Draft
- **Feature**: Participant zone selection and saved result zone totals
- **Created**: 2026-05-17
- **Owner**: TBD
- **Target Release**: TBD
- **Primary Areas**: Participant join flow, live game session metadata, saved results, result detail view

## Summary

Game participants should choose a zone before joining a live game. The fixed zone choices are `1구역`, `2구역`, `3구역`, `4구역`, `5구역`, `6구역`, `7구역`, `8구역`, `9구역`, `10구역`, and `11구역`.

Gameplay and scoring remain individual. After the admin saves results, the result detail page should keep showing the existing individual player results and also show a zone totals table computed from the saved player scores and each player's selected zone.

## Problem

Teachers can review individual scores after a game, but they cannot see how fixed classroom zones performed as groups. They need a zone summary for saved results without changing how players answer questions, earn points, or appear in the normal live game flow.

## Goals

- Require each participant to select one of the fixed zones before joining a game.
- Keep player-level gameplay and scoring keyed by the zone-scoped participant identity, while preserving historical saved results that may not have zone data.
- Persist each saved result with enough player-to-zone data to compute historical zone totals later.
- Show individual results and zone aggregate totals together on the result detail page.
- Preserve existing historical results that do not have zone data.

## Non-Goals

- Making the zone list configurable.
- Adding team gameplay, shared answers, shared leaderboards, or team-based scoring.
- Changing answer submission, live score calculation, or ranking rules beyond the zone-scoped participant identity.
- Redesigning the participant join page or result detail page beyond the zone field and totals table.
- Recalculating old saved results that did not capture zones.

## Current Behavior

- `frontend/src/lib/play/join.svelte` asks for the game PIN first, then asks for username and an optional custom field. It emits `join_game` with `username`, `game_pin`, `captcha`, and optional `custom_field`.
- `frontend/src/routes/play/+page.svelte` renders `JoinGame`, keeps the joined username and game PIN, and stores join data for rejoin behavior.
- `classquiz/socket_server/models.py` defines `JoinGameData` with `username`, `game_pin`, `captcha`, and `custom_field`.
- `classquiz/socket_server/__init__.py` stores game sessions by zone-scoped participant identity, increments `game_session:{pin}:player_scores` by participant key, and stores optional custom field values in `game:{pin}:players:custom_fields`.
- `classquiz/socket_server/export_helpers.py` reads Redis `player_scores` and `custom_field_data`, then saves them into `GameResults`.
- `classquiz/db/models.py` defines `GameResults.player_scores` and `GameResults.custom_field_data` as JSON fields.
- `frontend/src/routes/results/[result_id]/+page.svelte` passes `player_scores`, `custom_field_data`, and `answers` into `PlayerOverview`.
- `frontend/src/routes/results/[result_id]/player_overview.svelte` renders sorted per-player scores and correct answer counts.

## Proposed Behavior

Add a required participant zone field to the join flow after the game PIN is accepted and before the player joins the game.

- The only valid zone options are `1구역` through `11구역`.
- `join_game` includes the selected zone with the existing username, game PIN, captcha, and optional custom field.
- The socket server stores the selected zone by participant identity for the active game session.
- Player scoring remains individual and keyed by participant identity. Correct counts, player scores, answer handling, and gameplay state do not use the zone to calculate individual scores.
- When the admin saves results, the saved result includes player-to-zone data for the players whose scores are saved.
- The result detail page shows the existing individual results and a zone totals table in the same result view.
- Zone totals are computed by summing saved player scores for all players assigned to each zone.
- Historical results without saved zone data still show individual results. The zone totals section may be omitted or rendered as an empty state.

## User Stories

- As a participant, I want to choose my zone before joining so that my score can count toward the right classroom group.
- As a participant, I want my own score and gameplay to work the same after choosing a zone.
- As a teacher, I want saved result details to show individual scores and zone totals together so I can review both views after class.
- As a teacher, I want old saved results to keep opening even if they do not have zone data.

## Functional Requirements

1. The participant join form requires exactly one selected zone before emitting `join_game`.
2. The selectable zones are fixed to `1구역`, `2구역`, `3구역`, `4구역`, `5구역`, `6구역`, `7구역`, `8구역`, `9구역`, `10구역`, and `11구역`.
3. `JoinGameData` accepts the selected zone and rejects values outside the fixed list.
4. `classquiz/socket_server/__init__.py` stores selected zones by participant identity for the active game.
5. Existing player score updates continue to increment `game_session:{pin}:player_scores` by participant key.
6. Saved results persist player-to-zone data alongside `player_scores` and `custom_field_data`.
7. The result detail data path makes saved zone data available to `frontend/src/routes/results/[result_id]/+page.svelte` and `PlayerOverview`.
8. `PlayerOverview` continues to render individual player rows with scores and correct counts.
9. The result detail page renders a zone totals table when saved zone data exists.
10. Historical results without zone data continue to load and show individual results.

## UX Requirements

The join page should add one required zone selector near the username and optional custom field step. It should not change the game PIN step or the overall join sequence.

Suggested label:

- `Zone`

Suggested options:

- `1구역`
- `2구역`
- `3구역`
- `4구역`
- `5구역`
- `6구역`
- `7구역`
- `8구역`
- `9구역`
- `10구역`
- `11구역`

The result detail page should place the zone totals table near the existing individual player overview. The table should include zone name and total score. If no saved zone data exists, the page should either omit the table or show a short empty state without blocking the individual result table.

## Data Model and Persistence

Add a participant zone value to the live join payload and persist it through the saved result path.

- Socket model: add a required `zone` field to `JoinGameData` in `classquiz/socket_server/models.py`.
- Live storage: store a participant-to-zone mapping for each game, for example in a Redis hash keyed by game PIN, separate from `game_session:{pin}:player_scores`.
- Saved results: add or otherwise persist a JSON player-to-zone mapping on `GameResults` in `classquiz/db/models.py`.
- Export helper: update `classquiz/socket_server/export_helpers.py` so saved results include the zone mapping captured during play.
- Result detail data: return the saved zone mapping with the existing result payload so the frontend can compute or display zone totals.

The saved mapping must use participant keys that match `player_scores` keys. This keeps player-level scoring unchanged while allowing zone totals to be computed later from persisted result data.

## Acceptance Criteria

- Participants cannot join until they choose one fixed zone from `1구역` through `11구역`.
- Joining a game sends the selected zone to the socket server with the existing join fields.
- Live gameplay, answer submission, individual score updates, and participant-keyed player score storage remain unchanged.
- Saving results persists the player-to-zone mapping for the saved players.
- The result detail page displays the existing individual result table and a zone totals table for results with zone data.
- Zone totals equal the sum of saved individual player scores for players in each zone.
- Results saved before this feature still display individual results and do not fail when zone data is missing.

## Implementation Notes

- Update `frontend/src/lib/play/join.svelte` to hold the selected zone and include it in each `join_game` emit path.
- Keep `frontend/src/routes/play/+page.svelte` focused on passing join state into `JoinGame`; only extend it if selected zone state needs to cross the page boundary.
- Update `classquiz/socket_server/models.py` with a fixed-zone validation rule for `JoinGameData`.
- Update `classquiz/socket_server/__init__.py` to store the selected zone by participant identity during `join_game`; do not change `player_scores` keys or score calculation.
- Update `classquiz/socket_server/export_helpers.py` to read the stored zone mapping when creating `GameResults`.
- Update `classquiz/db/models.py` to persist the saved player-to-zone mapping.
- Update `frontend/src/routes/results/[result_id]/+page.svelte` to pass saved zone data into `PlayerOverview` or a small adjacent totals component.
- Update `frontend/src/routes/results/[result_id]/player_overview.svelte` to keep the individual table and add zone total rendering when zone data exists.

## Verification

- Verify the join flow requires one of the fixed zone values and sends it with `join_game`.
- Verify invalid zone values are rejected by the socket payload model.
- Verify answering questions still updates `player_scores` by participant key and produces the same individual scores as before.
- Verify saving results writes player scores, custom field data, and player-to-zone data.
- Verify a saved result with zone data shows individual player results and correct zone total sums on the result detail page.
- Verify a historical result without zone data still opens and shows individual results without errors.
- Run frontend validation from `frontend/` after Svelte changes.
- Run backend validation through the repository test path, using `./run_tests.sh a` with required environment and services rather than plain `pytest` alone.
