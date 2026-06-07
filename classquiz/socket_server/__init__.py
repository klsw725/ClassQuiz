# SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0


import base64
import hashlib
import json
import os
import random
from typing import cast

import socketio
from socketio.exceptions import ConnectionRefusedError
from cryptography.fernet import Fernet

from classquiz.config import redis, settings
from classquiz.scoring import calculate_answer_score
from classquiz.db.models import (
    PlayGame,
    QuizQuestionType,
    GameSession,
    GamePlayer,
    TextQuizAnswer,
    VotingQuizAnswer,
    AnswerDataList,
    AnswerData,
)
from pydantic import BaseModel, ValidationError
from datetime import datetime

from classquiz.socket_server.helpers import (
    build_multi_text_answer_details,
    check_answer,
    check_captcha,
    get_submitted_text_answers,
    has_already_answered,
)
from .models import (
    RejoinGameData,
    JoinGameData,
    ReturnQuestion,
    SubmitAnswerData,
    RegisterAsAdminData,
    KickPlayerInput,
    ConnectSessionIdEvent,
)

from classquiz.socket_server.export_helpers import save_quiz_to_storage
from classquiz.socket_server.participant_identity import participant_key
from classquiz.socket_server.session import get_session, save_session

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=[])
settings = settings()


def get_fernet_key() -> bytes:
    hlib = hashlib.sha256()
    hlib.update(settings.secret_key.encode("utf-8"))
    return base64.urlsafe_b64encode(hlib.hexdigest().encode("latin-1")[:32])


fernet = Fernet(get_fernet_key())


async def generate_final_results(game_data: PlayGame, game_pin: str) -> dict:
    results = {}
    for i in range(len(game_data.questions)):
        redis_res = await redis.get(f"game_session:{game_pin}:{i}")
        if redis_res is None:
            continue
        else:
            results[str(i)] = json.loads(redis_res)
    return results


async def set_answer(answers, game_pin: str, q_index: int, data: AnswerData) -> AnswerDataList:
    if answers is None:
        answers = AnswerDataList([data])
    else:
        answers = AnswerDataList.model_validate_json(answers)
        answers.append(data)
    await redis.set(
        f"game_session:{game_pin}:{q_index}",
        answers.model_dump_json(),
        ex=7200,
    )
    return answers


def should_randomize_answer_order_for_player(game_data: PlayGame) -> bool:
    return game_data.randomize_answers and game_data.randomize_answers_mode == "per_participant"


def can_randomize_question_answers(question_type: QuizQuestionType | None) -> bool:
    return question_type in {
        QuizQuestionType.ABCD,
        QuizQuestionType.CHECK,
        QuizQuestionType.ORDER,
        QuizQuestionType.VOTING,
    }


def build_return_question(game_data: PlayGame, question_index: int, shuffle_answers: bool = False) -> tuple[dict, list[int]]:
    question = game_data.questions[question_index]
    temp_return = game_data.model_dump(include={"questions"})["questions"][question_index]
    if question.type == QuizQuestionType.VOTING:
        for i in range(len(temp_return["answers"])):
            temp_return["answers"][i] = VotingQuizAnswer(**temp_return["answers"][i])
    temp_return["type"] = question.type
    answer_order = list(range(len(temp_return["answers"]))) if isinstance(temp_return.get("answers"), list) else []
    if question.type == QuizQuestionType.TEXT:
        temp_return["answers"] = []
        return temp_return, answer_order
    if question.type == QuizQuestionType.MULTI_TEXT:
        temp_return["answers"] = [{"answer": "", "case_sensitive": False} for _answer in answer_order]
        return temp_return, answer_order
    if shuffle_answers and can_randomize_question_answers(question.type) and answer_order:
        indexed_answers = list(zip(answer_order, temp_return["answers"]))
        random.shuffle(indexed_answers)
        answer_order = [index for index, _answer in indexed_answers]
        temp_return["answers"] = [answer for _index, answer in indexed_answers]
    return ReturnQuestion(**temp_return).model_dump(), answer_order


