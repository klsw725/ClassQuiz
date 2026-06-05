# SPDX-FileCopyrightText: 2026 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0

import uuid

import pytest
from pydantic import ValidationError

from classquiz.db.models import TextQuizAnswer
from classquiz.db.models import PlayGame, QuizQuestion, QuizQuestionType
from classquiz.socket_server.helpers import check_answer, check_multi_text_question, check_text_question
from classquiz.socket_server.models import SubmitAnswerData, SubmitAnswerDataOrderType


def make_text_game(
    answers: list[TextQuizAnswer],
    ignore_whitespace: bool = False,
    question_type: QuizQuestionType = QuizQuestionType.TEXT,
) -> PlayGame:
    return PlayGame(
        quiz_id=uuid.uuid4(),
        description="",
        user_id=uuid.uuid4(),
        title="",
        questions=[
            QuizQuestion(
                question="",
                time="20",
                type=question_type,
                answers=answers,
                ignore_whitespace=ignore_whitespace,
            )
        ],
        game_id=uuid.uuid4(),
        game_pin="123456",
    )


def test_text_answer_keeps_whitespace_significant_by_default():
    answers = [TextQuizAnswer(answer="대한민국", case_sensitive=False)]

    assert not check_text_question("대한 민국", answers)


def test_text_answer_can_ignore_whitespace():
    answers = [TextQuizAnswer(answer="대한민국", case_sensitive=False)]

    assert check_text_question("대 한 민 국", answers, ignore_whitespace=True)


def test_text_answer_ignores_whitespace_before_case_sensitive_compare():
    answers = [TextQuizAnswer(answer="Class Quiz", case_sensitive=True)]

    assert check_text_question("ClassQuiz", answers, ignore_whitespace=True)
    assert not check_text_question("classquiz", answers, ignore_whitespace=True)


def test_text_answer_accepts_multiple_answers_as_alternatives():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
    ]

    assert check_text_question("Beta", answers)


def test_check_answer_text_uses_single_answer_and_full_credit():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
    ]
    game = make_text_game(answers)
    data = SubmitAnswerData(
        question_index=0,
        answer="Beta",
        complex_answer=[SubmitAnswerDataOrderType(answer="wrong")],
    )

    right, answer, credit = check_answer(game, data)

    assert right
    assert answer == "Beta"
    assert credit == 1


def test_multi_text_answer_matches_required_answers_order_insensitively():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
        TextQuizAnswer(answer="gamma", case_sensitive=False),
    ]

    right, credit = check_multi_text_question(["gamma", "Alpha", "beta"], answers)

    assert right
    assert credit == 1


def test_multi_text_answer_awards_partial_credit_for_matched_required_answers():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
        TextQuizAnswer(answer="gamma", case_sensitive=False),
    ]

    right, credit = check_multi_text_question(["gamma", "wrong", "alpha"], answers)

    assert not right
    assert credit == 2 / 3


def test_multi_text_answer_uses_one_to_one_matching_for_duplicate_slots():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="alpha", case_sensitive=False),
    ]

    right, credit = check_multi_text_question(["alpha"], answers)

    assert not right
    assert credit == 0.5


def test_multi_text_answer_ignores_extra_submitted_guesses():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
    ]

    right, credit = check_multi_text_question(["wrong", "wrong", "alpha", "beta"], answers)

    assert not right
    assert credit == 0


def test_check_answer_multi_text_uses_complex_answer_and_returns_joined_submission():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
    ]
    game = make_text_game(answers, question_type=QuizQuestionType.MULTI_TEXT)
    data = SubmitAnswerData(
        question_index=0,
        answer="",
        complex_answer=[SubmitAnswerDataOrderType(answer="beta"), SubmitAnswerDataOrderType(answer="wrong")],
    )

    right, answer, credit = check_answer(game, data)

    assert not right
    assert answer == "beta, wrong"
    assert credit == 0.5


def test_check_answer_multi_text_bounds_extra_complex_answer_guesses():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
    ]
    game = make_text_game(answers, question_type=QuizQuestionType.MULTI_TEXT)
    data = SubmitAnswerData(
        question_index=0,
        answer="",
        complex_answer=[
            SubmitAnswerDataOrderType(answer="wrong"),
            SubmitAnswerDataOrderType(answer="wrong"),
            SubmitAnswerDataOrderType(answer="alpha"),
            SubmitAnswerDataOrderType(answer="beta"),
        ],
    )

    right, answer, credit = check_answer(game, data)

    assert not right
    assert answer == "wrong, wrong"
    assert credit == 0


def test_check_answer_multi_text_falls_back_to_single_answer():
    answers = [TextQuizAnswer(answer="alpha", case_sensitive=False)]
    game = make_text_game(answers, question_type=QuizQuestionType.MULTI_TEXT)
    data = SubmitAnswerData(question_index=0, answer="Alpha")

    right, answer, credit = check_answer(game, data)

    assert right
    assert answer == "Alpha"
    assert credit == 1


def test_submit_answer_data_bounds_text_payloads():
    with pytest.raises(ValidationError):
        SubmitAnswerData(question_index=0, answer="x" * 1001)

    with pytest.raises(ValidationError):
        SubmitAnswerData(
            question_index=0,
            complex_answer=[SubmitAnswerDataOrderType(answer="x" * 1001)],
        )

    with pytest.raises(ValidationError):
        SubmitAnswerData(
            question_index=0,
            complex_answer=[SubmitAnswerDataOrderType(answer="ok")] * 101,
        )
