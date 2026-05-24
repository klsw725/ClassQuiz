# SPDX-FileCopyrightText: 2026 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0

import fnmatch
from datetime import datetime, timedelta
import uuid

import pytest

from classquiz.db.models import (
    ABCDQuizAnswer,
    AnswerData,
    AnswerDataList,
    GamePlayer,
    GameSession,
    PlayGame,
    QuizQuestion,
    User,
)
from classquiz.routers.remote import get_live_games
from classquiz.socket_server import register_as_admin
import classquiz.db.models as db_models
import classquiz.routers.remote as remote_router
import classquiz.socket_server as socket_server


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.hashes = {}
        self.sets = {}

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, ex=None):
        self.values[key] = value

    async def delete(self, key):
        self.values.pop(key, None)

    async def scan_iter(self, match):
        for key in self.values:
            if fnmatch.fnmatch(key, match):
                yield key

    async def hget(self, key, field):
        return self.hashes.get(key, {}).get(field)

    async def hset(self, key, field, value):
        self.hashes.setdefault(key, {})[field] = value

    async def expire(self, key, ex):
        return None

    async def hgetall(self, key):
        return self.hashes.get(key, {})

    async def smembers(self, key):
        return self.sets.get(key, set())

    async def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    async def srem(self, key, value):
        self.sets.setdefault(key, set()).discard(value)


class FakeManager:
    def __init__(self, sio):
        self.sio = sio

    def is_connected(self, sid, namespace):
        return namespace == "/" and sid in self.sio.active_sids


class FakeSio:
    def __init__(self):
        self.emitted = []
        self.entered_rooms = []
        self.left_rooms = []
        self.disconnected = []
        self.active_sids = set()
        self.rooms_by_sid = {}
        self.manager = FakeManager(self)

    async def emit(self, event, data=None, room=None):
        self.emitted.append((event, data, room))

    async def enter_room(self, sid, room):
        self.entered_rooms.append((sid, room))
        self.rooms_by_sid.setdefault(sid, set()).add(room)

    async def leave_room(self, sid, room):
        self.left_rooms.append((sid, room))
        self.rooms_by_sid.setdefault(sid, set()).discard(room)

    async def disconnect(self, sid, namespace=None):
        self.disconnected.append((sid, namespace))

    def rooms(self, sid, namespace=None):
        return list(self.rooms_by_sid.get(sid, set()))


def make_game(
    user_id,
    game_id=None,
    game_pin="123456",
    current_question=0,
    question_show=False,
    questions=None,
    started=True,
):
    return PlayGame(
        quiz_id=uuid.uuid4(),
        description="description",
        user_id=user_id,
        title="title",
        questions=[] if questions is None else questions,
        game_id=game_id or uuid.uuid4(),
        game_pin=game_pin,
        started=started,
        captcha_enabled=False,
        game_mode="live",
        current_question=current_question,
        question_show=question_show,
    )


@pytest.fixture
def recovery_context(monkeypatch):
    fake_redis = FakeRedis()
    fake_sio = FakeSio()
    sessions = {}

    async def fake_save_session(sid, sio, session):
        sessions[sid] = session

    async def fake_get_session(sid, sio):
        return sessions[sid]

    monkeypatch.setattr(socket_server, "redis", fake_redis)
    monkeypatch.setattr(socket_server, "sio", fake_sio)
    monkeypatch.setattr(socket_server, "save_session", fake_save_session)
    monkeypatch.setattr(socket_server, "get_session", fake_get_session)
    monkeypatch.setattr(remote_router, "redis", fake_redis)
    monkeypatch.setattr(db_models, "redis", fake_redis)
    return fake_redis, fake_sio, sessions


def add_registered_player(fake_redis, game_pin, username, sid, zone="1구역"):
    fake_redis.values[f"game_session:{game_pin}:players:{username}"] = sid
    fake_redis.sets.setdefault(f"game_session:{game_pin}:players", set()).add(
        GamePlayer(username=username, sid=sid).model_dump_json()
    )
    fake_redis.hashes.setdefault(f"game:{game_pin}:players:zones", {})[username] = zone


def activate_player(fake_sio, sid, game_pin):
    fake_sio.active_sids.add(sid)
    fake_sio.rooms_by_sid.setdefault(sid, set()).add(game_pin)