async def emit_player_randomized_question(game_pin: str, question_index: int, game_data: PlayGame):
    players = await redis.smembers(f"game_session:{game_pin}:players")
    for raw_player in players:
        player = GamePlayer.model_validate_json(raw_player)
        if player.sid is None:
            continue
        await emit_question_to_player(player.sid, game_pin, player.username, player.zone, question_index, game_data)


async def emit_question_to_player(
    sid: str,
    game_pin: str,
    username: str,
    zone: str | None,
    question_index: int,
    game_data: PlayGame,
    use_remaining_time: bool = False,
):
    question_type = game_data.questions[question_index].type
    if question_type == QuizQuestionType.SLIDE:
        await sio.emit("set_question_number", {"question_index": question_index}, room=sid)
        return

    shuffle_answers = should_randomize_answer_order_for_player(game_data) or question_type == QuizQuestionType.ORDER
    question, answer_order = build_return_question(game_data, question_index, shuffle_answers=shuffle_answers)
    if use_remaining_time:
        question_started_raw = await redis.get(f"game:{game_pin}:current_time")
        if question_started_raw is not None:
            question_started = datetime.fromisoformat(question_started_raw)
            question_time = int(float(game_data.questions[question_index].time))
            elapsed = int((datetime.now() - question_started).total_seconds())
            question["time"] = str(max(question_time - elapsed, 0))
    if should_randomize_answer_order_for_player(game_data) and question_type == QuizQuestionType.CHECK:
        await redis.set(
            f"game_session:{game_pin}:answer_order:{question_index}:{participant_key(username, zone)}",
            json.dumps(answer_order),
            ex=7200,
        )
    await sio.emit(
        "set_question_number",
        {
            "question_index": question_index,
            "question": question,
        },
        room=sid,
    )


async def remap_player_randomized_check_answer(
    game_pin: str, username: str, zone: str | None, data: SubmitAnswerData
):
    order_raw = await redis.get(
        f"game_session:{game_pin}:answer_order:{data.question_index}:{participant_key(username, zone)}"
    )
    if order_raw is None:
        return
    answer_order = json.loads(order_raw)
    selected_answer_indexes = sorted(answer_order[int(i)] for i in str(data.answer))
    data.answer = "".join(str(i) for i in selected_answer_indexes)


async def clear_live_session_state(game_pin: str):
    await redis.delete(f"game_session:{game_pin}")
    async for key in redis.scan_iter(match=f"game_session:{game_pin}:*"):
        await redis.delete(key)
    await redis.delete(f"game:{game_pin}:current_time")
    await redis.delete(f"game:{game_pin}:players:zones")
    await redis.delete(f"game:{game_pin}:players:custom_fields")

    game_raw = await redis.get(f"game:{game_pin}")
    if game_raw is None:
        return
    game_data = PlayGame.model_validate_json(game_raw)
    game_data.started = False
    game_data.current_question = -1
    game_data.question_show = False
    await game_data.save(game_pin)


def player_sid_key(game_pin: str, username: str, zone: str | None) -> str:
    return f"game_session:{game_pin}:players:{participant_key(username, zone)}"


def player_set_key(game_pin: str) -> str:
    return f"game_session:{game_pin}:players"


def player_set_value(username: str, sid: str | None, zone: str | None) -> str:
    return GamePlayer(username=username, sid=sid, zone=zone).model_dump_json()


def is_active_player_sid(existing_sid: str, game_pin: str) -> bool:
    return bool(sio.manager.is_connected(existing_sid, "/")) and game_pin in sio.rooms(existing_sid, namespace="/")


async def is_registered_player(game_pin: str, username: str, zone: str | None, existing_sid: str | None) -> bool:
    if existing_sid is None:
        return False
    players = await redis.smembers(player_set_key(game_pin))
    return player_set_value(username, existing_sid, zone) in players


