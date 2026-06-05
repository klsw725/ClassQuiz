# SPDX-FileCopyrightText: 2026 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0

MAX_SCORE = 1000


def calculate_score(elapsed_ms: float, question_time_seconds: int, max_score: int = MAX_SCORE) -> int:
    question_time_ms = question_time_seconds * 1000
    result = (question_time_ms - elapsed_ms) / question_time_ms
    return int(result * max_score)


def calculate_answer_score(
    answer_right: bool | int | float,
    time_based_scoring: bool,
    elapsed_ms: float,
    question_time_seconds: int,
    max_score: int = MAX_SCORE,
) -> int:
    score_credit = float(answer_right)
    if score_credit == 0:
        return 0
    if not time_based_scoring:
        return int(max_score * score_credit)
    return int(min(calculate_score(elapsed_ms, question_time_seconds, max_score), max_score) * score_credit)
