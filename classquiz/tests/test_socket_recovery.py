# SPDX-FileCopyrightText: 2026 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0

import fnmatch
from datetime import datetime, timedelta
import uuid

import pytest

from classquiz.db.models import (
    ABCDQuizAnswer,
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
from classquiz.socket_server.participant_identity import participant_key


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

    async def hdel(self, key, field):
        self.hashes.setdefault(key, {}).pop(field, None)

    async def hincrby(self, key, field, amount):
        self.hashes.setdefault(key, {})[field] = str(int(self.hashes.setdefault(key, {}).get(field, 0)) + amount)

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

    async def scard(self, key):
        return len(self.sets.get(key, set()))


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
    key = participant_key(username, zone)
    fake_redis.values[f"game_session:{game_pin}:players:{key}"] = sid
    fake_redis.sets.setdefault(f"game_session:{game_pin}:players", set()).add(
        GamePlayer(username=username, sid=sid, zone=zone).model_dump_json()
    )
    fake_redis.hashes.setdefault(f"game:{game_pin}:players:zones", {})[key] = zone


def activate_player(fake_sio, sid, game_pin):
    fake_sio.active_sids.add(sid)
    fake_sio.rooms_by_sid.setdefault(sid, set()).add(game_pin)


@pytest.mark.asyncio
async def test_same_username_different_zones_can_join_before_start(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    game = make_game(uuid.uuid4(), started=False)
    fake_redis.values["game:123456"] = game.model_dump_json()

    for sid, zone in [("sid-zone-1", "1구역"), ("sid-zone-2", "2구역")]:
        await socket_server.join_game(
            sid,
            {
                "game_pin": "123456",
                "username": "alice",
                "zone": zone,
                "captcha": None,
                "custom_field": "",
            },
        )

    assert fake_redis.values[f"game_session:123456:players:{participant_key('alice', '1구역')}"] == "sid-zone-1"
    assert fake_redis.values[f"game_session:123456:players:{participant_key('alice', '2구역')}"] == "sid-zone-2"
    assert GamePlayer(username="alice", sid="sid-zone-1", zone="1구역").model_dump_json() in fake_redis.sets[
        "game_session:123456:players"
    ]
    assert GamePlayer(username="alice", sid="sid-zone-2", zone="2구역").model_dump_json() in fake_redis.sets[
        "game_session:123456:players"
    ]
    assert sessions["sid-zone-1"]["zone"] == "1구역"
    assert sessions["sid-zone-2"]["zone"] == "2구역"
    assert len([event for event, _data, _room in fake_sio.emitted if event == "joined_game"]) == 2


@pytest.mark.asyncio
async def test_same_username_same_zone_is_rejected_before_start(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    game = make_game(uuid.uuid4(), started=False)
    fake_redis.values["game:123456"] = game.model_dump_json()
    add_registered_player(fake_redis, "123456", "alice", "old-sid", zone="1구역")

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

    assert ("username_already_exists", None, "new-sid") in fake_sio.emitted
    assert "new-sid" not in sessions


@pytest.mark.asyncio
async def test_cookie_rejoin_rejects_active_old_sid(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    game = make_game(uuid.uuid4())
    fake_redis.values["game:123456"] = game.model_dump_json()
    add_registered_player(fake_redis, "123456", "alice", "old-sid")
    activate_player(fake_sio, "old-sid", "123456")

    await socket_server.rejoin_game(
        "new-sid",
        {"game_pin": "123456", "username": "alice", "zone": "1구역", "old_sid": "old-sid"},
    )

    assert ("participant_already_connected", None, "new-sid") in fake_sio.emitted
    assert fake_redis.values[f"game_session:123456:players:{participant_key('alice', '1구역')}"] == "old-sid"
    assert "new-sid" not in sessions


@pytest.mark.asyncio
async def test_cookie_rejoin_rejects_stale_sid_key_without_set_membership(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    game = make_game(uuid.uuid4())
    fake_redis.values["game:123456"] = game.model_dump_json()
    fake_redis.values[f"game_session:123456:players:{participant_key('alice', '1구역')}"] = "old-sid"

    await socket_server.rejoin_game(
        "new-sid",
        {"game_pin": "123456", "username": "alice", "zone": "1구역", "old_sid": "old-sid"},
    )

    assert all(event != "rejoined_game" for event, _data, _room in fake_sio.emitted)
    assert fake_redis.values[f"game_session:123456:players:{participant_key('alice', '1구역')}"] == "old-sid"
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
    assert fake_redis.values[f"game_session:123456:players:{participant_key('alice', '2구역')}"] == "new-sid"
    assert GamePlayer(username="alice", sid="old-sid", zone="2구역").model_dump_json() not in players
    assert GamePlayer(username="alice", sid="new-sid", zone="2구역").model_dump_json() in players
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
        {"game_pin": "123456", "username": "alice", "zone": "1구역", "old_sid": "old-sid"},
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
    assert fake_redis.values[f"game_session:123456:players:{participant_key('alice', '1구역')}"] == "old-sid"
    assert "new-sid" not in sessions


@pytest.mark.asyncio
async def test_active_sid_guard_is_zone_scoped(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    game = make_game(uuid.uuid4(), started=True)
    fake_redis.values["game:123456"] = game.model_dump_json()
    add_registered_player(fake_redis, "123456", "alice", "zone-1-sid", zone="1구역")
    add_registered_player(fake_redis, "123456", "alice", "zone-2-sid", zone="2구역")
    activate_player(fake_sio, "zone-1-sid", "123456")

    await socket_server.join_game(
        "new-zone-2-sid",
        {
            "game_pin": "123456",
            "username": "alice",
            "zone": "2구역",
            "captcha": None,
            "custom_field": "",
        },
    )

    assert ("participant_already_connected", None, "new-zone-2-sid") not in fake_sio.emitted
    assert fake_redis.values[f"game_session:123456:players:{participant_key('alice', '1구역')}"] == "zone-1-sid"
    assert fake_redis.values[f"game_session:123456:players:{participant_key('alice', '2구역')}"] == "new-zone-2-sid"
    assert sessions["new-zone-2-sid"]["zone"] == "2구역"


@pytest.mark.asyncio
async def test_kicked_player_cannot_started_game_fallback(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    game = make_game(uuid.uuid4(), started=True)
    fake_redis.values["game:123456"] = game.model_dump_json()
    add_registered_player(fake_redis, "123456", "alice", "old-sid")
    sessions["admin-sid"] = {"game_pin": "123456", "admin": True}

    await socket_server.kick_player("admin-sid", {"username": "alice", "zone": "1구역"})
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

    assert f"game_session:123456:players:{participant_key('alice', '1구역')}" not in fake_redis.values
    assert GamePlayer(username="alice", sid="old-sid", zone="1구역").model_dump_json() not in fake_redis.sets[
        "game_session:123456:players"
    ]
    assert ("old-sid", "123456") in fake_sio.left_rooms
    assert ("kick", None, "old-sid") in fake_sio.emitted
    assert ("game_already_started", None, "new-sid") in fake_sio.emitted
    assert "new-sid" not in sessions


@pytest.mark.asyncio
async def test_kick_player_removes_only_matching_zone(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    game = make_game(uuid.uuid4(), started=False)
    fake_redis.values["game:123456"] = game.model_dump_json()
    add_registered_player(fake_redis, "123456", "alice", "zone-1-sid", zone="1구역")
    add_registered_player(fake_redis, "123456", "alice", "zone-2-sid", zone="2구역")
    sessions["admin-sid"] = {"game_pin": "123456", "admin": True}

    await socket_server.kick_player("admin-sid", {"username": "alice", "zone": "1구역"})

    assert f"game_session:123456:players:{participant_key('alice', '1구역')}" not in fake_redis.values
    assert fake_redis.values[f"game_session:123456:players:{participant_key('alice', '2구역')}"] == "zone-2-sid"
    assert GamePlayer(username="alice", sid="zone-1-sid", zone="1구역").model_dump_json() not in fake_redis.sets[
        "game_session:123456:players"
    ]
    assert GamePlayer(username="alice", sid="zone-2-sid", zone="2구역").model_dump_json() in fake_redis.sets[
        "game_session:123456:players"
    ]
    assert ("zone-1-sid", "123456") in fake_sio.left_rooms
    assert ("kick", None, "zone-1-sid") in fake_sio.emitted
    assert ("kick", None, "zone-2-sid") not in fake_sio.emitted
    assert (
        "player_left",
        {"username": "alice", "zone": "1구역"},
        "admin:123456",
    ) in fake_sio.emitted


@pytest.mark.asyncio
async def test_kick_player_requires_admin(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    game = make_game(uuid.uuid4(), started=False)
    fake_redis.values["game:123456"] = game.model_dump_json()
    add_registered_player(fake_redis, "123456", "alice", "zone-1-sid", zone="1구역")
    sessions["player-sid"] = {"game_pin": "123456", "admin": False}

    await socket_server.kick_player("player-sid", {"username": "alice", "zone": "1구역"})

    assert fake_redis.values[f"game_session:123456:players:{participant_key('alice', '1구역')}"] == "zone-1-sid"
    assert GamePlayer(username="alice", sid="zone-1-sid", zone="1구역").model_dump_json() in fake_redis.sets[
        "game_session:123456:players"
    ]
    assert fake_sio.left_rooms == []
    assert fake_sio.emitted == []


@pytest.mark.asyncio
async def test_submit_answer_scores_same_username_different_zones_separately(recovery_context):
    fake_redis, _fake_sio, sessions = recovery_context
    question = QuizQuestion(
        question="Question",
        time="30",
        answers=[ABCDQuizAnswer(answer="A", right=True), ABCDQuizAnswer(answer="B")],
    )
    game = make_game(uuid.uuid4(), question_show=True, questions=[question], started=True)
    fake_redis.values["game:123456"] = game.model_dump_json()
    fake_redis.values["game:123456:current_time"] = datetime.now().isoformat()
    add_registered_player(fake_redis, "123456", "alice", "zone-1-sid", zone="1구역")
    add_registered_player(fake_redis, "123456", "alice", "zone-2-sid", zone="2구역")
    sessions["zone-1-sid"] = {
        "game_pin": "123456",
        "username": "alice",
        "sid_custom": "zone-1-sid",
        "admin": False,
        "zone": "1구역",
        "ping": 0,
    }
    sessions["zone-2-sid"] = {
        "game_pin": "123456",
        "username": "alice",
        "sid_custom": "zone-2-sid",
        "admin": False,
        "zone": "2구역",
        "ping": 0,
    }

    await socket_server.submit_answer("zone-1-sid", {"question_index": 0, "answer": 0})
    await socket_server.submit_answer("zone-2-sid", {"question_index": 0, "answer": 0})

    scores = fake_redis.hashes["game_session:123456:player_scores"]
    assert set(scores) == {participant_key("alice", "1구역"), participant_key("alice", "2구역")}
    answers = AnswerDataList.model_validate_json(fake_redis.values["game_session:123456:0"])
    assert [(answer.username, answer.zone) for answer in answers] == [("alice", "1구역"), ("alice", "2구역")]


@pytest.mark.asyncio
async def test_register_as_admin_existing_session_rejects_takeover(recovery_context):
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
async def test_register_as_admin_wrong_game_id_rejects(recovery_context):
    fake_redis, fake_sio, _sessions = recovery_context
    user_id = uuid.uuid4()
    actual_game_id = uuid.uuid4()
    fake_redis.values["game:123456"] = make_game(user_id, game_id=actual_game_id).model_dump_json()

    await register_as_admin("new-admin", {"game_pin": "123456", "game_id": str(uuid.uuid4())})

    assert ("game_not_found", None, "new-admin") in fake_sio.emitted


@pytest.mark.asyncio
async def test_register_as_admin_fresh_session_saves_and_enters_rooms(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    user_id = uuid.uuid4()
    game_id = uuid.uuid4()
    game = make_game(user_id, game_id=game_id)
    fake_redis.values["game:123456"] = game.model_dump_json()

    await register_as_admin("admin-sid", {"game_pin": "123456", "game_id": str(game_id)})

    saved_game_session = GameSession.model_validate_json(fake_redis.values["game_session:123456"])
    assert saved_game_session.admin == "admin-sid"
    assert saved_game_session.game_id == str(game_id)
    assert saved_game_session.answers == []
    assert ("registered_as_admin", {"game_id": str(game_id), "game": game.model_dump_json()}, "admin-sid") in fake_sio.emitted
    assert sessions["admin-sid"] == {"game_pin": "123456", "admin": True, "remote": False}
    assert ("admin-sid", "123456") in fake_sio.entered_rooms
    assert ("admin-sid", "admin:123456") in fake_sio.entered_rooms


@pytest.mark.asyncio
async def test_disconnect_clears_matching_admin_session(recovery_context):
    fake_redis, _fake_sio, sessions = recovery_context
    game_id = uuid.uuid4()
    sessions["admin-sid"] = {"game_pin": "123456", "admin": True, "remote": False}
    fake_redis.values["game_session:123456"] = GameSession(
        admin="admin-sid", game_id=str(game_id), answers=[]
    ).model_dump_json()

    await socket_server.disconnect("admin-sid")

    assert "game_session:123456" not in fake_redis.values


@pytest.mark.asyncio
async def test_register_as_remote_wrong_game_id_rejects(recovery_context):
    fake_redis, fake_sio, sessions = recovery_context
    user_id = uuid.uuid4()
    actual_game_id = uuid.uuid4()
    fake_redis.values["game:123456"] = make_game(user_id, game_id=actual_game_id).model_dump_json()

    await socket_server.register_as_remote(
        "remote-sid",
        {"game_pin": "123456", "game_id": str(uuid.uuid4())},
    )

    assert ("game_not_found", None, "remote-sid") in fake_sio.emitted
    assert "remote-sid" not in sessions
    assert all(event != "registered_as_admin" for event, _data, _room in fake_sio.emitted)


@pytest.mark.asyncio
async def test_live_games_returns_empty_list(recovery_context):
    fake_redis, _fake_sio, _sessions = recovery_context
    user_id = uuid.uuid4()
    game_id = uuid.uuid4()
    owned_game = make_game(user_id, game_id=game_id, game_pin="123456")
    fake_redis.values[f"game_pin:{user_id}:{owned_game.quiz_id}"] = "123456"
    fake_redis.values["game:123456"] = owned_game.model_dump_json()
    fake_redis.values["game_session:123456"] = GameSession(
        admin="old-admin", game_id=str(game_id), answers=[]
    ).model_dump_json()

    live_games = await get_live_games(
        user=User(id=user_id, email="user@example.com", username="user", avatar=b"")
    )

    assert live_games == []
