# SPDX-FileCopyrightText: 2026 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0

from classquiz.db.models import TextQuizAnswer
from classquiz.socket_server.helpers import check_text_question


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
