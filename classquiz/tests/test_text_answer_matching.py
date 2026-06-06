# SPDX-FileCopyrightText: 2026 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0

import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from classquiz.db.models import AnswerData, AnswerDataList, TextAnswerDetail, TextQuizAnswer
from classquiz.db.models import PlayGame, QuizQuestion, QuizQuestionType
from classquiz.routers import solo
from classquiz.scoring import calculate_answer_score
from classquiz.socket_server.helpers import (
    build_multi_text_answer_details,
    check_answer,
    check_multi_text_question,
    check_text_question,
)
from classquiz.socket_server.models import SubmitAnswerData, SubmitAnswerDataOrderType


def make_text_game(
    answers: list[TextQuizAnswer],
    ignore_whitespace: bool = False,
    question_type: QuizQuestionType = QuizQuestionType.TEXT,
    multi_text_order_sensitive: bool = False,
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
                multi_text_order_sensitive=multi_text_order_sensitive,
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


def test_multi_text_question_order_sensitive_defaults_to_false():
    answers = [TextQuizAnswer(answer="alpha", case_sensitive=False)]

    game = make_text_game(answers, question_type=QuizQuestionType.MULTI_TEXT)

    assert not game.questions[0].multi_text_order_sensitive


def test_multi_text_answer_can_require_matching_slot_order():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
        TextQuizAnswer(answer="gamma", case_sensitive=False),
    ]

    right, credit = check_multi_text_question(
        ["gamma", "Alpha", "beta"],
        answers,
        order_sensitive=True,
    )

    assert not right
    assert credit == 0


def test_multi_text_answer_order_sensitive_awards_matching_slots_only():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
        TextQuizAnswer(answer="gamma", case_sensitive=False),
    ]

    right, credit = check_multi_text_question(
        ["alpha", "wrong", "Gamma"],
        answers,
        order_sensitive=True,
    )

    assert not right
    assert credit == 2 / 3


def test_multi_text_answer_order_sensitive_still_respects_text_matching_options():
    answers = [
        TextQuizAnswer(answer="Class Quiz", case_sensitive=True),
        TextQuizAnswer(answer="대한민국", case_sensitive=False),
    ]

    right, credit = check_multi_text_question(
        ["ClassQuiz", "대 한 민 국"],
        answers,
        ignore_whitespace=True,
        order_sensitive=True,
    )

    assert right
    assert credit == 1


def test_multi_text_answer_feedback_marks_each_partial_submission():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
        TextQuizAnswer(answer="gamma", case_sensitive=False),
    ]

    answer_details = build_multi_text_answer_details(["gamma", "wrong", "alpha"], answers)

    assert [detail.model_dump() for detail in answer_details] == [
        {"answer": "gamma", "matched": True},
        {"answer": "wrong", "matched": False},
        {"answer": "alpha", "matched": True},
    ]


def test_multi_text_answer_feedback_marks_all_wrong_submissions_false():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
    ]

    answer_details = build_multi_text_answer_details(["wrong", "still wrong"], answers)

    assert [detail.matched for detail in answer_details] == [False, False]


def test_multi_text_answer_feedback_uses_one_to_one_matching_for_duplicate_submissions():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
    ]

    answer_details = build_multi_text_answer_details(["alpha", "alpha"], answers)

    assert [detail.model_dump() for detail in answer_details] == [
        {"answer": "alpha", "matched": True},
        {"answer": "alpha", "matched": False},
    ]


def test_multi_text_answer_feedback_truncates_extra_submissions_to_required_count():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
    ]

    answer_details = build_multi_text_answer_details(["alpha", "beta", "extra"], answers)

    assert [detail.model_dump() for detail in answer_details] == [
        {"answer": "alpha", "matched": True},
        {"answer": "beta", "matched": True},
    ]


def test_multi_text_answer_feedback_preserves_submissions_without_configured_answers():
    answer_details = build_multi_text_answer_details(["alpha"], [])

    assert [detail.model_dump() for detail in answer_details] == [
        {"answer": "alpha", "matched": False},
    ]


def test_multi_text_answer_feedback_can_require_matching_slot_order():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
    ]

    answer_details = build_multi_text_answer_details(
        ["beta", "alpha"],
        answers,
        order_sensitive=True,
    )

    assert [detail.model_dump() for detail in answer_details] == [
        {"answer": "beta", "matched": False},
        {"answer": "alpha", "matched": False},
    ]


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


def test_check_answer_multi_text_respects_order_sensitive_question_option():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
    ]
    game = make_text_game(
        answers,
        question_type=QuizQuestionType.MULTI_TEXT,
        multi_text_order_sensitive=True,
    )
    data = SubmitAnswerData(
        question_index=0,
        answer="",
        complex_answer=[SubmitAnswerDataOrderType(answer="beta"), SubmitAnswerDataOrderType(answer="alpha")],
    )

    right, answer, credit = check_answer(game, data)

    assert not right
    assert answer == "beta, alpha"
    assert credit == 0


