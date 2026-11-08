import http.cookiejar
import json
import re
import sys
import tempfile
import threading
import unittest
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import (
    HTTPRedirectHandler,
    HTTPCookieProcessor,
    Request,
    build_opener,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import app
import store


class NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


class BackendIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_directory = tempfile.TemporaryDirectory()
        cls.original_database_path = store.DATABASE_PATH
        store.DATABASE_PATH = Path(cls.temp_directory.name) / "test.sqlite3"
        store.initialize()
        cls.server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.SmartCampusHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=5)
        store.DATABASE_PATH = cls.original_database_path
        cls.temp_directory.cleanup()

    def setUp(self):
        with store.database_connection() as connection:
            connection.execute("DELETE FROM sessions")
            connection.execute("DELETE FROM credentials")
            connection.execute("DELETE FROM records")
        store.initialize()
        self.cookie_jar = http.cookiejar.CookieJar()
        self.client = build_opener(
            NoRedirectHandler(),
            HTTPCookieProcessor(self.cookie_jar),
        )

    def request(self, method, path, payload=None, csrf=None):
        headers = {}
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload).encode("utf-8")
        if csrf is not None:
            headers["X-CSRFToken"] = csrf
        request = Request(
            self.base_url + path,
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with self.client.open(request, timeout=5) as response:
                return response.status, response.headers, response.read()
        except HTTPError as error:
            return error.code, error.headers, error.read()

    def login(self, email="Antonio.correia@etpm.pt"):
        status, _, _ = self.request(
            "POST",
            "/api/login",
            {"email": email, "password": "demo1234"},
        )
        self.assertEqual(status, 200)

    def csrf_token(self):
        status, _, html = self.request("GET", "/dashboard.html")
        self.assertEqual(status, 200)
        match = re.search(
            rb"window\.SMARTCAMPUS_CONFIG=(\{.*?\});</script>", html, re.DOTALL
        )
        self.assertIsNotNone(match)
        config = json.loads(match.group(1))
        return config["csrfToken"]

    def test_requires_login_and_serves_integrated_frontend_after_login(self):
        status, headers, _ = self.request("GET", "/dashboard.html")
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/login.html")

        self.login()
        status, _, html = self.request("GET", "/dashboard.html")
        self.assertEqual(status, 200)
        self.assertIn(b'id="server-data"', html)
        self.assertIn(b'"mode":"integrado"', html)
        self.assertNotIn(b"dados-demo.js", html)
        data_match = re.search(
            rb'<script type="application/json" id="server-data">(.*?)</script>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(data_match)
        data = json.loads(data_match.group(1))
        self.assertEqual(data["logs"], [])
        self.assertEqual(data["eventos"], [])

    def test_demo_login_rejects_bad_password(self):
        status, _, response = self.request(
            "POST",
            "/api/login",
            {"email": "Antonio.correia@etpm.pt", "password": "wrong"},
        )
        self.assertEqual(status, 401)
        self.assertNotIn(b"wrong", response)

    def test_operation_requires_csrf_and_professor_cannot_create_account(self):
        self.login()
        status, _, _ = self.request(
            "POST",
            "/api/operations/avaria",
            {"id_equipamento": "EQ-001", "data": "2026-11-08T10:00", "motivo": "Teste"},
        )
        self.assertEqual(status, 403)

        status, _, _ = self.request(
            "POST",
            "/api/operations/conta",
            {
                "nome": "Conta não autorizada",
                "email": "nao.autorizado@etpm.pt",
                "perfil": "Professor",
            },
            csrf=self.csrf_token(),
        )
        self.assertEqual(status, 400)
        with store.database_connection() as connection:
            users = store.load_state(connection)["utilizadores"]
            self.assertFalse(
                any(item["email"] == "nao.autorizado@etpm.pt" for item in users)
            )

    def test_damage_operation_updates_equipment_and_audit_atomically(self):
        self.login()
        csrf = self.csrf_token()
        current_time = datetime.now(app.LISBON_TZ).strftime("%Y-%m-%dT%H:%M")
        status, _, response = self.request(
            "POST",
            "/api/operations/avaria",
            {
                "id_equipamento": "EQ-001",
                "data": current_time,
                "motivo": "Teste de avaria",
            },
            csrf=csrf,
        )
        self.assertEqual(status, 200, response.decode("utf-8"))
        with store.database_connection() as connection:
            equipment = store.get_record(connection, "equipamentos", "EQ-001")
            self.assertEqual(equipment["estado"], "Avariado")
            self.assertEqual(equipment["id_local"], "REP")
            state = store.load_state(connection)
            self.assertEqual(len(state["avarias"]), 2)
            self.assertEqual(len(state["transferencias"]), 2)
            self.assertTrue(
                any(item["acao"] == "Equipamento avariado" for item in state["logs"])
            )

    def test_logout_invalidates_session(self):
        self.login()
        csrf = self.csrf_token()
        status, _, _ = self.request("POST", "/api/logout", {}, csrf=csrf)
        self.assertEqual(status, 200)
        status, headers, _ = self.request("GET", "/dashboard.html")
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/login.html")

    def test_assignment_and_return_are_saved(self):
        self.login()
        csrf = self.csrf_token()
        current_time = datetime.now(app.LISBON_TZ).strftime("%Y-%m-%dT%H:%M")
        status, _, response = self.request(
            "POST",
            "/api/operations/atribuicao",
            {
                "id_equipamento": "EQ-001",
                "id_destinatario": "U-03",
                "data": current_time,
                "prazo": "",
            },
            csrf=csrf,
        )
        self.assertEqual(status, 200, response.decode("utf-8"))
        with store.database_connection() as connection:
            assignment = next(
                item
                for item in store.load_state(connection)["atribuicoes"]
                if item["id_equipamento"] == "EQ-001" and not item.get("fim")
            )
        status, _, response = self.request(
            "POST",
            "/api/operations/devolucao",
            {"id_atribuicao": assignment["id"], "data": current_time},
            csrf=csrf,
        )
        self.assertEqual(status, 200, response.decode("utf-8"))
        with store.database_connection() as connection:
            saved = store.get_record(connection, "atribuicoes", assignment["id"])
            self.assertTrue(saved["fim"])
            self.assertEqual(saved["id_utilizador_devolucao"], "U-01")

    def test_repair_exit_requires_confirmation_and_destination(self):
        self.login()
        csrf = self.csrf_token()
        current_time = datetime.now(app.LISBON_TZ).strftime("%Y-%m-%dT%H:%M")
        payload = {
            "tipo_objeto": "equipamento",
            "id_objeto": "EQ-003",
            "id_sala": "S-02",
            "data": current_time,
        }
        status, _, _ = self.request(
            "POST",
            "/api/operations/transferencia",
            payload,
            csrf=csrf,
        )
        self.assertEqual(status, 400)
        status, _, response = self.request(
            "POST",
            "/api/operations/transferencia",
            {**payload, "operacional": "sim"},
            csrf=csrf,
        )
        self.assertEqual(status, 200, response.decode("utf-8"))
        with store.database_connection() as connection:
            equipment = store.get_record(connection, "equipamentos", "EQ-003")
            self.assertEqual(equipment["estado"], "Em funcionamento")
            self.assertEqual(equipment["id_local"], "S-02")

    def test_professor_can_see_assignees_and_three_assignments_are_allowed(self):
        self.login()
        csrf = self.csrf_token()
        current_time = datetime.now(app.LISBON_TZ).strftime("%Y-%m-%dT%H:%M")
        for equipment_id in ("EQ-001", "EQ-004"):
            status, _, response = self.request(
                "POST",
                "/api/operations/atribuicao",
                {
                    "id_equipamento": equipment_id,
                    "id_destinatario": "U-03",
                    "data": current_time,
                    "prazo": "",
                },
                csrf=csrf,
            )
            self.assertEqual(status, 200, response.decode("utf-8"))

        status, _, html = self.request("GET", "/assignacao.html?vista=ativas")
        self.assertEqual(status, 200)
        match = re.search(
            rb'<script type="application/json" id="server-data">(.*?)</script>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        state = json.loads(match.group(1))
        self.assertIn("U-03", [item["id"] for item in state["destinatarios"]])
        self.assertEqual(
            sum(
                item["id_destinatario"] == "U-03" and not item.get("fim")
                for item in state["atribuicoes"]
            ),
            3,
        )

    def test_admin_can_open_assignment_and_return_history_views(self):
        status, _, _ = self.request(
            "POST",
            "/api/login",
            {"email": "admin.demo@etpm.pt", "password": "demo1234"},
        )
        self.assertEqual(status, 200)
        status, _, assignment_html = self.request(
            "GET", "/assignacao.html?vista=ativas"
        )
        self.assertEqual(status, 200)
        status, _, returns_html = self.request(
            "GET", "/devolucao.html?vista=historico"
        )
        self.assertEqual(status, 200)
        match = re.search(
            rb'<script type="application/json" id="server-data">(.*?)</script>',
            returns_html,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        state = json.loads(match.group(1))
        self.assertTrue(any(item.get("fim") for item in state["atribuicoes"]))


if __name__ == "__main__":
    unittest.main()
