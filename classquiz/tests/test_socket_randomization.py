# SPDX-FileCopyrightText: 2026 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0

import json
import uuid

import pytest

import classquiz.routers.live as live_router
import classquiz.socket_server as socket_server
from classquiz.db.models import ABCDQuizAnswer, GamePlayer, PlayGame, QuizQuestion, QuizQuestionType
from classquiz.socket_server import remap_player_randomized_check_answer, set_question_number
from classquiz.socket_server.models import SubmitAnswerData
from classquiz.socket_server.participant_identity import participant_key


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.sets = {}
        self.set_calls = []

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, ex=None):
        self.values[key] = value
        self.set_calls.append((key, value, ex))

    async def smembers(self, key):
        return self.sets.get(key, set())


class FakeSio:
    def __init__(self):
        self.emitted = []

    async def emit(self, event, data=None, room=None):
        self.emitted.append((event, data, room))


def make_answer(label: str, right: bool = False):
    return ABCDQuizAnswer(answer=label, right=right)


def make_game(question_type=QuizQuestionType.ABCD):
    return PlayGame(
        quiz_id=uuid.uuid4(),
        description="description",
        user_id=uuid.uuid4(),
        title="title",
        questions=[
            QuizQuestion(
                question="question",
                time="30",
                points=1000,
                type=question_type,
                answers=[make_answer("A", True), make_answer("B"), make_answer("C", True)],
            )
        ],
        game_id=uuid.uuid4(),
        game_pin="123456",
        started=True,
        captcha_enabled=False,
        game_mode="live",
        randomize_answers=True,
        randomize_answers_mode="per_participant",
    )


@pytest.fixture
def randomization_context(monkeypatch):
    fake_redis = FakeRedis()
    fake_sio = FakeSio()

    async def fake_get_session(_sid, _sio):
        return {"game_pin": "123456", "admin": True}

    monkeypatch.setattr(socket_server, "redis", fake_redis)
    monkeypatch.setattr(socket_server, "sio", fake_sio)
    monkeypatch.setattr(socket_server, "get_session", fake_get_session)
    return fake_redis, fake_sio


@pytest.mark.asyncio
async def test_per_participant_randomization_emits_distinct_player_questions(randomization_context, monkeypatch):
    fake_redis, fake_sio = randomization_context
    fake_redis.values["game:123456"] = make_game().model_dump_json()
    fake_redis.sets["game_session:123456:players"] = {
        GamePlayer(username="alice", sid="alice-sid", zone="1구역").model_dump_json(),
        GamePlayer(username="bob", sid="bob-sid", zone="2구역").model_dump_json(),
    }
    shuffle_calls = 0

    def fake_shuffle(items):
        nonlocal shuffle_calls
        shuffle_calls += 1
        if shuffle_calls == 1:
            items.reverse()
        else:
            items.append(items.pop(0))

    monkeypatch.setattr(socket_server.random, "shuffle", fake_shuffle)

    await set_question_number("admin-sid", "0")

    admin_events = [event for event in fake_sio.emitted if event[2] == "admin:123456"]
    player_events = [event for event in fake_sio.emitted if event[2] in {"alice-sid", "bob-sid"}]
    game_room_events = [event for event in fake_sio.emitted if event[2] == "123456"]

    assert admin_events == [("set_question_number", {"question_index": 0}, "admin:123456")]
    assert len(player_events) == 2
    assert game_room_events == []
    answer_orders = [
        [answer["answer"] for answer in event[1]["question"]["answers"]]
        for event in player_events
    ]
    assert answer_orders[0] != answer_orders[1]


@pytest.mark.asyncio
async def test_per_participant_check_answer_remaps_display_indexes(randomization_context):
    fake_redis, _fake_sio = randomization_context
    fake_redis.values[f"game_session:123456:answer_order:0:{participant_key('alice', '1구역')}"] = json.dumps([2, 0, 1])
    data = SubmitAnswerData(question_index=0, answer="01")

    await remap_player_randomized_check_answer("123456", "alice", "1구역", data)

    assert data.answer == "02"


@pytest.mark.asyncio
async def test_live_api_per_participant_randomization_emits_player_questions(randomization_context, monkeypatch):
    fake_redis, fake_sio = randomization_context
    game = make_game()
    fake_redis.values["game:123456"] = game.model_dump_json()
    fake_redis.sets["game_session:123456:players"] = {
        GamePlayer(username="alice", sid="alice-sid", zone="1구역").model_dump_json(),
        GamePlayer(username="bob", sid="bob-sid", zone="2구역").model_dump_json(),
    }
    shuffle_calls = 0

    async def fake_check_api_key(_api_key):
        return game.user_id

    def fake_shuffle(items):
        nonlocal shuffle_calls
        shuffle_calls += 1
        if shuffle_calls == 1:
            items.reverse()
        else:
            items.append(items.pop(0))

    monkeypatch.setattr(live_router, "redis", fake_redis)
    monkeypatch.setattr(live_router, "sio", fake_sio)
    monkeypatch.setattr(live_router, "check_api_key", fake_check_api_key)
    monkeypatch.setattr(socket_server.random, "shuffle", fake_shuffle)

    await live_router.set_next_question("123456", 0, "api-key")

    admin_events = [event for event in fake_sio.emitted if event[2] == "admin:123456"]
    player_events = [event for event in fake_sio.emitted if event[2] in {"alice-sid", "bob-sid"}]
    game_room_events = [event for event in fake_sio.emitted if event[2] == "123456"]

    assert admin_events == [("set_question_number", {"question_index": 0}, "admin:123456")]
    assert len(player_events) == 2
    assert game_room_events == []
    assert "game:123456:current_time" in fake_redis.values
