# SPDX-FileCopyrightText: 2025 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0

from pydantic import BaseModel, Field, field_validator, ValidationInfo
from classquiz.db.models import QuizQuestion, QuizQuestionType, VotingQuizAnswer


ALLOWED_ZONES = tuple(f"{zone}구역" for zone in range(1, 12))


class JoinGameData(BaseModel):
    username: str = Field(min_length=2)
    game_pin: str
    zone: str
    captcha: str | None = None
    custom_field: str | None = None

    @field_validator("zone")
    def zone_must_be_allowed(cls, v: str):
        if v not in ALLOWED_ZONES:
            raise ValueError("Zone must be between 1구역 and 11구역")
        return v


class RejoinGameData(BaseModel):
    old_sid: str
    game_pin: str
    username: str = Field(min_length=2)
    zone: str | None = None

    @field_validator("zone")
    def zone_must_be_allowed(cls, v: str | None):
        if v is not None and v not in ALLOWED_ZONES:
            raise ValueError("Zone must be between 1구역 and 11구역")
        return v


class RegisterAsAdminData(BaseModel):
    game_pin: str
    game_id: str


class ABCDQuizAnswerWithoutSolution(BaseModel):
    answer: str
    color: str | None = None
    emoji: str | None = None


class RangeQuizAnswerWithoutSolution(BaseModel):
    min: int
    max: int


class ReturnQuestion(QuizQuestion):
    answers: list[ABCDQuizAnswerWithoutSolution] | RangeQuizAnswerWithoutSolution | list[VotingQuizAnswer]
    type: QuizQuestionType = QuizQuestionType.ABCD

    @field_validator("answers")
    def answers_not_none_if_abcd_type(cls, v, info: ValidationInfo):
        if info.data["type"] == QuizQuestionType.ABCD and type(v[0]) is not ABCDQuizAnswerWithoutSolution:
            raise ValueError("Answers can't be none if type is ABCD")
        if info.data["type"] == QuizQuestionType.RANGE and type(v) is not RangeQuizAnswerWithoutSolution:
            raise ValueError("Answer must be from type RangeQuizAnswer if type is RANGE")
        # skipcq: PTC-W0047
        if info.data["type"] == QuizQuestionType.VOTING and type(v[0]) is not VotingQuizAnswer:
            pass
        return v


class SubmitAnswerDataOrderType(BaseModel):
    answer: str


class SubmitAnswerData(BaseModel):
    question_index: int
    answer: str | int | None = None
    complex_answer: list[SubmitAnswerDataOrderType] | None = Field(default=None, max_length=100)

    @field_validator("answer")
    def answer_is_bounded(cls, v: str | int | None):
        if isinstance(v, str) and len(v) > 1000:
            raise ValueError("answer must be 1000 characters or fewer")
        return v

    @field_validator("complex_answer")
    def complex_answer_items_are_bounded(cls, v: list[SubmitAnswerDataOrderType] | None):
        if v is not None:
            for item in v:
                if len(item.answer) > 1000:
                    raise ValueError("complex answer items must be 1000 characters or fewer")
        return v


class KickPlayerInput(BaseModel):
    username: str
    zone: str | None = None

    @field_validator("zone")
    def zone_must_be_allowed(cls, v: str | None):
        if v is not None and v not in ALLOWED_ZONES:
            raise ValueError("Zone must be between 1구역 and 11구역")
        return v


class ConnectSessionIdEvent(BaseModel):
    session_id: str
