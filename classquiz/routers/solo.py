import hmac
import random
import uuid
from datetime import datetime
from typing import cast

import bleach
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from classquiz.config import ALLOWED_TAGS_FOR_QUIZ, redis
from classquiz.db.models import AnswerData, PlayGame, QuizQuestion, QuizQuestionType, TextQuizAnswer, TextAnswerDetail
from classquiz.scoring import calculate_answer_score
from classquiz.socket_server.helpers import build_multi_text_answer_details, check_answer, get_submitted_text_answers
from classquiz.socket_server.models import ALLOWED_ZONES, ReturnQuestion, SubmitAnswerData, SubmitAnswerDataOrderType

router = APIRouter()

SOLO_ATTEMPT_TTL_SECONDS = 18000


class CreateSoloAttemptRequest(BaseModel):
    game_pin: str = Field(pattern=r"^\d{6}$")
    solo_token: str | None = Field(default=None, min_length=1, max_length=256)
    username: str | None = Field(default=None, min_length=1, max_length=100)
    zone: str

    @field_validator("zone")
    def zone_must_be_allowed(cls, value: str):
        if value not in ALLOWED_ZONES:
            raise ValueError("Zone must be between 1구역 and 11구역")
        return value


class SubmitSoloAttemptRequest(BaseModel):
    question_index: int = Field(ge=0, le=1000)
    answer: str | int | None = None
    complex_answer: list[SubmitAnswerDataOrderType] | None = Field(default=None, max_length=100)

    @field_validator("answer")
    def answer_is_bounded(cls, value: str | int | None):
        if isinstance(value, str) and len(value) > 1000:
            raise ValueError("answer must be 1000 characters or fewer")
        return value

    @field_validator("complex_answer")
    def complex_answer_items_are_bounded(cls, value: list[SubmitAnswerDataOrderType] | None):
        if value is not None:
            for item in value:
                if len(item.answer) > 1000:
                    raise ValueError("complex answer items must be 1000 characters or fewer")
        return value


class SoloAttempt(BaseModel):
    game_pin: str
    username: str
    zone: str
    current_question: int = 0
    total_score: int = 0
    answers: list[AnswerData] = Field(default_factory=list)
    question_started_at: datetime
    awaiting_next_question: bool = False
    completed: bool = False


class SoloAttemptStateResponse(BaseModel):
    attempt_id: str
    game_pin: str
    username: str
    zone: str
    title: str
    description: str
    current_question: int
    question_count: int
    total_score: int
    completed: bool
    awaiting_next_question: bool
    question: dict[str, object] | None = None


class SoloAttemptSubmitResponse(BaseModel):
    right: bool
    score: int
    total_score: int
    completed: bool
    solution: dict[str, object] | None = None
    answer_details: list[TextAnswerDetail] | None = None


def _attempt_key(attempt_id: str) -> str:
    return f"solo_attempt:{attempt_id}"



def _strip_solution_data(question_data: dict[str, object]) -> dict[str, object]:
    answers = question_data.get("answers")
    if isinstance(answers, list):
        question_data["answers"] = [
            {key: value for key, value in cast(dict[str, object], answer).items() if key != "right"}
            if isinstance(answer, dict)
            else answer
            for answer in answers
        ]
    elif isinstance(answers, dict):
        question_data["answers"] = {
            key: value
            for key, value in cast(dict[str, object], answers).items()
            if key not in {"min_correct", "max_correct"}
        }
    return question_data


def _safe_question(game: PlayGame, question_index: int) -> dict[str, object]:
    question = game.questions[question_index]
    question_data = cast(dict[str, object], game.model_dump(include={"questions"})["questions"][question_index])
    question_data["question"] = bleach.clean(cast(str, question_data["question"]), tags=ALLOWED_TAGS_FOR_QUIZ, strip=True)
    question_data["type"] = question.type
    if question.type == QuizQuestionType.TEXT:
        question_data["answers"] = []
        return _strip_solution_data(question_data)
    if question.type == QuizQuestionType.MULTI_TEXT:
        answers = question_data.get("answers")
        answer_count = len(answers) if isinstance(answers, list) else 0
        question_data["answers"] = [{"answer": "", "case_sensitive": False} for _answer in range(answer_count)]
        return _strip_solution_data(question_data)
    if question.type == QuizQuestionType.ORDER and isinstance(question_data["answers"], list):
        random.shuffle(question_data["answers"])
    try:
        return _strip_solution_data(cast(dict[str, object], ReturnQuestion(**question_data).model_dump()))
    except ValueError:
        if question.type in [QuizQuestionType.TEXT, QuizQuestionType.MULTI_TEXT]:
            question_data["answers"] = []
        return _strip_solution_data(question_data)


def _solution_question(question: QuizQuestion) -> dict[str, object]:
    question_data = cast(dict[str, object], question.model_dump())
    answers = question_data.get("answers")
    if question.type == QuizQuestionType.MULTI_TEXT and isinstance(answers, list):
        question_data["answers"] = [{"answer": "", "case_sensitive": False} for _answer in answers]
    return question_data


async def _get_solo_game(game_pin: str) -> PlayGame:
    game_raw = await redis.get(f"game:{game_pin}")
    if game_raw is None:
        raise HTTPException(status_code=404, detail="game not found")
    game = PlayGame.model_validate_json(game_raw)
    if game.game_mode != "solo":
        raise HTTPException(status_code=400, detail="game is not a solo game")
    return game


