# SPDX-FileCopyrightText: 2026 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0

from classquiz.scoring import MAX_SCORE, calculate_answer_score, calculate_score


def test_calculate_score_preserves_time_based_formula():
    assert calculate_score(0, 20) == MAX_SCORE
    assert calculate_score(10000, 20) == 500


def test_time_based_scoring_caps_fast_correct_answers():
    assert calculate_answer_score(True, True, -50, 20) == MAX_SCORE


def test_disabled_time_based_scoring_awards_fixed_score():
    assert calculate_answer_score(True, False, 15000, 20) == MAX_SCORE
    assert calculate_answer_score(True, False, 15000, 20, 500) == 500


def test_wrong_answers_score_zero_in_both_modes():
    assert calculate_answer_score(False, True, 0, 20) == 0
    assert calculate_answer_score(False, False, 0, 20) == 0


def test_time_based_scoring_uses_question_points():
    assert calculate_score(10000, 20, 500) == 250
    assert calculate_answer_score(True, True, 10000, 20, 500) == 250


def test_fixed_scoring_accepts_partial_credit():
    assert calculate_answer_score(0.5, False, 15000, 20, 500) == 250


def test_time_based_scoring_accepts_partial_credit():
    assert calculate_answer_score(0.5, True, 10000, 20, 500) == 125
