# SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0


from types import SimpleNamespace
import uuid
from typing import cast

from classquiz.db.models import Quiz
from classquiz.helpers import (
    check_question_media_string,
    check_youtube_media_string,
    extract_image_ids_from_quiz,
)


def test_check_question_media_string():
    storage_id = str(uuid.uuid4())
    storage_pair = f"{uuid.uuid4()}--{uuid.uuid4()}"

    assert check_question_media_string(storage_id)
    assert check_question_media_string(storage_pair)
    assert check_question_media_string("youtube:AbCdEfGh123")
    assert check_youtube_media_string("youtube:AbCdEfGh123")
    assert not check_question_media_string("https://youtube.com/watch?v=AbCdEfGh123")
    assert not check_youtube_media_string("youtube:AbCdEfGh12")


def test_extract_image_ids_from_quiz_skips_youtube_markers():
    storage_id = str(uuid.uuid4())
    quiz = SimpleNamespace(
        cover_image=storage_id,
        background_image="youtube:AbCdEfGh123",
        questions=[
            {"image": "youtube:AbCdEfGh123"},
            {"image": storage_id},
            {"image": None},
        ],
    )

    assert extract_image_ids_from_quiz(cast(Quiz, quiz)) == [storage_id, storage_id]