async def restore_player_session(
    sid: str,
    game_pin: str,
    username: str,
    zone: str | None,
    old_sid: str,
    game_data: PlayGame,
) -> None:
    await redis.set(player_sid_key(game_pin, username, zone), sid, ex=7200)
    await redis.srem(player_set_key(game_pin), player_set_value(username, old_sid, zone))
    await redis.sadd(player_set_key(game_pin), player_set_value(username, sid, zone))
    stored_zone = await redis.hget(f"game:{game_pin}:players:zones", participant_key(username, zone))
    session_zone = stored_zone if stored_zone is not None else zone
    session = {
        "game_pin": game_pin,
        "username": username,
        "sid_custom": sid,
        "admin": False,
    }
    if session_zone is not None:
        session["zone"] = session_zone
    await save_session(sid, sio, session)
    await sio.enter_room(sid, game_pin)
    await sio.emit("rejoined_game", game_data.to_player_data(), room=sid)
    encrypted_datetime = fernet.encrypt(datetime.now().isoformat().encode("utf-8")).decode("utf-8")
    await sio.emit("time_sync", encrypted_datetime, room=sid)
    if game_data.started and game_data.question_show and game_data.current_question != -1:
        await emit_question_to_player(
            sid,
            game_pin,
            username,
            session_zone,
            game_data.current_question,
            game_data,
            use_remaining_time=True,
        )