def test_check_answer_multi_text_awards_order_sensitive_partial_credit():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
        TextQuizAnswer(answer="gamma", case_sensitive=False),
    ]
    game = make_text_game(
        answers,
        question_type=QuizQuestionType.MULTI_TEXT,
        multi_text_order_sensitive=True,
    )
    data = SubmitAnswerData(
        question_index=0,
        answer="",
        complex_answer=[
            SubmitAnswerDataOrderType(answer="alpha"),
            SubmitAnswerDataOrderType(answer="wrong"),
            SubmitAnswerDataOrderType(answer="Gamma"),
        ],
    )

    right, answer, credit = check_answer(game, data)

    assert not right
    assert answer == "alpha, wrong, Gamma"
    assert credit == 2 / 3


def test_live_multi_text_ordered_partial_credit_answer_data_serializes_details():
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
        TextQuizAnswer(answer="gamma", case_sensitive=False),
    ]
    game = make_text_game(
        answers,
        question_type=QuizQuestionType.MULTI_TEXT,
        multi_text_order_sensitive=True,
    )
    game.time_based_scoring = False
    data = SubmitAnswerData(
        question_index=0,
        answer="",
        complex_answer=[
            SubmitAnswerDataOrderType(answer="alpha"),
            SubmitAnswerDataOrderType(answer="wrong"),
            SubmitAnswerDataOrderType(answer="Gamma"),
        ],
    )

    answer_right, answer, score_credit = check_answer(game, data)
    score = calculate_answer_score(
        score_credit,
        game.time_based_scoring,
        0,
        int(float(game.questions[0].time)),
        game.questions[0].points,
    )
    answer_details = build_multi_text_answer_details(
        [item.answer for item in data.complex_answer or []],
        answers,
        game.questions[0].ignore_whitespace,
        game.questions[0].multi_text_order_sensitive,
    )
    answer_data = AnswerData(
        username="Player",
        answer=answer,
        right=answer_right,
        time_taken=0,
        score=score,
        zone="1구역",
        answer_details=answer_details,
    )

    serialized_answers = AnswerDataList.model_validate_json(
        AnswerDataList([answer_data]).model_dump_json()
    )

    assert not serialized_answers.root[0].right
    assert serialized_answers.root[0].score > 0
    assert serialized_answers.root[0].answer_details == [
        TextAnswerDetail(answer="alpha", matched=True),
        TextAnswerDetail(answer="wrong", matched=False),
        TextAnswerDetail(answer="Gamma", matched=True),
    ]


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


def test_check_answer_multi_text_preserves_submission_without_configured_answers():
    question = QuizQuestion.model_construct(
        question="",
        time="20",
        points=1000,
        type=QuizQuestionType.MULTI_TEXT,
        answers=[],
        ignore_whitespace=False,
        multi_text_order_sensitive=False,
    )
    game = PlayGame.model_construct(
        quiz_id=uuid.uuid4(),
        description="",
        user_id=uuid.uuid4(),
        title="",
        questions=[question],
        game_id=uuid.uuid4(),
        game_pin="123456",
    )
    data = SubmitAnswerData(
        question_index=0,
        complex_answer=[SubmitAnswerDataOrderType(answer="alpha")],
    )

    right, answer, credit = check_answer(game, data)

    assert not right
    assert answer == "alpha"
    assert credit == 0


@pytest.mark.asyncio
async def test_solo_submit_attempt_returns_answer_details_for_multi_text(monkeypatch):
    answers = [
        TextQuizAnswer(answer="alpha", case_sensitive=False),
        TextQuizAnswer(answer="beta", case_sensitive=False),
    ]
    game = make_text_game(answers, question_type=QuizQuestionType.MULTI_TEXT)
    game.questions[0].hide_results = False
    attempt = solo.SoloAttempt(
        game_pin="123456",
        username="Player",
        zone="1구역",
        question_started_at=datetime.now(),
    )

    async def fake_get_attempt(_attempt_id: str):
        return attempt

    async def fake_get_solo_game(_game_pin: str):
        return game

    async def fake_save_attempt(_attempt_id: str, _attempt: solo.SoloAttempt):
        return None

    monkeypatch.setattr(solo, "_get_attempt", fake_get_attempt)
    monkeypatch.setattr(solo, "_get_solo_game", fake_get_solo_game)
    monkeypatch.setattr(solo, "_save_attempt", fake_save_attempt)
    monkeypatch.setattr(solo, "calculate_answer_score", lambda *args, **kwargs: 42)

    response = await solo.submit_attempt(
        "attempt-id",
        solo.SubmitSoloAttemptRequest(
            question_index=0,
            complex_answer=[
                SubmitAnswerDataOrderType(answer="beta"),
                SubmitAnswerDataOrderType(answer="wrong"),
                SubmitAnswerDataOrderType(answer="alpha"),
            ],
        ),
    )

    assert response.answer_details == [
        TextAnswerDetail(answer="beta", matched=True),
        TextAnswerDetail(answer="wrong", matched=False),
    ]
    assert attempt.answers[0].answer_details == response.answer_details
    assert response.solution is not None
    assert response.solution["answers"] == [
        {"answer": "", "case_sensitive": False},
        {"answer": "", "case_sensitive": False},
    ]


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
