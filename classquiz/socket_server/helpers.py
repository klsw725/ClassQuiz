# SPDX-FileCopyrightText: 2025 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0
import aiohttp
from typing import NamedTuple, cast

from classquiz.config import settings
from classquiz.db.models import (
    PlayGame,
    QuizQuestionType,
    TextQuizAnswer,
    ABCDQuizAnswer,
    VotingQuizAnswer,
    RangeQuizAnswer,
    AnswerDataList,
)
from classquiz.socket_server.models import SubmitAnswerData
from .models import SubmitAnswerDataOrderType


class AnswerCheckResult(NamedTuple):
    right: bool
    answer: str
    score_credit: float


async def check_captcha(captcha_data: str) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            if settings.hcaptcha_key is not None:
                try:
                    async with session.post(
                        "https://hcaptcha.com/siteverify",
                        data={
                            "response": captcha_data,
                            "secret": settings.hcaptcha_key,
                        },
                    ) as resp:
                        resp_data = await resp.model_dump_json()
                        if not resp_data["success"]:
                            return
                except KeyError:
                    return False
            elif settings.recaptcha_key is not None:
                async with session.post(
                    "https://www.google.com/recaptcha/api/siteverify",
                    data={
                        "secret": settings.recaptcha_key,
                        "response": captcha_data,
                    },
                ) as resp:
                    try:
                        resp_data = await resp.model_dump_json()
                        if not resp_data["success"]:
                            return False
                    except KeyError:
                        return False
        except TypeError:
            pass
            return False
    return True


def check_answer(game_data: PlayGame, data: SubmitAnswerData) -> AnswerCheckResult:
    q_i = int(float(data.question_index))
    q_type = game_data.questions[q_i].type
    q_answers = game_data.questions[q_i].answers
    q_answer = "" if data.answer is None else str(data.answer)
    if q_type == QuizQuestionType.ABCD:
        answer_right = check_abcd_question(q_answer, cast(list[ABCDQuizAnswer], q_answers))
        return AnswerCheckResult(answer_right, q_answer, float(answer_right))
    elif q_type == QuizQuestionType.RANGE:
        answer_right = check_range_question(q_answer, cast(RangeQuizAnswer, q_answers))
        return AnswerCheckResult(answer_right, q_answer, float(answer_right))
    elif q_type == QuizQuestionType.VOTING:
        return AnswerCheckResult(False, q_answer, 0)
    elif q_type == QuizQuestionType.ORDER:
        return check_order_question(data.complex_answer, q_answer, cast(list[VotingQuizAnswer], q_answers))
    elif q_type == QuizQuestionType.TEXT:
        text_answers = cast(list[TextQuizAnswer], q_answers)
        answer_right = check_text_question(
            q_answer,
            text_answers,
            game_data.questions[q_i].ignore_whitespace,
        )
        return AnswerCheckResult(answer_right, q_answer, float(answer_right))
    elif q_type == QuizQuestionType.MULTI_TEXT:
        text_answers = cast(list[TextQuizAnswer], q_answers)
        submitted_answers = get_submitted_text_answers(data)[: len(text_answers)]
        answer_right, score_credit = check_multi_text_question(
            submitted_answers,
            text_answers,
            game_data.questions[q_i].ignore_whitespace,
        )
        return AnswerCheckResult(answer_right, ", ".join(submitted_answers), score_credit)

    elif q_type == QuizQuestionType.CHECK:
        answer_right = check_check_question(q_answer, cast(list[ABCDQuizAnswer], q_answers))
        return AnswerCheckResult(answer_right, q_answer, float(answer_right))
    else:
        return AnswerCheckResult(False, q_answer, 0)


def check_abcd_question(answer: str, answers: list[ABCDQuizAnswer]) -> bool:
    for a in answers:
        if a.answer == answer and a.right:
            return True
    return False


def check_range_question(answer: str, answers: RangeQuizAnswer) -> bool:
    if answers.min_correct <= int(float(answer)) <= answers.max_correct:
        return answers.min_correct <= int(float(answer)) <= answers.max_correct
    return False


def check_order_question(
    complex_answer: list[SubmitAnswerDataOrderType] | None,
    answer: str,
    answers: list[VotingQuizAnswer],
) -> AnswerCheckResult:
    if complex_answer is None:
        return AnswerCheckResult(False, answer, 0)
    correct_answers = [{"answer": a.answer} for a in answers]
    submitted_answers = [{"answer": a.answer} for a in complex_answer]
    answer_str = ", ".join(a["answer"] for a in submitted_answers)
    is_correct = submitted_answers == correct_answers
    return AnswerCheckResult(is_correct, answer_str, float(is_correct))


def normalize_text_answer(answer: str, ignore_whitespace: bool) -> str:
    if ignore_whitespace:
        return "".join(answer.split())
    return answer


def text_answer_matches(
    submitted_answer: str,
    correct_answer: TextQuizAnswer,
    ignore_whitespace: bool,
) -> bool:
    submitted_answer = normalize_text_answer(submitted_answer, ignore_whitespace)
    answer = normalize_text_answer(correct_answer.answer, ignore_whitespace)
    if correct_answer.case_sensitive:
        return submitted_answer == answer
    return submitted_answer.lower() == answer.lower()


def count_text_matches(
    submitted_answers: list[str],
    answers: list[TextQuizAnswer],
    ignore_whitespace: bool = False,
) -> int:
    matches: list[int | None] = [None] * len(submitted_answers)

    def assign_answer(answer_index: int, seen_submissions: set[int]) -> bool:
        for submitted_index, submitted_answer in enumerate(submitted_answers):
            if submitted_index in seen_submissions or not text_answer_matches(
                submitted_answer,
                answers[answer_index],
                ignore_whitespace,
            ):
                continue
            seen_submissions.add(submitted_index)
            previous_answer_index = matches[submitted_index]
            if previous_answer_index is None or assign_answer(previous_answer_index, seen_submissions):
                matches[submitted_index] = answer_index
                return True
        return False

    return sum(assign_answer(answer_index, set()) for answer_index in range(len(answers)))


def check_text_question(
    answer: str,
    answers: list[TextQuizAnswer],
    ignore_whitespace: bool = False,
) -> bool:
    return any(text_answer_matches(answer, correct_answer, ignore_whitespace) for correct_answer in answers)


def check_multi_text_question(
    submitted_answers: list[str],
    answers: list[TextQuizAnswer],
    ignore_whitespace: bool = False,
) -> tuple[bool, float]:
    if not answers:
        return False, 0
    submitted_answers = submitted_answers[: len(answers)]
    match_count = count_text_matches(submitted_answers, answers, ignore_whitespace)
    score_credit = match_count / len(answers)
    return match_count == len(answers), score_credit


def get_submitted_text_answers(data: SubmitAnswerData) -> list[str]:
    if data.complex_answer is not None:
        return [answer.answer for answer in data.complex_answer]
    return ["" if data.answer is None else str(data.answer)]


def check_check_question(answer: str, answers: list[ABCDQuizAnswer]) -> bool:
    correct_string = ""
    for i, a in enumerate(answers):
        if a.right:
            correct_string += str(i)
    return bool(correct_string == answer)


async def has_already_answered(game_pin: str, q_index: int, username: str, zone: str | None = None) -> bool:
    answers = await AnswerDataList.get_redis_or_empty(game_pin, q_index)
    if answers is None:
        return False
    else:
        answers = list(filter(lambda a: a.username == username and a.zone == zone, answers.root))
        return len(answers) > 0