@sio.event
async def rejoin_game(sid: str, data: dict):
    try:
        data = RejoinGameData(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return
    redis_res = await redis.get(f"game:{data.game_pin}")
    if redis_res is None:
        await sio.emit("game_not_found", room=sid)
        return
    game_data = PlayGame.model_validate_json(redis_res)
    if game_data.game_mode == "solo":
        await sio.emit("game_not_found", room=sid)
        return
    old_sid = await redis.get(player_sid_key(data.game_pin, data.username, data.zone))
    if old_sid != data.old_sid:
        return
    if not await is_registered_player(data.game_pin, data.username, data.zone, data.old_sid):
        return
    if is_active_player_sid(data.old_sid, data.game_pin):
        await sio.emit("participant_already_connected", room=sid)
        return
    await restore_player_session(sid, data.game_pin, data.username, data.zone, data.old_sid, game_data)


@sio.event
async def join_game(sid: str, data: dict):
    redis_res = await redis.get(f"game:{data['game_pin']}")
    if redis_res is None:
        await sio.emit("game_not_found", room=sid)
        return
    try:
        data = JoinGameData(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return
    game_data = PlayGame.model_validate_json(redis_res)
    if game_data.game_mode == "solo":
        await sio.emit("game_not_found", room=sid)
        return
    if game_data.started:
        old_sid = await redis.get(player_sid_key(data.game_pin, data.username, data.zone))
        zone = await redis.hget(f"game:{data.game_pin}:players:zones", participant_key(data.username, data.zone))
        if old_sid is None or not await is_registered_player(data.game_pin, data.username, data.zone, old_sid):
            await sio.emit("game_already_started", room=sid)
            return
        if zone != data.zone:
            await sio.emit("username_already_exists", room=sid)
            return
        if is_active_player_sid(old_sid, data.game_pin):
            await sio.emit("participant_already_connected", room=sid)
            return
        await restore_player_session(sid, data.game_pin, data.username, data.zone, old_sid, game_data)
        return
    # +++ START checking captcha +++
    if game_data.captcha_enabled:
        captcha_res = check_captcha(data.captcha)
        if not captcha_res:
            return
    # --- END checking captcha ---
    key = participant_key(data.username, data.zone)
    if await redis.get(player_sid_key(data.game_pin, data.username, data.zone)) is not None:
        await sio.emit("username_already_exists", room=sid)
        return

    session = {
        "game_pin": data.game_pin,
        "username": data.username,
        "sid_custom": sid,
        "admin": False,
        "zone": data.zone,
    }
    await save_session(sid, sio, session)
    await sio.emit(
        "joined_game",
        game_data.to_player_data(),
        room=sid,
    )
    await redis.set(player_sid_key(data.game_pin, data.username, data.zone), sid, ex=7200)
    await GamePlayer(username=data.username, sid=sid, zone=data.zone).to_player_stack(data.game_pin)
    player_zones_key = f"game:{data.game_pin}:players:zones"
    await redis.hset(
        player_zones_key,
        key,
        data.zone,
    )
    await redis.expire(player_zones_key, 7200)

    if data.custom_field == "":
        data.custom_field = None
    if data.custom_field is not None:
        await redis.hset(
            f"game:{data.game_pin}:players:custom_fields",
            key,
            data.custom_field,
        )

    await sio.emit(
        "player_joined",
        {"username": data.username, "sid": sid, "zone": data.zone},
        room=f"admin:{data.game_pin}",
    )
    # +++ Time-Sync +++
    encrypted_datetime = fernet.encrypt(datetime.now().isoformat().encode("utf-8")).decode("utf-8")
    await sio.emit("time_sync", encrypted_datetime, room=sid)
    # --- Time-Sync ---
    await sio.enter_room(sid, data.game_pin)


@sio.event
async def start_game(sid: str, _data: dict):
    session = await get_session(sid, sio)
    if not session["admin"]:
        return
    game_data = await PlayGame.get_from_redis(session["game_pin"])
    game_data.started = True
    await game_data.save(session["game_pin"])
    await redis.delete(f"game_in_lobby:{game_data.user_id.hex}")
    await sio.emit("start_game", room=session["game_pin"])


@sio.event
async def register_as_admin(sid: str, data: dict):
    try:
        data = RegisterAsAdminData(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return
    game_pin = data.game_pin
    game_id = data.game_id
    redis_res = await redis.get(f"game:{game_pin}")
    if redis_res is None:
        await sio.emit("game_not_found", room=sid)
        return

    game_data = PlayGame.model_validate_json(redis_res)
    if game_data.game_mode == "solo" or str(game_data.game_id) != str(game_id):
        await sio.emit("game_not_found", room=sid)
        return

    session_raw = await redis.get(f"game_session:{game_pin}")
    if session_raw is None:
        await GameSession(admin=sid, game_id=game_id, answers=[]).save(game_pin)
        payload = {"game_id": game_id, "game": redis_res}
    else:
        await sio.emit("already_registered_as_admin", room=sid)
        return

    await sio.emit(
        "registered_as_admin",
        payload,
        room=sid,
    )
    session = {"game_pin": game_pin, "admin": True, "remote": False}
    await save_session(sid, sio, session)
    await sio.enter_room(sid, game_pin)
    await sio.enter_room(sid, f"admin:{data.game_pin}")


@sio.event
async def get_question_results(sid: str, data: dict):
    session = await get_session(sid, sio)
    if not session["admin"]:
        return
    game_pin = session["game_pin"]
    answer_data_list = await AnswerDataList.get_redis_or_empty(game_pin, data["question_number"])
    game_data = await PlayGame.get_from_redis(game_pin)
    game_data.question_show = False
    await game_data.save(game_pin)
    await sio.emit("question_results", answer_data_list.model_dump(), room=game_pin)


@sio.event
async def set_question_number(sid: str, data: str):
    # data is just a number (as a str) of the question
    session = await get_session(sid, sio)
    if not session["admin"]:
        return
    game_pin = session["game_pin"]
    game_data = await PlayGame.get_from_redis(session["game_pin"])
    game_data.current_question = int(float(data))
    game_data.question_show = True
    await game_data.save(session["game_pin"])
    await redis.set(f"game:{session['game_pin']}:current_time", datetime.now().isoformat(), ex=7200)
    question_index = int(float(data))
    if game_data.questions[int(float(data))].type == QuizQuestionType.SLIDE:
        await sio.emit(
            "set_question_number",
            {
                "question_index": question_index,
            },
            room=sid,
        )
        return
    if should_randomize_answer_order_for_player(game_data) and can_randomize_question_answers(
        game_data.questions[question_index].type
    ):
        await sio.emit(
            "set_question_number",
            {
                "question_index": question_index,
            },
            room=f"admin:{game_pin}",
        )
        await emit_player_randomized_question(game_pin, question_index, game_data)
        return
    shuffle_answers = game_data.questions[question_index].type == QuizQuestionType.ORDER
    question, _answer_order = build_return_question(game_data, question_index, shuffle_answers=shuffle_answers)
    await sio.emit(
        "set_question_number",
        {
            "question_index": question_index,
            "question": question,
        },
        room=game_pin,
    )


@sio.event
async def submit_answer(sid: str, data: dict):
    now = datetime.now()
    try:
        data = SubmitAnswerData(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return
    data.answer = "" if data.answer is None else str(data.answer)
    session = await get_session(sid, sio)
    question_index = int(float(data.question_index))
    game_data = await PlayGame.get_from_redis(session["game_pin"])

    if question_index != game_data.current_question:
        await sio.emit("question_not_active", room=sid)
        return

    already_answered = await has_already_answered(
        session["game_pin"], question_index, session["username"], session.get("zone")
    )
    if already_answered:
        await sio.emit("already_replied", room=sid)
        return

    if game_data.questions[question_index].type == QuizQuestionType.CHECK:
        await remap_player_randomized_check_answer(session["game_pin"], session["username"], session.get("zone"), data)
    answer_right, answer, score_credit = check_answer(game_data, data)
    answer_details = None
    if game_data.questions[question_index].type == QuizQuestionType.MULTI_TEXT:
        answer_details = build_multi_text_answer_details(
            get_submitted_text_answers(data),
            cast(list[TextQuizAnswer], game_data.questions[question_index].answers),
            game_data.questions[question_index].ignore_whitespace,
            game_data.questions[question_index].multi_text_order_sensitive,
        )
    latency = int(float(session["ping"]))
    time_q_started = datetime.fromisoformat(await redis.get(f"game:{session['game_pin']}:current_time"))
    diff = (time_q_started - now).total_seconds() * 1000  # - timedelta(milliseconds=latency)
    score = calculate_answer_score(
        score_credit,
        game_data.time_based_scoring,
        abs(diff) - latency,
        int(float(game_data.questions[question_index].time)),
        game_data.questions[question_index].points,
    )
    await redis.hincrby(
        f"game_session:{session['game_pin']}:player_scores",
        participant_key(session["username"], session.get("zone")),
        score,
    )
    answer_data = AnswerData(
        username=session["username"],
        answer=answer,
        right=answer_right,
        time_taken=abs(diff) - latency,
        score=score,
        zone=session.get("zone"),
        answer_details=answer_details,
    )
    answers = await redis.get(f"game_session:{session['game_pin']}:{data.question_index}")
    answers = await set_answer(
        answers,
        game_pin=session["game_pin"],
        data=answer_data,
        q_index=int(float(data.question_index)),
    )
    await sio.emit("player_answer", {})


@sio.event
async def get_final_results(sid: str, _data: dict):
    session: dict = await get_session(sid, sio)
    if not session["admin"]:
        return
    game_data = await PlayGame.get_from_redis(session["game_pin"])
    results = await generate_final_results(game_data, session["game_pin"])
    await sio.emit("final_results", results, room=session["game_pin"])


@sio.event
async def get_export_token(sid: str):
    session = await get_session(sid, sio)
    if not session["admin"]:
        return
    game_data = await PlayGame.get_from_redis(session["game_pin"])
    results = await generate_final_results(game_data, session["game_pin"])
    token = os.urandom(32).hex()
    await redis.set(f"export_token:{token}", json.dumps(results), ex=7200)
    await sio.emit("export_token", token, room=sid)


@sio.event
async def show_solutions(sid: str, _data: dict):
    session: dict = await get_session(sid, sio)
    game_data = await PlayGame.get_from_redis(session["game_pin"])
    if not session["admin"]:
        return
    await sio.emit(
        "solutions",
        game_data.questions[game_data.current_question].model_dump(),
        room=session["game_pin"],
    )


@sio.event
async def echo_time_sync(sid: str, data: str):
    then_dec = fernet.decrypt(data).decode("utf-8")
    then = datetime.fromisoformat(then_dec)
    now = datetime.now()
    delta = now - then
    session = await get_session(sid, sio)
    session["ping"] = delta.microseconds / 1000
    await save_session(sid, sio, session)


@sio.event
async def kick_player(sid: str, data: dict):
    try:
        data = KickPlayerInput(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return

    session: dict = await get_session(sid, sio)
    if not session["admin"]:
        return

    player_sid = await redis.get(player_sid_key(session["game_pin"], data.username, data.zone))
    await redis.srem(
        f"game_session:{session['game_pin']}:players",
        GamePlayer(username=data.username, sid=player_sid, zone=data.zone).model_dump_json(),
    )
    await redis.delete(player_sid_key(session["game_pin"], data.username, data.zone))
    key = participant_key(data.username, data.zone)
    await redis.hdel(f"game:{session['game_pin']}:players:zones", key)
    await redis.hdel(f"game:{session['game_pin']}:players:custom_fields", key)
    await sio.emit(
        "player_left",
        {"username": data.username, "zone": data.zone},
        room=f"admin:{session['game_pin']}",
    )
    if player_sid is not None:
        await sio.leave_room(player_sid, session["game_pin"])
        await sio.emit("kick", room=player_sid)


class _RegisterAsRemoteInput(BaseModel):
    game_pin: str
    game_id: str


@sio.event
async def register_as_remote(sid: str, data: dict):
    try:
        data = _RegisterAsRemoteInput(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return
    redis_res = await redis.get(f"game:{data.game_pin}")
    if redis_res is None:
        await sio.emit("game_not_found", room=sid)
        return
    game_data = PlayGame.model_validate_json(redis_res)
    if game_data.game_mode == "solo" or str(game_data.game_id) != str(data.game_id):
        await sio.emit("game_not_found", room=sid)
        return
    await sio.emit(
        "registered_as_admin",
        {"game_id": data.game_id, "game": redis_res},
        room=sid,
    )
    await sio.emit("control_visibility", {"visible": False}, room=f"admin:{data.game_pin}")
    session = await get_session(sid, sio)
    session["game_pin"] = data.game_pin
    session["admin"] = True
    session["remote"] = True
    await save_session(sid, sio, session)
    await sio.enter_room(sid, data.game_pin)
    await sio.enter_room(sid, f"admin:{data.game_pin}")


class _SetControlVisibilityInput(BaseModel):
    visible: bool


@sio.event
async def set_control_visibility(sid: str, data: dict):
    try:
        data = _SetControlVisibilityInput(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return
    session: dict = await get_session(sid, sio)
    await sio.emit(
        "control_visibility",
        {"visible": data.visible},
        room=f"admin:{session['game_pin']}",
    )


@sio.event
async def save_quiz(sid: str):
    session: dict = await get_session(sid, sio)
    if not session["admin"]:
        return
    await save_quiz_to_storage(session["game_pin"])
    await sio.emit("results_saved_successfully")


@sio.event
async def connect(sid: str, _environ, _auth):
    session_id = os.urandom(16).hex()
    print("Connection opened with handler")
    sio_session = {"session_id": session_id}
    await sio.save_session(sid, sio_session)
    await sio.emit("session_id", ConnectSessionIdEvent(session_id=session_id).dict())


@sio.event
async def disconnect(sid: str):
    try:
        session = await get_session(sid, sio)
    except (ConnectionRefusedError, KeyError, TypeError, json.JSONDecodeError):
        return

    if not session.get("admin") or session.get("remote"):
        return

    game_pin = session["game_pin"]
    session_raw = await redis.get(f"game_session:{game_pin}")
    if session_raw is None:
        return
    game_session = GameSession.model_validate_json(session_raw)
    if game_session.admin == sid:
        await clear_live_session_state(game_pin)