def _check_solo_token(game: PlayGame, token: str | None):
    if game.solo_token is None or token is None or not hmac.compare_digest(game.solo_token, token):
        raise HTTPException(status_code=404, detail="game not found")


async def _get_attempt(attempt_id: str) -> SoloAttempt:
    attempt_raw = await redis.get(_attempt_key(attempt_id))
    if attempt_raw is None:
        raise HTTPException(status_code=404, detail="attempt not found")
    return SoloAttempt.model_validate_json(attempt_raw)


async def _save_attempt(attempt_id: str, attempt: SoloAttempt):
    await redis.set(_attempt_key(attempt_id), attempt.model_dump_json(), ex=SOLO_ATTEMPT_TTL_SECONDS)


def _state_response(attempt_id: str, attempt: SoloAttempt, game: PlayGame) -> SoloAttemptStateResponse:
    question = None
    if not attempt.completed and attempt.current_question < len(game.questions):
        question = _safe_question(game, attempt.current_question)
    return SoloAttemptStateResponse(
        attempt_id=attempt_id,
        game_pin=attempt.game_pin,
        username=attempt.username,
        zone=attempt.zone,
        title=bleach.clean(game.title, tags=ALLOWED_TAGS_FOR_QUIZ, strip=True),
        description=bleach.clean(game.description, tags=ALLOWED_TAGS_FOR_QUIZ, strip=True),
        current_question=attempt.current_question,
        question_count=len(game.questions),
        total_score=attempt.total_score,
        completed=attempt.completed,
        awaiting_next_question=attempt.awaiting_next_question,
        question=question,
    )


@router.post("/attempts", response_model=SoloAttemptStateResponse)
async def create_attempt(data: CreateSoloAttemptRequest):
    game = await _get_solo_game(data.game_pin)
    _check_solo_token(game, data.solo_token)
    attempt_id = str(uuid.uuid4())
    completed = len(game.questions) == 0
    attempt = SoloAttempt(
        game_pin=data.game_pin,
        username=data.username or "Player",
        zone=data.zone,
        question_started_at=datetime.now(),
        completed=completed,
    )
    await _save_attempt(attempt_id, attempt)
    return _state_response(attempt_id, attempt, game)


@router.get("/attempts/{attempt_id}", response_model=SoloAttemptStateResponse)
async def get_attempt(attempt_id: str):
    attempt = await _get_attempt(attempt_id)
    game = await _get_solo_game(attempt.game_pin)
    return _state_response(attempt_id, attempt, game)


@router.post("/attempts/{attempt_id}/submit", response_model=SoloAttemptSubmitResponse)
async def submit_attempt(attempt_id: str, data: SubmitSoloAttemptRequest):
    now = datetime.now()
    attempt = await _get_attempt(attempt_id)
    game = await _get_solo_game(attempt.game_pin)
    if attempt.completed:
        raise HTTPException(status_code=400, detail="attempt already completed")
    if attempt.awaiting_next_question:
        raise HTTPException(status_code=400, detail="question already answered")
    if data.question_index != attempt.current_question:
        raise HTTPException(status_code=400, detail="question index is not current")

    question = game.questions[data.question_index]
    answer_right: bool = False
    answer: str | int = ""
    score = 0
    solution: dict[str, object] | None = None
    answer_details: list[TextAnswerDetail] | None = None
    elapsed_ms = (now - attempt.question_started_at).total_seconds() * 1000
    has_answer = (data.answer is not None or data.complex_answer is not None) and question.type != QuizQuestionType.SLIDE
    if has_answer:
        submit_data = SubmitAnswerData(
            question_index=data.question_index,
            answer="" if data.answer is None else data.answer,
            complex_answer=data.complex_answer,
        )
        answer_right, answer, score_credit = check_answer(game, submit_data)
        if question.type == QuizQuestionType.MULTI_TEXT:
            answer_details = build_multi_text_answer_details(
                get_submitted_text_answers(submit_data),
                cast(list[TextQuizAnswer], question.answers),
                question.ignore_whitespace,
            )
        score = calculate_answer_score(
            score_credit,
            game.time_based_scoring,
            elapsed_ms,
            int(float(question.time)),
            question.points,
        )
        if not question.hide_results:
            solution = _solution_question(question)

    attempt.total_score += score
    attempt.answers.append(
        AnswerData(
            username=attempt.username,
            answer=str(answer),
            right=answer_right,
            time_taken=elapsed_ms,
            score=score,
            zone=attempt.zone,
            answer_details=answer_details,
        )
    )
    if attempt.current_question >= len(game.questions) - 1:
        attempt.current_question = len(game.questions)
        attempt.completed = True
    else:
        attempt.awaiting_next_question = True
    await _save_attempt(attempt_id, attempt)

    return SoloAttemptSubmitResponse(
        right=answer_right,
        score=score,
        total_score=attempt.total_score,
        completed=attempt.completed,
        solution=solution,
        answer_details=answer_details,
    )


@router.post("/attempts/{attempt_id}/advance", response_model=SoloAttemptStateResponse)
async def advance_attempt(attempt_id: str):
    attempt = await _get_attempt(attempt_id)
    game = await _get_solo_game(attempt.game_pin)
    if attempt.completed:
        raise HTTPException(status_code=400, detail="attempt already completed")
    if not attempt.awaiting_next_question:
        raise HTTPException(status_code=400, detail="current question is not answered")

    attempt.current_question += 1
    attempt.awaiting_next_question = False
    attempt.question_started_at = datetime.now()
    await _save_attempt(attempt_id, attempt)
    return _state_response(attempt_id, attempt, game)
