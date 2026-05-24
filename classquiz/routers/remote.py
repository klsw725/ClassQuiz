# SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0


from fastapi import APIRouter, Depends, HTTPException

from classquiz.auth import get_current_user
from classquiz.db.models import User, GameInLobby, PlayGame, GameSession
from classquiz.config import redis

router = APIRouter()


def _decode_redis_value(value):
    if isinstance(value, bytes):
        return value.decode()
    return value


@router.get("/game_waiting")
async def get_game_in_lobby(user: User = Depends(get_current_user)):
    game_in_lobby_raw = await redis.get(f"game_in_lobby:{user.id.hex}")
    if game_in_lobby_raw is None:
        raise HTTPException(status_code=404, detail="No game waiting")
    game_in_lobby = GameInLobby.model_validate_json(game_in_lobby_raw)
    return game_in_lobby


@router.get("/live_games")
async def get_live_games(user: User = Depends(get_current_user)):
    live_games = []

    async for alias_key in redis.scan_iter(match=f"game_pin:{user.id}:*"):
        game_pin = _decode_redis_value(await redis.get(alias_key))
        if game_pin is None:
            continue

        game_raw = await redis.get(f"game:{game_pin}")
        if game_raw is None:
            continue

        game = PlayGame.model_validate_json(game_raw)
        if game.user_id != user.id or game.game_mode == "solo":
            continue

        session_raw = await redis.get(f"game_session:{game_pin}")
        if session_raw is not None:
            session = GameSession.model_validate_json(session_raw)
            if str(session.game_id) != str(game.game_id):
                continue

        live_games.append(
            {
                "game_pin": str(game_pin),
                "game_id": str(game.game_id),
                "quiz_id": str(game.quiz_id),
                "title": game.title,
                "current_question": game.current_question,
                "question_count": len(game.questions),
                "started": game.started,
                "resume_url": f"/admin?token={game.game_id}&pin={game_pin}&connect=1&resume=1",
            }
        )

    return sorted(live_games, key=lambda live_game: live_game["game_pin"])
