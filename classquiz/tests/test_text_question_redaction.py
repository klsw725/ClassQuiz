# SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0

import uuid
from collections.abc import Callable
from typing import cast

import pytest

from classquiz.db.models import PlayGame, QuizQuestion, QuizQuestionType, TextQuizAnswer
from classquiz.routers import quiz
from classquiz.routers import solo
import classquiz.socket_server as socket_server

build_return_question = cast(
    Callable[[PlayGame, int], tuple[dict[str, object], list[int]]],
    getattr(socket_server, "build_return_question"),
)
safe_question = cast(Callable[[PlayGame, int], dict[str, object]], getattr(solo, "_safe_question"))
solution_question = cast(Callable[[QuizQuestion], dict[str, object]], getattr(solo, "_solution_question"))
practice_question = cast(Callable[[QuizQuestion], QuizQuestion], getattr(quiz, "practice_question"))


def make_text_game(question_type: QuizQuestionType = QuizQuestionType.MULTI_TEXT) -> PlayGame:
    return PlayGame(
        quiz_id=uuid.uuid4(),
        description="",
        user_id=uuid.uuid4(),
        title="",
        questions=[
            QuizQuestion(
                question="Text question",
                time="20",
                type=question_type,
                answers=[
                    TextQuizAnswer(answer="secret one", case_sensitive=False),
                    TextQuizAnswer(answer="secret two", case_sensitive=True),
                ],
            )
        ],
        game_id=uuid.uuid4(),
        game_pin="123456",
    )


def test_live_multi_text_question_payload_redacts_answer_text_but_keeps_field_count():
    question, answer_order = build_return_question(make_text_game(), 0)

    assert answer_order == [0, 1]
    assert question["answers"] == [
        {"answer": "", "case_sensitive": False},
        {"answer": "", "case_sensitive": False},
    ]
    assert "secret one" not in str(question)
    assert "secret two" not in str(question)


def test_solo_multi_text_question_payload_redacts_answer_text_but_keeps_field_count():
    question = safe_question(make_text_game(), 0)

    assert question["answers"] == [
        {"answer": "", "case_sensitive": False},
        {"answer": "", "case_sensitive": False},
    ]
    assert "secret one" not in str(question)
    assert "secret two" not in str(question)


def test_solo_multi_text_solution_payload_exposes_answer_text():
    question = solution_question(make_text_game().questions[0])

    answers = question["answers"]
    assert isinstance(answers, list)
    assert [a["answer"] for a in answers] == ["secret one", "secret two"]


@pytest.mark.asyncio
async def test_live_multi_text_solution_payload_exposes_answer_text(monkeypatch):
    emitted: list[tuple[str, object, str | None]] = []
    game = make_text_game()
    game.current_question = 0

    async def fake_get_session(_sid, _sio):
        return {"admin": True, "game_pin": game.game_pin}

    async def fake_get_from_redis(_game_pin):
        return game

    async def fake_emit(event, data=None, room=None):
        emitted.append((event, data, room))

    monkeypatch.setattr(socket_server, "get_session", fake_get_session)
    monkeypatch.setattr(socket_server.PlayGame, "get_from_redis", fake_get_from_redis)
    monkeypatch.setattr(socket_server.sio, "emit", fake_emit)

    await socket_server.show_solutions("admin-sid", {})

    assert len(emitted) == 1
    event, payload, room = emitted[0]
    assert event == "solutions"
    assert room == game.game_pin
    assert payload["type"] == QuizQuestionType.MULTI_TEXT
    assert [a["answer"] for a in payload["answers"]] == ["secret one", "secret two"]


def test_solo_text_solution_payload_keeps_answer_text():
    question = solution_question(make_text_game(QuizQuestionType.TEXT).questions[0])

    assert question["answers"] == [
        {"answer": "secret one", "case_sensitive": False},
        {"answer": "secret two", "case_sensitive": True},
    ]


def test_practice_multi_text_question_redacts_answer_text_but_keeps_field_count():
    question = practice_question(make_text_game().questions[0])

    assert question.answers == [
        TextQuizAnswer(answer="", case_sensitive=False),
        TextQuizAnswer(answer="", case_sensitive=False),
    ]
    assert "secret one" not in question.model_dump_json()
    assert "secret two" not in question.model_dump_json()


def test_practice_text_question_keeps_answer_text():
    question = practice_question(make_text_game(QuizQuestionType.TEXT).questions[0])

    assert question.answers == [
        TextQuizAnswer(answer="secret one", case_sensitive=False),
        TextQuizAnswer(answer="secret two", case_sensitive=True),
    ]
