# SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0


import json
import uuid
from datetime import datetime

import pytest
from redis import Redis
from classquiz.config import settings
from fastapi import HTTPException
from classquiz.db.models import GameResults
from classquiz.routers import utils as utils_router
from classquiz.routers.box_controller.embedded.socket import submit_answer_fn
from classquiz.tests import test_user_email, test_user_password, example_quiztivity
from classquiz.tests import test_client, example_quiz, ValueStorage  # noqa : F401
from fastapi.testclient import TestClient


# @pytest.fixture
# async def startup_and_shutdown_server():
#     """Start server as test fixture and tear down after test"""
#     print("starting up")
#     server = UvicornTestServer()
#     await server.up()
#     print("Server up")
#     yield
#     await server.down()


class TestUsers:
    @staticmethod
    def log_in(tc: TestClient, email=test_user_email, password=test_user_password) -> int:
        resp = tc.post("/api/v1/login/start", json={"email": email})
        session_id = resp.json()["session_id"]
        resp = tc.post(
            f"/api/v1/login/step/1?session_id={session_id}", json={"auth_type": "PASSWORD", "data": password}
        )
        ValueStorage.cookies = resp.cookies
        return resp.status_code

    @pytest.mark.asyncio
    async def test_create_test_user(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post(
            "/api/v1/users/create",
            json={"email": test_user_email, "password": test_user_password, "username": "mawoka"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == test_user_email
        resp = test_client.post(
            "/api/v1/users/create",
            json={"email": test_user_email, "password": test_user_password, "username": "mawoka"},
        )
        assert resp.status_code == 409
        resp = test_client.post(
            "/api/v1/users/create",
            json={"email": "doesntexist@hidsadawadsdaads.ghsxd", "password": test_user_password, "username": "dieter"},
        )
        assert resp.status_code == 400

        resp = test_client.post(
            "/api/v1/users/create",
            json={
                "email": "doesntexist@hidsadawadsdaads.ghsxd",
                "password": test_user_password,
                "username": "12345678978978978978945632145678",
            },
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_verify_email(self, test_client: TestClient):  # noqa : F811
        user = test_client.get(f"/api/v1/internal/testing/user/{test_user_email}?secret_key={settings().secret_key}")
        assert (test_client.get("/api/v1/users/verify/dasadsasdadsasdsaddassad")).status_code == 404

        test_client.get(f"/api/v1/users/verify/{user.json()['verify_key']}")
        resp = test_client.post("/api/v1/login/start", json={"email": test_user_email})
        assert resp.status_code == 200
        session_id = resp.json()["session_id"]
        resp = test_client.post(
            f"/api/v1/login/step/1?session_id={session_id}", json={"auth_type": "PASSWORD", "data": test_user_password}
        )
        ValueStorage.cookies = resp.cookies
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_check(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/users/check", cookies=ValueStorage.cookies)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_me(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/users/me", cookies=ValueStorage.cookies)
        data = resp.json()
        assert resp.status_code == 200
        assert data["verified"] is True
        assert data["email"] == test_user_email
        assert data["username"] == "mawoka"

    # @pytest.mark.asyncio
    # async def test_logout(self, test_client):  # noqa : F811
    #     resp = test_client.get("/api/v1/users/me", cookies={"access_token": access_token})
    #     assert resp.status_code == 200
    #     resp = test_client.get(
    #         "/api/v1/users/logout", cookies={"rememberme_token": rememberme_token}, allow_redirects=False
    #     )
    #     assert resp.status_code == 302
    #     resp = test_client.get("/api/v1/users/me", cookies={"rememberme_token": rememberme_token})
    #     assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_password_update(self, test_client: TestClient):  # noqa : F811
        resp = test_client.put(
            "/api/v1/users/password/update",
            json={"new_password": "new_password", "old_password": test_user_password},
            cookies=ValueStorage.cookies,
        )
        assert resp.status_code == 200
        resp = test_client.put(
            "/api/v1/users/password/update",
            json={"new_password": "asdsdadsasdaasd", "old_password": "asdasdsadadsasdsadasdasd"},
            cookies=ValueStorage.cookies,
        )
        assert resp.status_code == 400
        resp_code = self.log_in(test_client, password="new_password")
        assert resp_code == 200
        resp = test_client.put(
            "/api/v1/users/password/update",
            json={"new_password": test_user_password, "old_password": "new_password"},
            cookies=ValueStorage.cookies,
        )
        assert resp.status_code == 200
        resp_code = self.log_in(test_client)
        assert resp_code == 200
        response = test_client.get("/api/v1/users/me", cookies=ValueStorage.cookies)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_session(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/users/session", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        assert resp.json()["ip_address"] == "testclient"

    @pytest.mark.asyncio
    async def test_list_sessions(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/users/sessions/list", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_delete_session(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/users/session", cookies=ValueStorage.cookies)
        session_id = resp.json()["id"]
        resp = test_client.delete("/api/v1/users/sessions/" + str(session_id), cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        resp = test_client.delete("/api/v1/users/sessions/asdsadasdasdsad", cookies=ValueStorage.cookies)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_forgotten_password(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post("/api/v1/users/forgot-password", json={"email": test_user_email})
        assert resp.status_code == 200
        resp = test_client.post("/api/v1/users/forgot-password", json={"email": "ddassad@dsa.ads"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_password_with_token(self, test_client: TestClient):  # noqa : F811
        me = test_client.get("/api/v1/users/me", cookies=ValueStorage.cookies).json()
        redis = Redis().from_url(settings().redis)
        redis.set("reset_passwd:_1token_", str(me["id"]))
        redis.set("reset_passwd:_2token_", str(uuid.uuid4()))
        # test wtith wrong token
        resp = test_client.post(
            "/api/v1/users/reset-password", json={"token": "doesnt_exist", "password": "new_password"}
        )
        assert resp.status_code == 400
        resp = test_client.post("/api/v1/users/reset-password", json={"token": "_2token_", "password": "new_password"})
        assert resp.status_code == 400
        resp = test_client.post("/api/v1/users/reset-password", json={"token": "_1token_", "password": "new_password"})
        assert resp.status_code == 200
        self.log_in(test_client, password="new_password")
        test_client.put(
            "/api/v1/users/password/update",
            json={"new_password": test_user_password, "old_password": "new_password"},
            cookies=ValueStorage.cookies,
        )
        redis.flushdb()

    @pytest.mark.asyncio
    async def test_signout_everywhere(self, test_client: TestClient):  # noqa : F811
        resp = test_client.delete("/api/v1/users/signout-everywhere", cookies=ValueStorage.cookies)
        assert resp.status_code == 200


class TestUtils:
    @pytest.mark.asyncio
    async def test_get_ip_data(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/utils/ip-lookup/1.1.1.1", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        assert resp.json()["query"] == "1.1.1.1"

    @pytest.mark.asyncio
    async def test_get_qr(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/utils/qr/12345678")
        assert resp.status_code == 200
        assert resp.headers["Content-Type"] == "image/svg+xml"

    @pytest.mark.asyncio
    async def test_get_solo_qr(self, test_client: TestClient, monkeypatch):  # noqa : F811
        payloads: list[tuple[str, bool]] = []

        def fake_get_svg_qr_bytes(payload: str, dark_mode: bool = False) -> bytes:
            payloads.append((payload, dark_mode))
            return b"<svg></svg>"

        monkeypatch.setattr(utils_router, "_get_svg_qr_bytes", fake_get_svg_qr_bytes)
        resp = test_client.get("/api/v1/utils/qr/solo/123456", params={"token": "test token+&="})
        assert resp.status_code == 200
        assert resp.headers["Content-Type"] == "image/svg+xml"
        assert resp.headers["Cache-Control"] == "no-store"
        assert payloads == [
            (f"{settings().root_address}/solo?pin=123456&token=test+token%2B%26%3D", False)
        ]


class TestStats:
    @pytest.mark.asyncio
    async def test_get_quiz_count(self, test_client: TestClient):  # noqa : F811
        redis = Redis().from_url(settings().redis)
        redis.flushdb()
        for _ in range(2):
            resp = test_client.get("/api/v1/stats/quizzes")
            assert resp.status_code == 200
            assert resp.text == str(0)

    @pytest.mark.asyncio
    async def test_get_user_count(self, test_client: TestClient):  # noqa : F811
        redis = Redis().from_url(settings().redis)
        redis.flushdb()
        for _ in range(2):
            resp = test_client.get("/api/v1/stats/users")
            assert resp.status_code == 200
            assert resp.text == str(1)

    @pytest.mark.asyncio
    async def test_get_combined_count(self, test_client: TestClient):  # noqa : F811
        redis = Redis().from_url(settings().redis)
        redis.flushdb()
        for _ in range(2):
            resp = test_client.get("/api/v1/stats/combined")
            assert resp.status_code == 200
            assert resp.json()["quiz_count"] == 0
            assert resp.json()["user_count"] == 1


class TestQuiz:
    @pytest.mark.asyncio
    async def test_create_quiz(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post("/api/v1/editor/start?edit=false", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        edit_token = resp.json()["token"]
        assert len(edit_token) == 8
        resp = test_client.post(
            f"/api/v1/editor/finish?edit_id={edit_token}", json=example_quiz, cookies=ValueStorage.cookies
        )
        assert resp.status_code == 200
        resp = test_client.get("/api/v1/quiz/list", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        ValueStorage.quiz_id = data[0]["id"]

    @pytest.mark.asyncio
    async def test_get_quiz_from_id(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get(f"/api/v1/quiz/get/{ValueStorage.quiz_id}", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        resp = test_client.get("/api/v1/quiz/get/dasdsadsadsadsadsa", cookies=ValueStorage.cookies)
        assert resp.status_code == 400
        resp = test_client.get("/api/v1/quiz/get/847c64d3-39f9-4bb7-8f13-fae913f67858", cookies=ValueStorage.cookies)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_quizzes(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/quiz/list", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        assert resp.json()[0]["id"] == ValueStorage.quiz_id

    @pytest.mark.asyncio
    async def test_update_quiz(self, test_client: TestClient):  # noqa : F811
        example_quiz["public"] = True
        resp = test_client.post(
            f"/api/v1/editor/start?edit=true&quiz_id={ValueStorage.quiz_id}", cookies=ValueStorage.cookies
        )
        edit_id = resp.json()["token"]
        resp = test_client.post(
            f"/api/v1/editor/finish?edit_id={edit_id}", json=example_quiz, cookies=ValueStorage.cookies
        )
        assert resp.status_code == 200
        resp = test_client.post(
            "/api/v1/editor/start?edit=true&quiz_id=f183e091-a863-44ec-a1b7-c70eb92e3f6a", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 404
        resp = test_client.post("/api/v1/editor/start?edit=true&quiz_id=asddasasdasdads", cookies=ValueStorage.cookies)
        assert resp.status_code == 422
        example_quiz["public"] = False
        resp = test_client.post(
            f"/api/v1/editor/start?edit=true&quiz_id={ValueStorage.quiz_id}", cookies=ValueStorage.cookies
        )
        edit_id = resp.json()["token"]
        test_client.post(f"/api/v1/editor/finish?edit_id={edit_id}", json=example_quiz, cookies=ValueStorage.cookies)
        example_quiz["public"] = True
        resp = test_client.post(
            f"/api/v1/editor/start?edit=true&quiz_id={ValueStorage.quiz_id}", cookies=ValueStorage.cookies
        )
        edit_id = resp.json()["token"]
        test_client.post(f"/api/v1/editor/finish?edit_id={edit_id}", json=example_quiz, cookies=ValueStorage.cookies)

    @pytest.mark.asyncio
    async def test_import_quiz(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post(
            "/api/v1/quiz/import/1f95eb0b-fcf4-4db2-879b-5418ef75116b", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 200
        ValueStorage.imported_quizzes.append(resp.json()["id"])
        resp = test_client.post("/api/v1/quiz/import/1f95eb0bdassdadasdas", cookies=ValueStorage.cookies)
        assert resp.text == '"quiz not found"'

    @pytest.mark.asyncio
    async def test_get_public_quiz(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get(f"/api/v1/quiz/get/public/{ValueStorage.imported_quizzes[0]}")
        assert resp.status_code == 200
        resp = test_client.get(
            "/api/v1/quiz/get/public/f183e091-a863-44ec-a1b7-c70eb92e3f6a", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 404
        resp = test_client.get("/api/v1/quiz/get/public/dadasdas92e3f6a", cookies=ValueStorage.cookies)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_search_get(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/search/?q=*")
        assert resp.status_code == 200
        assert len(resp.json()["hits"]) > 0

    @pytest.mark.asyncio
    async def test_search_post(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post("/api/v1/search/", json={"q": "*"})
        assert resp.status_code == 200
        assert len(resp.json()["hits"]) > 0

    @pytest.mark.asyncio
    async def test_image_cdn(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get(f"/api/v1/quiz/get/public/{ValueStorage.imported_quizzes[0]}")
        assert resp.status_code == 200
        quiz = resp.json()
        image_id = quiz["questions"][0]["image"]
        # resp = test_client.get(f"/api/v1/storage/download/{image_id}")
        # print(resp.text)
        # assert resp.status_code == 200 This fails because I don't know
        resp = test_client.get(f"/api/v1/storage/download/{image_id}sadgvsadgvhsad")
        assert resp.status_code == 400


class TestPlayQuiz:
    @pytest.mark.asyncio
    async def test_start_quiz(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post(
            "/api/v1/quiz/start/fb5adc91-629e-416e-8b98-ae400e36417c?game_mode=kahoot", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 404
        resp = test_client.post(
            "/api/v1/quiz/start/fb5adc91-629e-416e-8b98-ae400sdadsasadsadasddsae36417c?game_mode=kahoot",
            cookies=ValueStorage.cookies,
        )
        assert resp.status_code == 400
        resp = test_client.post(
            f"/api/v1/quiz/start/{ValueStorage.quiz_id}?game_mode=kahoot", cookies=ValueStorage.cookies
        )
        ValueStorage.game_pin = resp.json()["game_pin"]
        ValueStorage.game_id = resp.json()["game_id"]

    @pytest.mark.asyncio
    async def test_start_solo_quiz(self, test_client: TestClient):  # noqa : F811
        redis = Redis().from_url(settings().redis)
        me = test_client.get("/api/v1/users/me", cookies=ValueStorage.cookies).json()
        lobby_key = f"game_in_lobby:{uuid.UUID(me['id']).hex}"
        lobby_before = redis.get(lobby_key)
        live_alias_key = f"game_pin:{me['id']}:{ValueStorage.quiz_id}"
        live_alias_before = redis.get(live_alias_key)
        resp = test_client.post(
            f"/api/v1/quiz/start/{ValueStorage.quiz_id}?game_mode=solo&cqcs_enabled=true", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 200
        data = resp.json()
        ValueStorage.solo_game_pin = data["game_pin"]
        ValueStorage.solo_token = data["solo_token"]
        assert data["game_mode"] == "solo"
        assert data["solo_token"] is not None
        assert data["cqc_code"] is None
        assert redis.get(lobby_key) == lobby_before
        assert redis.get(live_alias_key) == live_alias_before
        stored_game = json.loads(redis.get(f"game:{ValueStorage.solo_game_pin}"))
        assert stored_game["solo_token"] == ValueStorage.solo_token
        solo_game_ttl = redis.ttl(f"game:{ValueStorage.solo_game_pin}")
        assert 29 * 24 * 60 * 60 < solo_game_ttl <= 30 * 24 * 60 * 60
        assert redis.get(f"game_session:{ValueStorage.solo_game_pin}") is None

    @pytest.mark.asyncio
    async def test_solo_multi_text_question_does_not_expose_answer_before_submit(self, test_client: TestClient):  # noqa : F811
        redis = Redis().from_url(settings().redis)
        solo_text_game_pin = "654321"
        solo_text_token = "solo-text-token"
        stored_game = json.loads(redis.get(f"game:{ValueStorage.solo_game_pin}"))
        stored_game["game_pin"] = solo_text_game_pin
        stored_game["solo_token"] = solo_text_token
        stored_game["questions"] = [
            {
                "type": "MULTI_TEXT",
                "question": "Type the secret",
                "time": 10,
                "answers": [{"answer": "secret answer", "case_sensitive": False}],
                "hide_results": False,
            }
        ]
        redis.set(f"game:{solo_text_game_pin}", json.dumps(stored_game), ex=18000)
        resp = test_client.post(
            "/api/v1/solo/attempts",
            json={
                "game_pin": solo_text_game_pin,
                "solo_token": solo_text_token,
                "username": "Solo Text Player",
                "zone": "1구역",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["question"]["answers"] == [{"answer": "", "case_sensitive": False}]
        assert "secret answer" not in json.dumps(data["question"])

        resp = test_client.post(
            f"/api/v1/solo/attempts/{data['attempt_id']}/submit",
            json={"question_index": 0, "answer": "secret answer"},
        )
        assert resp.status_code == 200
        assert resp.json()["solution"]["answers"] == [{"answer": "", "case_sensitive": False}]
        assert "secret answer" not in json.dumps(resp.json()["solution"])

    @pytest.mark.asyncio
    async def test_reject_solo_game_in_live_rest_endpoints(self, test_client: TestClient):  # noqa : F811
        redis = Redis().from_url(settings().redis)
        me = test_client.get("/api/v1/users/me", cookies=ValueStorage.cookies).json()
        api_key = "solo-live-test-api-key"
        redis.set(f"apikey:{api_key}", me["id"], ex=3600)
        stored_before = json.loads(redis.get(f"game:{ValueStorage.solo_game_pin}"))
        assert stored_before["current_question"] == -1

        live_requests = [
            ("get", "/api/v1/live/"),
            ("get", "/api/v1/live/user_count"),
            ("get", "/api/v1/live/players"),
            ("get", "/api/v1/live/scores"),
            ("get", "/api/v1/live/get_question/now"),
            ("get", "/api/v1/live/voting"),
            ("post", "/api/v1/live/set_question"),
        ]
        for method, path in live_requests:
            resp = getattr(test_client, method)(
                path,
                params={"game_pin": ValueStorage.solo_game_pin, "api_key": api_key, "question_number": 0},
            )
            assert resp.status_code == 404

        live_alias_key = f"game_pin:{me['id']}:{ValueStorage.quiz_id}"
        live_alias_before = redis.get(live_alias_key)
        redis.set(live_alias_key, ValueStorage.solo_game_pin, ex=18000)
        resp = test_client.get(
            "/api/v1/live/scores",
            params={"game_pin": ValueStorage.quiz_id, "api_key": api_key},
        )
        assert resp.status_code == 404
        if live_alias_before is None:
            redis.delete(live_alias_key)
        else:
            redis.set(live_alias_key, live_alias_before, ex=18000)

        stored_after = json.loads(redis.get(f"game:{ValueStorage.solo_game_pin}"))
        assert stored_after["current_question"] == -1

    @pytest.mark.asyncio
    async def test_reject_solo_game_in_cqc_submit_answer(self, test_client: TestClient):  # noqa : F811
        redis = Redis().from_url(settings().redis)
        redis.set("game:cqc:player:solo-player", "Solo Player", ex=60)
        with pytest.raises(HTTPException) as exc_info:
            await submit_answer_fn(0, ValueStorage.solo_game_pin, "solo-player", datetime.now())
        assert exc_info.value.status_code == 404
        assert redis.hgetall(f"game_session:{ValueStorage.solo_game_pin}:player_scores") == {}

    @pytest.mark.asyncio
    async def test_create_solo_attempt(self, test_client: TestClient):  # noqa : F811
        ValueStorage.solo_results_count = await GameResults.objects.count()
        for game_pin in ["12345", "1234567", "abcdef", "12345a"]:
            resp = test_client.post(
                "/api/v1/solo/attempts",
                json={
                    "game_pin": game_pin,
                    "solo_token": ValueStorage.solo_token,
                    "username": "Solo Player",
                    "zone": "3구역",
                },
            )
            assert resp.status_code == 422
        resp = test_client.post(
            "/api/v1/solo/attempts",
            json={
                "game_pin": ValueStorage.solo_game_pin,
                "solo_token": ValueStorage.solo_token,
                "username": "Solo Player",
                "zone": "12구역",
            },
        )
        assert resp.status_code == 422
        resp = test_client.post(
            "/api/v1/solo/attempts",
            json={"game_pin": ValueStorage.solo_game_pin, "username": "Solo Player", "zone": "3구역"},
        )
        assert resp.status_code == 404
        resp = test_client.post(
            "/api/v1/solo/attempts",
            json={
                "game_pin": ValueStorage.solo_game_pin,
                "solo_token": "wrong",
                "username": "Solo Player",
                "zone": "3구역",
            },
        )
        assert resp.status_code == 404
        resp = test_client.post(
            "/api/v1/solo/attempts",
            json={
                "game_pin": ValueStorage.solo_game_pin,
                "solo_token": ValueStorage.solo_token,
                "username": "Solo Player",
                "zone": "3구역",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        ValueStorage.solo_attempt_id = data["attempt_id"]
        assert data["game_pin"] == ValueStorage.solo_game_pin
        assert data["username"] == "Solo Player"
        assert data["zone"] == "3구역"
        assert data["current_question"] == 0
        assert data["completed"] is False
        assert data["awaiting_next_question"] is False
        assert data["question"]["answers"][0].get("right") is None
        redis = Redis().from_url(settings().redis)
        stored_attempt = json.loads(redis.get(f"solo_attempt:{ValueStorage.solo_attempt_id}"))
        assert stored_attempt["zone"] == "3구역"

    @pytest.mark.asyncio
    async def test_reject_oversized_solo_submit_payloads(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post(
            f"/api/v1/solo/attempts/{ValueStorage.solo_attempt_id}/submit",
            json={"question_index": 0, "answer": "x" * 1001},
        )
        assert resp.status_code == 422
        resp = test_client.post(
            f"/api/v1/solo/attempts/{ValueStorage.solo_attempt_id}/submit",
            json={"question_index": 0, "answer": "Yes", "complex_answer": [{"answer": "x" * 1001}]},
        )
        assert resp.status_code == 422
        resp = test_client.post(
            f"/api/v1/solo/attempts/{ValueStorage.solo_attempt_id}/submit",
            json={"question_index": 0, "answer": "Yes", "complex_answer": [{"answer": "Yes"}] * 101},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_answer_first_solo_question(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post(
            f"/api/v1/solo/attempts/{ValueStorage.solo_attempt_id}/submit",
            json={"question_index": 0, "answer": "Yes"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["right"] is True
        assert data["score"] > 0
        assert data["total_score"] == data["score"]
        assert data["completed"] is False
        assert "next_question" not in data
        resp = test_client.post(
            f"/api/v1/solo/attempts/{ValueStorage.solo_attempt_id}/submit",
            json={"question_index": 0, "answer": "Yes"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_advance_solo_attempt(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post(f"/api/v1/solo/attempts/{ValueStorage.solo_attempt_id}/advance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_question"] == 1
        assert data["completed"] is False
        assert data["awaiting_next_question"] is False
        assert data["question"]["answers"][0].get("right") is None

    @pytest.mark.asyncio
    async def test_complete_second_solo_question(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post(
            f"/api/v1/solo/attempts/{ValueStorage.solo_attempt_id}/submit",
            json={"question_index": 1, "answer": "Yes"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["right"] is True
        assert data["completed"] is True
        assert "next_question" not in data
        redis = Redis().from_url(settings().redis)
        stored_attempt = json.loads(redis.get(f"solo_attempt:{ValueStorage.solo_attempt_id}"))
        assert stored_attempt["current_question"] == 2
        assert stored_attempt["awaiting_next_question"] is False
        assert stored_attempt["answers"][0]["zone"] == "3구역"
        assert stored_attempt["answers"][1]["zone"] == "3구역"
        assert redis.get(f"solo_attempt:{ValueStorage.solo_attempt_id}") is not None
        assert redis.get(f"game_session:{ValueStorage.solo_game_pin}") is None
        assert redis.hgetall(f"game:{ValueStorage.solo_game_pin}:players:zones") == {}
        assert await GameResults.objects.count() == ValueStorage.solo_results_count

    @pytest.mark.asyncio
    async def test_reject_live_game_pin_for_solo_attempt(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post(
            "/api/v1/solo/attempts",
            json={
                "game_pin": ValueStorage.game_pin,
                "solo_token": ValueStorage.solo_token,
                "username": "Solo Player",
                "zone": "3구역",
            },
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_check_captcha_enabled(self, test_client: TestClient):  # noqa : F811
        res = test_client.get(f"/api/v1/quiz/play/check_captcha/{ValueStorage.game_pin}")
        assert res.status_code == 200
        assert res.json()["enabled"] is True

        res = test_client.get("/api/v1/quiz/play/check_captcha/dsadsadas")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_join_game_route(self, test_client: TestClient):  # noqa : F811
        res = test_client.get(f"/api/v1/quiz/join/{ValueStorage.solo_game_pin}")
        assert res.status_code == 404
        res = test_client.get(f"/api/v1/quiz/join/{ValueStorage.game_pin}")
        assert res.status_code == 200
        assert res.text == f'"{ValueStorage.game_id}"'
        res = test_client.get("/api/v1/quiz/join/dsadasdasdas")
        assert res.status_code == 404


# skipcq: PYL-W0105
"""
class TestCache:
    @pytest.mark.asyncio
    async def test_cache_get_by_username(self, test_client):
        user = await get_user_from_username("mawoka")
        user = await get_user_from_username("mawoka")

    @pytest.mark.asyncio
    async def test_cache_get_by_id(self, test_client):
        resp = test_client.post(
            "/api/v1/users/token/cookie", data={"username": test_user_email, "password": test_user_password}
        )
        token = resp.cookies["access_token"]
        resp = test_client.get("/api/v1/users/me", cookies=ValueStorage.cookies)
        user = await get_user_from_id(resp.json()["id"])
"""


class TestCommunity:
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, test_client: TestClient):  # noqa : F811
        user = test_client.get("/api/v1/users/me", cookies=ValueStorage.cookies)
        user_id = user.json()["id"]
        resp = test_client.get(f"/api/v1/community/user/{user_id}")
        assert resp.status_code == 200
        resp = test_client.get("/api/v1/community/user/e673c9ca-0cdf-4ebf-bad2-7d009ef5c62b")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_quizzes_from_user(self, test_client: TestClient):  # noqa : F811
        user = test_client.get("/api/v1/users/me", cookies=ValueStorage.cookies)
        user_id = user.json()["id"]
        resp = test_client.get(f"/api/v1/community/quizzes/{user_id}")
        data = resp.json()
        assert type(data) is list


class TestSitemap:
    @pytest.mark.asyncio
    async def test_get_sitemap(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/sitemap/get")
        assert resp.status_code == 200
        resp = test_client.get("/api/v1/sitemap/get")
        assert resp.status_code == 200


class TestStorage:
    @pytest.mark.asyncio
    async def test_upload_file(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post(
            "/api/v1/storage/", cookies=ValueStorage.cookies, files={"file": ("img.svg", "svg_content")}
        )
        assert resp.status_code == 200
        data = resp.json()
        ValueStorage.file_id = data["id"]
        resp = test_client.post(
            "/api/v1/storage/",
            cookies=ValueStorage.cookies,
            files={"file": ("song.mp3", b"mp3_content", "audio/mpeg")},
        )
        assert resp.status_code == 200
        resp = test_client.post(
            "/api/v1/storage/",
            cookies=ValueStorage.cookies,
            files={"file": ("note.txt", b"text_content", "text/plain")},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_raw_file(self, test_client: TestClient):  # noqa : F811
        resp = test_client.request(
            "POST",
            "/api/v1/storage/raw",
            data=b"data!",
            headers={"Content-Type": "image/svg+xml"},
            cookies=ValueStorage.cookies,
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_file_info(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/storage/meta/dsadsaasdas", cookies=ValueStorage.cookies)
        assert resp.status_code == 422
        resp = test_client.get(
            "/api/v1/storage/meta/35c4f635-906a-46d7-8ab8-0520105ffff5", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 404
        resp = test_client.get(f"/api/v1/storage/meta/{ValueStorage.file_id}", cookies=ValueStorage.cookies)
        data = resp.json()
        assert data["size"] == 0
        assert data["imported"] is False
        assert data["alt_text"] is None
        assert data["filename"] is None
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_image_data(self, test_client: TestClient):  # noqa : F811
        resp = test_client.put(
            f"/api/v1/storage/meta/{ValueStorage.file_id}",
            json={"alt_text": "Alt", "filename": "Filename"},
            cookies=ValueStorage.cookies,
        )
        assert resp.status_code == 200
        resp = test_client.put(
            f"/api/v1/storage/meta/{ValueStorage.file_id}",
            json={"alt_text": "", "filename": ""},
            cookies=ValueStorage.cookies,
        )
        assert resp.status_code == 200
        resp = test_client.get(f"/api/v1/storage/meta/{ValueStorage.file_id}", cookies=ValueStorage.cookies)
        data = resp.json()
        assert data["alt_text"] is None
        assert data["filename"] is None

    @pytest.mark.asyncio
    async def test_list_images(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/storage/list", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert type(data) is list
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_get_latest_images(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/storage/list/last", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert type(data) is list
        assert len(data) >= 2
        resp = test_client.get("/api/v1/storage/list/last?count=1", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        # assert len(data) == 1

    @pytest.mark.asyncio
    async def test_get_storage_limit(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/storage/limit", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit_reached"] is False
        assert type(data["limit"]) is int
        assert data["used"] == 0


class TestQuizivity:
    @pytest.mark.asyncio
    async def test_create_quiztivity(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post("/api/v1/quiztivity/create", cookies=ValueStorage.cookies, json=example_quiztivity)
        assert resp.status_code == 200
        data = resp.json()
        ValueStorage.quiztivity_id = data["id"]

    @pytest.mark.asyncio
    async def test_get_quiztivity(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/quiztivity/8bd77201-65ed-46fe-9160-cfe71dad501f", cookies=ValueStorage.cookies)
        assert resp.status_code == 404
        resp = test_client.get(f"/api/v1/quiztivity/{ValueStorage.quiztivity_id}", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == ValueStorage.quiztivity_id

    @pytest.mark.asyncio
    async def test_put_quiztivity(self, test_client: TestClient):  # noqa : F811
        example_quiztivity["title"] = "New title"
        resp = test_client.put(
            f"/api/v1/quiztivity/{ValueStorage.quiztivity_id}", json=example_quiztivity, cookies=ValueStorage.cookies
        )
        assert resp.status_code == 200
        resp = test_client.put(
            "/api/v1/quiztivity/8bd77201-65ed-46fe-9160-cfe71dad501f",
            json=example_quiztivity,
            cookies=ValueStorage.cookies,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_all_quiztivities(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/quiztivity/", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert type(data) is list
        assert data[0]["id"] == ValueStorage.quiztivity_id

    @pytest.mark.asyncio
    async def test_create_share(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post(
            "/api/v1/quiztivity/shares/",
            cookies=ValueStorage.cookies,
            json={"quiztivity": ValueStorage.quiztivity_id, "expire_in": None},
        )
        assert resp.status_code == 200
        data = resp.json()
        ValueStorage.share_id = data["id"]
        resp = test_client.post(
            "/api/v1/quiztivity/shares/",
            cookies=ValueStorage.cookies,
            json={"quiztivity": "a090077f-9059-42bc-9783-f2cd01e069b8", "expire_in": None},
        )
        assert resp.status_code == 400
        resp = test_client.post(
            "/api/v1/quiztivity/shares/",
            cookies=ValueStorage.cookies,
            json={"quiztivity": ValueStorage.quiztivity_id, "expire_in": 0},
        )
        data = resp.json()
        ValueStorage.expired_share_id = data["id"]
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_share(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get(
            "/api/v1/quiztivity/shares/8bd77201-65ed-46fe-9160-cfe71dad501f", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 404
        resp = test_client.get(f"/api/v1/quiztivity/shares/{ValueStorage.share_id}", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == ValueStorage.quiztivity_id
        resp = test_client.get(
            f"/api/v1/quiztivity/shares/{ValueStorage.expired_share_id}", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 410

    @pytest.mark.asyncio
    async def test_update_share(self, test_client: TestClient):  # noqa : F811
        resp = test_client.put(
            "/api/v1/quiztivity/shares/8bd77201-65ed-46fe-9160-cfe71dad501f",
            cookies=ValueStorage.cookies,
            json={"expire_in": 50},
        )
        assert resp.status_code == 404
        resp = test_client.put(
            f"/api/v1/quiztivity/shares/{ValueStorage.share_id}", cookies=ValueStorage.cookies, json={"expire_in": 50}
        )
        assert resp.status_code == 200

    async def test_delete_share(self, test_client: TestClient):  # noqa : F811
        resp = test_client.delete(
            "/api/v1/quiztivity/shares/8bd77201-65ed-46fe-9160-cfe71dad501f", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 404
        resp = test_client.delete(
            f"/api/v1/quiztivity/shares/{ValueStorage.expired_share_id}", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_shares(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/quiztivity/shares/", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert type(data) is list
        assert data[0]["id"] == ValueStorage.share_id
        assert data[0]["expire_in"] == 49

    @pytest.mark.asyncio
    async def test_get_shares_by_quiztivity(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get(f"/api/v1/quiztivity/{ValueStorage.quiztivity_id}/shares", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert type(data) is list
        assert data[0]["id"] == ValueStorage.share_id

    @pytest.mark.asyncio
    async def test_get_shares(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/quiztivity/shares/", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert type(data) is list
        assert data[0]["id"] == ValueStorage.share_id

    @pytest.mark.asyncio
    async def test_delete_quiztivity(self, test_client: TestClient):  # noqa : F811
        test_client.delete(f"/api/v1/quiztivity/shares/{ValueStorage.share_id}", cookies=ValueStorage.cookies)
        resp = test_client.delete(
            "/api/v1/quiztivity/8bd77201-65ed-46fe-9160-cfe71dad501f", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 404
        resp = test_client.delete(f"/api/v1/quiztivity/{ValueStorage.quiztivity_id}", cookies=ValueStorage.cookies)
        assert resp.status_code == 200


class TestAvatar:
    @pytest.mark.asyncio
    async def test_get_customized_avatar(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/avatar/custom?skin_color=69", cookies=ValueStorage.cookies)
        assert resp.status_code == 400
        resp = test_client.get("/api/v1/avatar/custom", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        assert "image/svg+xml" in resp.headers.get("Content-Type")

    @pytest.mark.asyncio
    async def test_save_avatar(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post("/api/v1/avatar/save?skin_color=69", cookies=ValueStorage.cookies)
        assert resp.status_code == 400
        resp = test_client.post("/api/v1/avatar/save", cookies=ValueStorage.cookies)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_own_avatar(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/users/avatar", cookies=ValueStorage.cookies)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_other_avatar(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get(
            "/api/v1/users/8bd77201-65ed-46fe-9160-cfe71dad501f/avatar", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 404
        user_id = test_client.get("/api/v1/users/me", cookies=ValueStorage.cookies).json()["id"]
        resp = test_client.get(f"/api/v1/users/avatar/{user_id}", cookies=ValueStorage.cookies)
        assert resp.status_code == 200


class TestExImport:
    @pytest.mark.asyncio
    async def test_export_quiz(self, test_client: TestClient):  # noqa : F811
        resp = test_client.get("/api/v1/eximport/jgfgufgfgfzftzi", cookies=ValueStorage.cookies)
        assert resp.status_code == 422
        resp = test_client.get("/api/v1/eximport/8bd77201-65ed-46fe-9160-cfe71dad501f", cookies=ValueStorage.cookies)
        assert resp.status_code == 404
        resp = test_client.get(f"/api/v1/eximport/{ValueStorage.quiz_id}", cookies=ValueStorage.cookies)
        assert resp.status_code == 200
        exported_data = resp.content
        assert len(exported_data) < 3000
        ValueStorage.exported_quiz_data = exported_data

    @pytest.mark.asyncio
    async def test_import_quiz(self, test_client: TestClient):  # noqa : F811
        resp = test_client.post(
            "/api/v1/eximport/", files={"file": ValueStorage.exported_quiz_data}, cookies=ValueStorage.cookies
        )
        assert resp.status_code == 200


class TestDeleteStuff:
    @pytest.mark.asyncio
    async def test_delete_quiz(self, test_client: TestClient):  # noqa : F811
        resp = test_client.delete(
            f"/api/v1/quiz/delete/{ValueStorage.imported_quizzes[0]}", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 200
        resp = test_client.delete(
            "/api/v1/quiz/delete/be582c77-da03-4271-929c-5d582056eb78", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 404

        resp = test_client.delete(
            "/api/v1/quiz/delete/be582c77-da03-sdaasdadsasddas4271-929c-5d582056eb78", cookies=ValueStorage.cookies
        )
        assert resp.status_code == 400

    # @pytest.mark.asyncio
    # async def test_delete_user(self, test_client: TestClient):  # noqa : F811
    #     data = {"password": test_user_password}
    #     resp = test_client.delete("/api/v1/users/me", cookies=ValueStorage.cookies, json=data)
    #     assert resp.status_code == 200