@pytest.mark.asyncio
async def test_cookie_rejoin_rejects_active_old_sid(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    game = make_game(uuid.uuid4())
    fake_redis.values["game:123456"] = game.model_dump_json()
    add_registered_player(fake_redis, "123456", "alice", "old-sid")
    activate_player(fake_sio, "old-sid", "123456")

    await socket_server.rejoin_game(
        "new-sid",
        {"game_pin": "123456", "username": "alice", "old_sid": "old-sid"},
    )

    assert ("participant_already_connected", None, "new-sid") in fake_sio.emitted
    assert fake_redis.values["game_session:123456:players:alice"] == "old-sid"
    assert "new-sid" not in sessions


@pytest.mark.asyncio
async def test_cookie_rejoin_rejects_stale_sid_key_without_set_membership(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    game = make_game(uuid.uuid4())
    fake_redis.values["game:123456"] = game.model_dump_json()
    fake_redis.values["game_session:123456:players:alice"] = "old-sid"

    await socket_server.rejoin_game(
        "new-sid",
        {"game_pin": "123456", "username": "alice", "old_sid": "old-sid"},
    )

    assert all(event != "rejoined_game" for event, _data, _room in fake_sio.emitted)
    assert fake_redis.values["game_session:123456:players:alice"] == "old-sid"
    assert "new-sid" not in sessions


@pytest.mark.asyncio
async def test_started_game_fallback_restores_inactive_registered_player_with_matching_zone(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    game = make_game(uuid.uuid4(), started=True)
    fake_redis.values["game:123456"] = game.model_dump_json()
    add_registered_player(fake_redis, "123456", "alice", "old-sid", zone="2구역")

    await socket_server.join_game(
        "new-sid",
        {
            "game_pin": "123456",
            "username": "alice",
            "zone": "2구역",
            "captcha": None,
            "custom_field": "",
        },
    )

    players = fake_redis.sets["game_session:123456:players"]
    assert fake_redis.values["game_session:123456:players:alice"] == "new-sid"
    assert GamePlayer(username="alice", sid="old-sid").model_dump_json() not in players
    assert GamePlayer(username="alice", sid="new-sid").model_dump_json() in players
    assert sessions["new-sid"] == {
        "game_pin": "123456",
        "username": "alice",
        "sid_custom": "new-sid",
        "admin": False,
        "zone": "2구역",
    }
    assert ("new-sid", "123456") in fake_sio.entered_rooms
    assert any(event == "rejoined_game" and room == "new-sid" for event, _data, room in fake_sio.emitted)
    assert any(event == "time_sync" and room == "new-sid" for event, _data, room in fake_sio.emitted)
    assert all(event != "joined_game" for event, _data, _room in fake_sio.emitted)


@pytest.mark.asyncio
async def test_rejoin_active_question_restores_question_payload(recovery_context):
    fake_redis, fake_sio, _sessions = recovery_context
    question = QuizQuestion(
        question="Question",
        time="30",
        answers=[ABCDQuizAnswer(answer="A", right=True), ABCDQuizAnswer(answer="B")],
    )
    game = make_game(uuid.uuid4(), question_show=True, questions=[question])
    fake_redis.values["game:123456"] = game.model_dump_json()
    fake_redis.values["game:123456:current_time"] = (datetime.now() - timedelta(seconds=5)).isoformat()
    add_registered_player(fake_redis, "123456", "alice", "old-sid")

    await socket_server.rejoin_game(
        "new-sid",
        {"game_pin": "123456", "username": "alice", "old_sid": "old-sid"},
    )

    question_events = [
        data
        for event, data, room in fake_sio.emitted
        if event == "set_question_number" and room == "new-sid"
    ]
    assert len(question_events) == 1
    assert question_events[0]["question_index"] == 0
    assert question_events[0]["question"]["question"] == "Question"
    assert 20 <= int(question_events[0]["question"]["time"]) <= 30


@pytest.mark.asyncio
async def test_started_game_fallback_rejects_active_old_sid(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    game = make_game(uuid.uuid4(), started=True)
    fake_redis.values["game:123456"] = game.model_dump_json()
    add_registered_player(fake_redis, "123456", "alice", "old-sid")
    activate_player(fake_sio, "old-sid", "123456")

    await socket_server.join_game(
        "new-sid",
        {
            "game_pin": "123456",
            "username": "alice",
            "zone": "1구역",
            "captcha": None,
            "custom_field": "",
        },
    )

    assert ("participant_already_connected", None, "new-sid") in fake_sio.emitted
    assert fake_redis.values["game_session:123456:players:alice"] == "old-sid"
    assert "new-sid" not in sessions


@pytest.mark.asyncio
async def test_kicked_player_cannot_started_game_fallback(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    game = make_game(uuid.uuid4(), started=True)
    fake_redis.values["game:123456"] = game.model_dump_json()
    add_registered_player(fake_redis, "123456", "alice", "old-sid")
    sessions["admin-sid"] = {"game_pin": "123456", "admin": True}

    await socket_server.kick_player("admin-sid", {"username": "alice"})
    await socket_server.join_game(
        "new-sid",
        {
            "game_pin": "123456",
            "username": "alice",
            "zone": "1구역",
            "captcha": None,
            "custom_field": "",
        },
    )

    assert "game_session:123456:players:alice" not in fake_redis.values
    assert GamePlayer(username="alice", sid="old-sid").model_dump_json() not in fake_redis.sets[
        "game_session:123456:players"
    ]
    assert ("old-sid", "123456") in fake_sio.left_rooms
    assert ("kick", None, "old-sid") in fake_sio.emitted
    assert ("game_already_started", None, "new-sid") in fake_sio.emitted
    assert "new-sid" not in sessions


@pytest.mark.asyncio
async def test_register_as_admin_resume_replaces_admin_sid_and_hydrates_state(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    user_id = uuid.uuid4()
    game_id = uuid.uuid4()
    game = make_game(user_id, game_id=game_id)
    fake_redis.values["game:123456"] = game.model_dump_json()
    fake_redis.values["game_session:123456"] = GameSession(
        admin="old-admin", game_id=str(game_id), answers=[]
    ).model_dump_json()
    fake_redis.sets["game_session:123456:players"] = {
        GamePlayer(username="alice", sid="alice-sid").model_dump_json()
    }
    fake_redis.hashes["game:123456:players:zones"] = {"alice": "1구역"}
    fake_redis.hashes["game_session:123456:player_scores"] = {"alice": "100"}
    fake_redis.values["game_session:123456:0"] = AnswerDataList(
        [AnswerData(username="alice", answer="A", right=True, time_taken=100.0, score=100)]
    ).model_dump_json()

    await register_as_admin(
        "new-admin",
        {"game_pin": "123456", "game_id": str(game_id), "resume": True},
    )

    saved_session = GameSession.model_validate_json(fake_redis.values["game_session:123456"])
    assert saved_session.admin == "new-admin"
    assert fake_redis.hashes["game_session:123456:player_scores"] == {"alice": "100"}
    registered_payload = next(
        data for event, data, _room in fake_sio.emitted if event == "registered_as_admin"
    )
    assert registered_payload["players"] == [
        {"username": "alice", "sid": "alice-sid", "zone": "1구역"}
    ]
    assert registered_payload["player_scores"] == {"alice": 0}
    assert registered_payload["selected_question"] == 0
    assert registered_payload["answer_count"] == 1
    assert registered_payload["timer_res"] == "0"
    assert registered_payload["question_results"] is not None
    assert sessions["new-admin"] == {"game_pin": "123456", "admin": True, "remote": False}
    assert ("old-admin", "/") in fake_sio.disconnected
    assert ("new-admin", "123456") in fake_sio.entered_rooms
    assert ("new-admin", "admin:123456") in fake_sio.entered_rooms


@pytest.mark.asyncio
async def test_register_as_admin_existing_session_without_resume_still_rejects(recovery_context):
    fake_redis, fake_sio, _sessions = recovery_context
    user_id = uuid.uuid4()
    game_id = uuid.uuid4()
    fake_redis.values["game:123456"] = make_game(user_id, game_id=game_id).model_dump_json()
    fake_redis.values["game_session:123456"] = GameSession(
        admin="old-admin", game_id=str(game_id), answers=[]
    ).model_dump_json()

    await register_as_admin("new-admin", {"game_pin": "123456", "game_id": str(game_id)})

    assert ("already_registered_as_admin", None, "new-admin") in fake_sio.emitted
    saved_session = GameSession.model_validate_json(fake_redis.values["game_session:123456"])
    assert saved_session.admin == "old-admin"


@pytest.mark.asyncio
async def test_register_as_admin_resume_wrong_game_id_rejects(recovery_context):
    fake_redis, fake_sio, _sessions = recovery_context
    user_id = uuid.uuid4()
    actual_game_id = uuid.uuid4()
    fake_redis.values["game:123456"] = make_game(user_id, game_id=actual_game_id).model_dump_json()

    await register_as_admin(
        "new-admin",
        {"game_pin": "123456", "game_id": str(uuid.uuid4()), "resume": True},
    )

    assert ("game_not_found", None, "new-admin") in fake_sio.emitted


@pytest.mark.asyncio
async def test_register_as_admin_resume_active_question_uses_remaining_time(recovery_context):
    fake_redis, fake_sio, _sessions = recovery_context
    user_id = uuid.uuid4()
    game_id = uuid.uuid4()
    question = QuizQuestion(
        question="Question",
        time="30",
        answers=[ABCDQuizAnswer(answer="A", right=True)],
    )
    game = make_game(
        user_id,
        game_id=game_id,
        question_show=True,
        questions=[question],
    )
    fake_redis.values["game:123456"] = game.model_dump_json()
    fake_redis.values["game_session:123456"] = GameSession(
        admin="old-admin", game_id=str(game_id), answers=[]
    ).model_dump_json()
    fake_redis.values["game:123456:current_time"] = (datetime.now() - timedelta(seconds=5)).isoformat()

    await register_as_admin(
        "new-admin",
        {"game_pin": "123456", "game_id": str(game_id), "resume": True},
    )

    registered_payload = next(
        data for event, data, _room in fake_sio.emitted if event == "registered_as_admin"
    )
    assert registered_payload["question_results"] is None
    assert 20 <= int(registered_payload["timer_res"]) <= 30


@pytest.mark.asyncio
async def test_live_games_lists_only_owned_games_with_sessions(recovery_context):
    fake_redis, _fake_sio, _sessions = recovery_context
    user_id = uuid.uuid4()
    game_id = uuid.uuid4()
    owned_game = make_game(user_id, game_id=game_id, game_pin="123456")
    lobby_game = make_game(user_id, game_pin="222222")
    missing_game = make_game(user_id, game_pin="444444")
    other_user_game = make_game(uuid.uuid4(), game_pin="333333")
    fake_redis.values[f"game_pin:{user_id}:{owned_game.quiz_id}"] = "123456"
    fake_redis.values[f"game_pin:{user_id}:{lobby_game.quiz_id}"] = "222222"
    fake_redis.values[f"game_pin:{user_id}:{missing_game.quiz_id}"] = "444444"
    fake_redis.values[f"game_pin:{user_id}:{other_user_game.quiz_id}"] = "333333"
    fake_redis.values["game:123456"] = owned_game.model_dump_json()
    fake_redis.values["game_session:123456"] = GameSession(
        admin="old-admin", game_id=str(game_id), answers=[]
    ).model_dump_json()
    fake_redis.values["game:222222"] = lobby_game.model_dump_json()
    fake_redis.values["game:333333"] = other_user_game.model_dump_json()
    fake_redis.values["game_session:333333"] = GameSession(
        admin="old-admin", game_id=str(other_user_game.game_id), answers=[]
    ).model_dump_json()

    live_games = await get_live_games(
        user=User(id=user_id, email="user@example.com", username="user", avatar=b"")
    )

    assert live_games == [
        {
            "game_pin": "123456",
            "game_id": str(game_id),
            "quiz_id": str(owned_game.quiz_id),
            "title": "title",
            "current_question": 0,
            "question_count": 0,
            "started": True,
            "resume_url": f"/admin?token={game_id}&pin=123456&connect=1&resume=1",
        },
        {
            "game_pin": "222222",
            "game_id": str(lobby_game.game_id),
            "quiz_id": str(lobby_game.quiz_id),
            "title": "title",
            "current_question": 0,
            "question_count": 0,
            "started": True,
            "resume_url": f"/admin?token={lobby_game.game_id}&pin=222222&connect=1&resume=1",
        },
    ]
