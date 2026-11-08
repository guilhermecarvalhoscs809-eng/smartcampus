"""Single-process HTTP/API draft for running the SmartCampus V1 demo."""

from __future__ import annotations

import copy
import calendar
import json
import re
import secrets
import sqlite3
import uuid
from datetime import date, datetime, timedelta, timezone, tzinfo
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from store import (
    ROOT,
    database_connection,
    get_record,
    hash_password,
    initialize,
    load_state,
    replace_state,
    verify_password,
)


HOST = "127.0.0.1"
PORT = 8766
SESSION_COOKIE = "smartcampus_session"
SESSION_HOURS = 8
MAX_REQUEST_BYTES = 1_000_000
EMAIL_RE = re.compile(r"^[^\s@]+@etpm\.pt$", re.IGNORECASE)
PAGES = {
    "dashboard",
    "equipamentos",
    "registar-equipamento",
    "salas",
    "armarios",
    "assignacao",
    "devolucao",
    "avaria",
    "transferencia",
    "utilizacoes",
    "eventos",
    "logs",
    "utilizadores",
    "criar-utilizador",
    "login",
}
PERMISSIONS = {
    "Professor": {
        "dashboard",
        "equipamentos",
        "salas",
        "armarios",
        "assignacao",
        "devolucao",
        "avaria",
        "transferencia",
        "utilizadores",
    },
    "Administrador": PAGES - {"login"},
}
ACTION_PAGES = {
    "equipamento": "registar-equipamento",
    "sala": "admin",
    "armario": "admin",
    "conta": "admin",
    "estadoConta": "admin",
    "ocultarLog": "admin",
    "atribuicao": "assignacao",
    "devolucao": "devolucao",
    "avaria": "avaria",
    "transferencia": "transferencia",
}
PAGE_TITLES = {
    "login": "Iniciar sessão",
    "dashboard": "Dashboard",
    "equipamentos": "Equipamentos",
    "registar-equipamento": "Ficha de equipamento",
    "salas": "Salas",
    "armarios": "Armários",
    "assignacao": "Atribuir equipamento",
    "devolucao": "Registar devolução",
    "avaria": "Marcar como avariado",
    "transferencia": "Transferências",
    "utilizacoes": "Histórico de utilização",
    "eventos": "Eventos",
    "logs": "Logs de auditoria",
    "utilizadores": "Utilizadores",
    "criar-utilizador": "Ficha de utilizador",
}


class OperationError(Exception):
    """Expected validation or authorization failure for a submitted operation."""


class LisbonTimeZone(tzinfo):
    """EU Lisbon daylight-saving rules fallback for Windows without tzdata."""

    @staticmethod
    def last_sunday(year: int, month: int) -> int:
        last_day = calendar.monthrange(year, month)[1]
        return last_day - (date(year, month, last_day).weekday() - 6) % 7

    def _is_daylight(self, value: datetime) -> bool:
        if value.year < 1996:
            return False
        start = self.last_sunday(value.year, 3)
        end = self.last_sunday(value.year, 10)
        if value.month < 3 or value.month > 10:
            return False
        if 3 < value.month < 10:
            return True
        if value.month == 3:
            if value.day != start:
                return value.day > start
            if value.hour < 1:
                return False
            if value.hour == 1:
                raise OperationError("A hora local indicada não existe na mudança de hora.")
            return True
        if value.day != end:
            return value.day < end
        if value.hour == 1:
            return value.fold == 0
        return value.hour < 1

    def utcoffset(self, value: datetime | None):
        if value is None:
            return timedelta(0)
        return timedelta(hours=1 if self._is_daylight(value) else 0)

    def dst(self, value: datetime | None):
        if value is None:
            return timedelta(0)
        return timedelta(hours=1 if self._is_daylight(value) else 0)

    def tzname(self, value: datetime | None):
        return "WEST" if value and self._is_daylight(value) else "WET"

    def fromutc(self, value: datetime) -> datetime:
        if value.tzinfo is not self:
            raise ValueError("fromutc requires a datetime with this timezone")
        if value.year < 1996:
            return value
        start = datetime(value.year, 3, self.last_sunday(value.year, 3), 1)
        end = datetime(value.year, 10, self.last_sunday(value.year, 10), 1)
        utc_value = value.replace(tzinfo=None)
        daylight = start <= utc_value < end
        fold = int(end <= utc_value < end + timedelta(hours=1))
        local = utc_value + timedelta(hours=1 if daylight else 0)
        return local.replace(tzinfo=self, fold=fold)


try:
    LISBON_TZ: tzinfo = ZoneInfo("Europe/Lisbon")
except ZoneInfoNotFoundError:
    LISBON_TZ = LisbonTimeZone()


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def normalized(value: Any) -> str:
    return clean(value).casefold()


def demand(condition: bool, message: str) -> None:
    if not condition:
        raise OperationError(message)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def record(state: dict[str, list[dict[str, Any]]], collection: str, record_id: str):
    return next((item for item in state[collection] if item["id"] == record_id), None)


def room_id(state: dict[str, list[dict[str, Any]]], equipment: dict[str, Any]):
    if equipment["tipo_local"] == "sala":
        return equipment["id_local"]
    locker = record(state, "armarios", equipment["id_local"])
    return locker["id_sala"] if locker else None


def local_name(state: dict[str, list[dict[str, Any]]], equipment: dict[str, Any]):
    room = record(state, "salas", room_id(state, equipment) or "")
    room_name = room["nome"] if room else "Sem sala"
    if equipment["tipo_local"] == "armario":
        locker = record(state, "armarios", equipment["id_local"])
        if locker:
            return f"{locker['nome']} · {room_name}"
    return room_name


def active_assignment(state: dict[str, list[dict[str, Any]]], equipment_id: str):
    return next(
        (
            item
            for item in state["atribuicoes"]
            if item["id_equipamento"] == equipment_id and not item.get("fim")
        ),
        None,
    )


def timestamp(value: Any, allow_future: bool = False) -> str:
    text = clean(value)
    demand(text, "Indique uma data válida.")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise OperationError("Indique uma data válida.") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=LISBON_TZ)
    parsed = parsed.astimezone(timezone.utc)
    if not allow_future:
        demand(
            parsed <= datetime.now(timezone.utc),
            "Indique uma data válida que não seja futura.",
        )
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


def audit(
    state: dict[str, list[dict[str, Any]]],
    actor: str | None,
    action: str,
    target: str,
    result: str = "Sucesso",
    before: Any = None,
    after: Any = None,
    reason: str = "",
    protected: bool = False,
) -> None:
    user = next((item for item in state["utilizadores"] if item["id"] == actor), None)
    state["logs"].append(
        {
            "id": new_id("LOG"),
            "data": datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
                "+00:00", "Z"
            ),
            "ator": actor,
            "nome": user["nome"] if user else "Não autenticado",
            "perfil": user["perfil"] if user else "—",
            "acao": action,
            "objeto": clean(target),
            "resultado": result,
            "antes": copy.deepcopy(before),
            "depois": copy.deepcopy(after),
            "motivo": clean(reason),
            "protegido": protected,
        }
    )


def add_event(
    state: dict[str, list[dict[str, Any]]],
    actor: str,
    action: str,
    target: str,
    description: str,
) -> None:
    state["eventos"].append(
        {
            "id": new_id("EV"),
            "data": datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
                "+00:00", "Z"
            ),
            "tipo": action,
            "objeto": target,
            "descricao": clean(description) or action,
            "autor": actor,
        }
    )


def validate_reason(data: dict[str, Any]) -> str:
    reason = clean(data.get("motivo"))
    demand(len(reason) >= 3, "Indique um motivo com pelo menos 3 caracteres.")
    return reason


def apply_operation(
    connection: sqlite3.Connection,
    state: dict[str, list[dict[str, Any]]],
    actor: str,
    kind: str,
    submitted: dict[str, Any],
) -> str:
    data = {
        key: value.strip() if isinstance(value, str) else value
        for key, value in submitted.items()
    }
    user = record(state, "utilizadores", actor)
    demand(
        user is not None and user.get("estado") == "Ativo",
        "A sessão terminou ou a conta está inativa.",
    )
    admin = user["perfil"] == "Administrador"
    required_page = ACTION_PAGES.get(kind)
    demand(required_page is not None, "Operação desconhecida.")
    demand(
        admin if required_page == "admin" else required_page in PERMISSIONS[user["perfil"]],
        "Sem permissão para esta operação.",
    )

    before = None
    after = None
    target = ""
    label = kind

    def operation_time() -> str:
        return timestamp(data.get("data"))

    if kind == "conta":
        email = clean(data.get("email")).lower()
        name = clean(data.get("nome"))
        profile = clean(data.get("perfil"))
        demand(name and EMAIL_RE.fullmatch(email), "Indique nome e email do domínio etpm.pt.")
        demand(profile in ("Professor", "Administrador"), "Perfil inválido.")
        account_id = clean(data.get("id"))
        existing = record(state, "utilizadores", account_id) if account_id else None
        demand(not account_id or existing, "O registo a alterar já não existe.")
        demand(
            not any(
                item["id"] != account_id and normalized(item["email"]) == normalized(email)
                for item in state["utilizadores"]
            ),
            "Este email já existe, mesmo que a conta esteja inativa.",
        )
        before = copy.deepcopy(existing)
        if existing:
            demand(
                normalized(existing["email"]) == normalized(email),
                "O email da conta não pode ser alterado.",
            )
            if (
                existing["perfil"] == "Administrador"
                and profile != "Administrador"
                and existing["estado"] == "Ativo"
            ):
                demand(
                    sum(
                        item["perfil"] == "Administrador" and item["estado"] == "Ativo"
                        for item in state["utilizadores"]
                    )
                    > 1,
                    "É necessário manter um Administrador ativo.",
                )
            existing.update({"nome": name, "perfil": profile})
            account = existing
            label = "Conta alterada"
        else:
            account = {
                "id": new_id("U"),
                "nome": name,
                "email": email,
                "perfil": profile,
                "estado": "Ativo",
            }
            state["utilizadores"].append(account)
            salt, hashed = hash_password("demo1234")
            connection.execute(
                "INSERT INTO credentials (user_id, password_salt, password_hash) "
                "VALUES (?, ?, ?)",
                (account["id"], salt, hashed),
            )
            label = "Conta criada"
        target = account["id"]
        after = copy.deepcopy(account)

    elif kind == "estadoConta":
        reason = validate_reason(data)
        account = record(state, "utilizadores", clean(data.get("id")))
        demand(account is not None, "Conta inexistente.")
        new_status = clean(data.get("estado"))
        demand(
            new_status in ("Ativo", "Inativo") and account["estado"] != new_status,
            "Estado inválido ou já aplicado.",
        )
        if new_status == "Inativo":
            demand(account["id"] != actor, "Não pode desativar a própria conta.")
            if account["perfil"] == "Administrador":
                demand(
                    sum(
                        item["perfil"] == "Administrador" and item["estado"] == "Ativo"
                        for item in state["utilizadores"]
                    )
                    > 1,
                    "É necessário manter um Administrador ativo.",
                )
        before = copy.deepcopy(account)
        account["estado"] = new_status
        after = copy.deepcopy(account)
        target = account["id"]
        label = "Conta desativada" if new_status == "Inativo" else "Conta reativada"

    elif kind in ("sala", "armario"):
        name = clean(data.get("nome"))
        demand(name, "Indique o nome.")
        collection = "salas" if kind == "sala" else "armarios"
        object_id = clean(data.get("id"))
        existing = record(state, collection, object_id) if object_id else None
        demand(not object_id or existing, "O registo a alterar já não existe.")
        demand(
            not any(
                item["id"] != object_id and normalized(item["nome"]) == normalized(name)
                for item in state[collection]
            ),
            "Já existe um registo com este nome.",
        )
        if kind == "armario":
            room = record(state, "salas", clean(data.get("id_sala")))
            demand(room is not None and room["id"] != "REP", "Escolha uma sala válida fora da Sala de Reparação.")
            if existing:
                demand(
                    existing["id_sala"] == room["id"],
                    "Use Transferências para mudar a sala do armário.",
                )
        if existing:
            demand(existing["id"] != "REP", "A Sala de Reparação é uma localização reservada.")
            before = copy.deepcopy(existing)
            existing["nome"] = name
            target = existing["id"]
            after = copy.deepcopy(existing)
            label = ("Sala" if kind == "sala" else "Armário") + " alterado"
        else:
            created = {"id": new_id("S" if kind == "sala" else "ARM"), "nome": name}
            if kind == "armario":
                created["id_sala"] = room["id"]
            state[collection].append(created)
            target = created["id"]
            after = copy.deepcopy(created)
            label = ("Sala" if kind == "sala" else "Armário") + " criado"

    elif kind == "equipamento":
        code = clean(data.get("codigo"))
        name = clean(data.get("nome"))
        serial = clean(data.get("serie"))
        equipment_type = clean(data.get("tipo"))
        demand(
            code and name and serial and equipment_type in ("Portátil", "PC all-in-one", "Outro"),
            "Preencha os dados do equipamento.",
        )
        object_id = clean(data.get("id"))
        existing = record(state, "equipamentos", object_id) if object_id else None
        demand(not object_id or existing, "O registo a alterar já não existe.")
        demand(
            not any(
                item["id"] != object_id
                and (
                    normalized(item["codigo"]) == normalized(code)
                    or normalized(item["serie"]) == normalized(serial)
                )
                for item in state["equipamentos"]
            ),
            "Código ou número de série já existente.",
        )
        if existing:
            before = copy.deepcopy(existing)
            existing.update({"codigo": code, "nome": name, "serie": serial, "tipo": equipment_type})
            equipment = existing
            label = "Equipamento alterado"
        else:
            room = record(state, "salas", clean(data.get("id_sala")))
            demand(
                room is not None and room["id"] != "REP",
                "Escolha uma sala operacional. Para avarias use a operação própria.",
            )
            locker_id = clean(data.get("id_armario"))
            if locker_id:
                locker = record(state, "armarios", locker_id)
                demand(locker is not None and locker["id_sala"] == room["id"], "Armário incompatível com a sala.")
            equipment = {
                "id": new_id("EQ"),
                "codigo": code,
                "nome": name,
                "serie": serial,
                "tipo": equipment_type,
                "estado": "Em funcionamento",
                "tipo_local": "armario" if locker_id else "sala",
                "id_local": locker_id or room["id"],
            }
            state["equipamentos"].append(equipment)
            label = "Equipamento registado"
        target = equipment["id"]
        after = copy.deepcopy(equipment)

    elif kind == "atribuicao":
        equipment = record(state, "equipamentos", clean(data.get("id_equipamento")))
        demand(
            equipment is not None
            and equipment["estado"] == "Em funcionamento"
            and active_assignment(state, equipment["id"]) is None,
            "Equipamento indisponível.",
        )
        recipient_id = clean(data.get("id_destinatario"))
        recipient = record(state, "destinatarios", recipient_id) or record(
            state, "utilizadores", recipient_id
        )
        demand(
            recipient is not None
            and (
                recipient.get("tipo") == "Aluno"
                or recipient.get("estado") == "Ativo"
            ),
            "Destinatário inválido.",
        )
        started = operation_time()
        deadline = clean(data.get("prazo"))
        if deadline:
            deadline = timestamp(deadline, allow_future=True)
            demand(deadline >= started, "Prazo anterior à atribuição ou inválido.")
        assignment = {
            "id": new_id("AT"),
            "id_equipamento": equipment["id"],
            "id_destinatario": recipient["id"],
            "id_utilizador": actor,
            "inicio": started,
            "prazo": deadline,
            "fim": None,
        }
        state["atribuicoes"].append(assignment)
        target = equipment["id"]
        after = copy.deepcopy(assignment)
        label = "Atribuição"

    elif kind == "devolucao":
        assignment = record(state, "atribuicoes", clean(data.get("id_atribuicao")))
        demand(
            assignment is not None and not assignment.get("fim"),
            "Atribuição inexistente ou já devolvida.",
        )
        returned = operation_time()
        demand(returned >= assignment["inicio"], "A devolução não pode ser anterior à atribuição.")
        before = copy.deepcopy(assignment)
        assignment["fim"] = returned
        assignment["id_utilizador_devolucao"] = actor
        after = copy.deepcopy(assignment)
        target = assignment["id_equipamento"]
        label = "Devolução"

    elif kind == "avaria":
        equipment = record(state, "equipamentos", clean(data.get("id_equipamento")))
        demand(equipment is not None, "Equipamento inválido.")
        demand(equipment["estado"] != "Avariado", "A avaria já está registada.")
        demand(
            active_assignment(state, equipment["id"]) is None,
            "Registe primeiro a devolução; avarias durante utilização aguardam regra do docente.",
        )
        demand(record(state, "salas", "REP") is not None, "A Sala de Reparação não está configurada.")
        reason = validate_reason(data)
        occurred = operation_time()
        before = copy.deepcopy(equipment)
        origin = local_name(state, equipment)
        origin_room = room_id(state, equipment)
        equipment.update({"estado": "Avariado", "tipo_local": "sala", "id_local": "REP"})
        after = copy.deepcopy(equipment)
        target = equipment["id"]
        label = "Equipamento avariado"
        state["avarias"].append(
            {
                "id": new_id("AV"),
                "id_equipamento": equipment["id"],
                "descricao": reason,
                "data": occurred,
                "autor": actor,
            }
        )
        if origin_room != "REP":
            movement = {
                "id": new_id("TR"),
                "tipo": "equipamento",
                "id_objeto": equipment["id"],
                "origem": origin,
                "destino": "Sala de Reparação",
                "data": occurred,
                "autor": actor,
            }
            state["transferencias"].append(movement)
            audit(
                state,
                actor,
                "Transferência automática",
                equipment["id"],
                before={"local": origin},
                after={"local": "Sala de Reparação"},
                reason="Avaria",
            )

    elif kind == "transferencia":
        object_type = clean(data.get("tipo_objeto"))
        demand(object_type in ("equipamento", "armario"), "Tipo inválido.")
        is_locker = object_type == "armario"
        demand(not is_locker or admin, "Só o Administrador transfere armários nesta proposta.")
        collection = "armarios" if is_locker else "equipamentos"
        object_id = clean(data.get("id_objeto"))
        obj = record(state, collection, object_id)
        demand(obj is not None, "Objeto inválido.")
        destination = record(state, "salas", clean(data.get("id_sala")))
        demand(destination is not None, "Escolha a sala de destino.")
        demand(destination["id"] != "REP", "Para encaminhar à Sala de Reparação, registe uma avaria.")
        affected = (
            [
                item
                for item in state["equipamentos"]
                if item["tipo_local"] == "armario" and item["id_local"] == obj["id"]
            ]
            if is_locker
            else [obj]
        )
        demand(
            not any(active_assignment(state, item["id"]) for item in affected),
            "Existe equipamento em utilização. Registe primeiro a devolução.",
        )
        locker_id = clean(data.get("id_armario"))
        if locker_id:
            locker = record(state, "armarios", locker_id)
            demand(
                not is_locker and locker is not None and locker["id_sala"] == destination["id"],
                "O armário não pertence à sala escolhida.",
            )
        leaving_repair = not is_locker and room_id(state, obj) == "REP"
        if leaving_repair:
            demand(
                clean(data.get("operacional")) == "sim",
                "Confirme que o equipamento está operacional para sair da Sala de Reparação.",
            )
        else:
            demand(
                not any(item["estado"] == "Avariado" for item in affected),
                "Equipamento avariado deve permanecer na Sala de Reparação.",
            )
        same_location = (
            obj["id_sala"] == destination["id"]
            if is_locker
            else obj["tipo_local"] == ("armario" if locker_id else "sala")
            and obj["id_local"] == (locker_id or destination["id"])
        )
        demand(not same_location, "A origem e o destino são iguais.")
        occurred = operation_time()
        origin = (
            record(state, "salas", obj["id_sala"])["nome"]
            if is_locker
            else local_name(state, obj)
        )
        before = {
            "objeto": copy.deepcopy(obj),
            "equipamentos": copy.deepcopy(affected),
        }
        if is_locker:
            obj["id_sala"] = destination["id"]
        else:
            obj.update(
                {
                    "tipo_local": "armario" if locker_id else "sala",
                    "id_local": locker_id or destination["id"],
                }
            )
            if leaving_repair:
                obj["estado"] = "Em funcionamento"
        movement = {
            "id": new_id("TR"),
            "tipo": object_type,
            "id_objeto": obj["id"],
            "origem": origin,
            "destino": destination["nome"]
            + (f" / {record(state, 'armarios', locker_id)['nome']}" if locker_id else ""),
            "data": occurred,
            "autor": actor,
            "equipamentos": [item["id"] for item in affected],
        }
        state["transferencias"].append(movement)
        after = {"objeto": copy.deepcopy(obj), "movimento": copy.deepcopy(movement)}
        target = obj["id"]
        label = "Saída da Sala de Reparação" if leaving_repair else "Transferência"

    elif kind == "ocultarLog":
        reason = validate_reason(data)
        entry = record(state, "logs", clean(data.get("id")))
        demand(entry is not None, "Log inexistente.")
        demand(
            not entry.get("protegido"),
            "Este log de auditoria é protegido e não pode ser removido.",
        )
        demand(
            not any(
                item["acao"] == "Remoção lógica de log" and item["objeto"] == entry["id"]
                for item in state["logs"]
            ),
            "Este log já foi removido da lista normal.",
        )
        audit(
            state,
            actor,
            "Remoção lógica de log",
            entry["id"],
            before={"log": copy.deepcopy(entry)},
            after={"visibilidade": "Removido da lista normal"},
            reason=reason,
            protected=True,
        )
        return "Log removido da lista normal. O original e a remoção continuam na auditoria."

    else:
        raise OperationError("Operação desconhecida.")

    audit(state, actor, label, target, before=before, after=after, reason=clean(data.get("motivo")))
    add_event(state, actor, label, target, clean(data.get("motivo")) or label)
    return "Operação registada com sucesso. O histórico e os logs foram atualizados."


class SmartCampusHandler(BaseHTTPRequestHandler):
    server_version = "SmartCampusV1Demo/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def send_json(self, status: int, payload: dict[str, Any], headers: dict[str, str] | None = None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, file_path: Path):
        if not file_path.is_file():
            self.send_error(404, "Not found")
            return
        data = file_path.read_bytes()
        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
        }.get(file_path.suffix, "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise OperationError("Pedido inválido.") from exc
        demand(0 < length <= MAX_REQUEST_BYTES, "Pedido vazio ou demasiado grande.")
        try:
            body = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise OperationError("JSON inválido.") from exc
        demand(isinstance(body, dict), "O corpo do pedido deve ser um objeto JSON.")
        return body

    def cookie_value(self, name: str) -> str | None:
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
        except cookies.CookieError:
            return None
        morsel = jar.get(name)
        return morsel.value if morsel else None

    def active_session(self, connection: sqlite3.Connection):
        session_id = self.cookie_value(SESSION_COOKIE)
        if not session_id:
            return None
        row = connection.execute(
            "SELECT user_id, csrf_token, expires_at FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        expiry = datetime.fromisoformat(row["expires_at"])
        if expiry <= datetime.now(timezone.utc):
            connection.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            return None
        user = get_record(connection, "utilizadores", row["user_id"])
        if user is None or user.get("estado") != "Ativo":
            connection.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            return None
        return session_id, row["user_id"], row["csrf_token"], user

    def require_csrf(self, session: tuple[Any, ...]) -> None:
        supplied = self.headers.get("X-CSRFToken", "")
        demand(
            bool(supplied) and secrets.compare_digest(supplied, session[2]),
            "Token CSRF inválido ou expirado.",
        )

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        try:
            with database_connection() as connection:
                session = self.active_session(connection)
                if path == "/" or path == "/index.html":
                    self.send_response(302)
                    self.send_header("Location", "/login.html")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return

                if path == "/api/session":
                    if session is None:
                        self.send_json(401, {"message": "É necessário iniciar sessão."})
                    else:
                        self.send_json(200, {"user": session[3]})
                    return

                if path.startswith("/frontend/static/"):
                    requested = (ROOT / path.lstrip("/")).resolve()
                    if not requested.is_relative_to(ROOT / "frontend" / "static"):
                        self.send_error(403, "Forbidden")
                        return
                    self.send_file(requested)
                    return

                if path in ("/salas.html", "/armarios.html"):
                    section = Path(path).stem
                    self.send_response(302)
                    self.send_header("Location", f"/equipamentos.html?secao={section}")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return

                page = Path(path).stem
                if path.startswith("/") and path.endswith(".html") and page in PAGES:
                    if page != "login" and session is None:
                        self.send_response(302)
                        self.send_header("Location", "/login.html")
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return
                    if page == "login" and session is not None:
                        self.send_response(302)
                        self.send_header("Location", "/dashboard.html")
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return
                    if session is not None and page not in PERMISSIONS[session[3]["perfil"]]:
                        self.send_error(403, "Sem permissão para esta página.")
                        return
                    self.serve_page(connection, page, session)
                    return
                self.send_error(404, "Not found")
        except (sqlite3.Error, OSError) as exc:
            print(f"GET {path} failed: {exc}")
            self.send_error(500, "Não foi possível carregar a página.")

    def serve_page(self, connection: sqlite3.Connection, page: str, session: Any) -> None:
        page_file = ROOT / "frontend" / f"{page}.html"
        html = page_file.read_text(encoding="utf-8")
        if session is None:
            current_user = None
            csrf_token = ""
            state = None
            actor = None
        else:
            _, actor, csrf_token, current_user = session
            state = load_state(connection)
            audit(state, actor, "Consulta de página", page)
            replace_state(connection, state)
            state = load_state(connection)
            if current_user["perfil"] == "Professor":
                assigned_ids = {
                    item["id_destinatario"]
                    for item in state["atribuicoes"]
                    if not item.get("fim")
                }
                state["utilizadores"] = [
                    item
                    for item in state["utilizadores"]
                    if item["id"] == actor or item["id"] in assigned_ids
                ]
                state["destinatarios"] = [
                    item for item in state["destinatarios"] if item["id"] in assigned_ids
                ]
                state["logs"] = []
                state["eventos"] = []
                state["atribuicoes"] = [
                    item for item in state["atribuicoes"] if not item.get("fim")
                ]
                state["avarias"] = []
                state["transferencias"] = []

        config = {
            "mode": "integrado",
            "currentUserId": actor,
            "currentUser": current_user,
            "csrfToken": csrf_token,
            "routes": {name: f"/{name}.html" for name in PAGES},
            "operations": {
                "login": "/api/login",
                "logout": "/api/logout",
                **{kind: f"/api/operations/{kind}" for kind in ACTION_PAGES},
            },
        }
        config_json = (
            json.dumps(config, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
        )
        if state is None:
            server_data = "null"
        else:
            server_data = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
            server_data = server_data.replace("<", "\\u003c").replace(">", "\\u003e")
        scripts = (
            f'<script>window.SMARTCAMPUS_CONFIG={config_json};</script>'
            f'<script type="application/json" id="server-data">{server_data}</script>'
        )
        html = html.replace(
            '<script src="../frontend/static/js/dados-demo.js"></script>',
            scripts,
        )
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        try:
            body = self.read_json()
        except OperationError as exc:
            self.send_json(400, {"message": str(exc)})
            return

        if path == "/api/login":
            self.login(body)
            return
        if path == "/api/logout":
            self.logout(body)
            return
        match = re.fullmatch(r"/api/operations/([A-Za-z]+)", path)
        if match:
            self.operate(match.group(1), body)
            return
        self.send_json(404, {"message": "Rota inexistente."})

    def login(self, body: dict[str, Any]) -> None:
        email = clean(body.get("email")).casefold()
        password = body.get("password")
        if (
            not EMAIL_RE.fullmatch(email)
            or not isinstance(password, str)
            or len(password) > 256
        ):
            self.send_json(401, {"message": "Conta ETPM ativa e credenciais válidas são necessárias."})
            return
        try:
            with database_connection() as connection:
                user_row = connection.execute(
                    "SELECT data_json FROM records "
                    "WHERE collection = 'utilizadores' AND lower(json_extract(data_json, '$.email')) = ?",
                    (email,),
                ).fetchone()
                user = json.loads(user_row["data_json"]) if user_row else None
                credential = None
                if user:
                    credential = connection.execute(
                        "SELECT password_salt, password_hash FROM credentials WHERE user_id = ?",
                        (user["id"],),
                    ).fetchone()
                valid = (
                    user is not None
                    and user.get("estado") == "Ativo"
                    and user.get("perfil") in ("Professor", "Administrador")
                    and credential is not None
                    and verify_password(
                        password,
                        credential["password_salt"],
                        credential["password_hash"],
                    )
                )
                state = load_state(connection)
                audit(
                    state,
                    user["id"] if valid else None,
                    "Login",
                    "Sessão",
                    "Sucesso" if valid else "Recusado",
                    reason="" if valid else "Credenciais inválidas ou conta indisponível",
                    protected=True,
                )
                replace_state(connection, state)
                if not valid:
                    self.send_json(
                        401,
                        {"message": "Conta ETPM ativa e credenciais válidas são necessárias."},
                    )
                    return
                session_id = secrets.token_urlsafe(32)
                csrf_token = secrets.token_urlsafe(32)
                expires = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
                connection.execute(
                    "INSERT INTO sessions (session_id, user_id, csrf_token, expires_at) "
                    "VALUES (?, ?, ?, ?)",
                    (session_id, user["id"], csrf_token, expires.isoformat()),
                )
                self.send_json(
                    200,
                    {"message": "Sessão iniciada."},
                    {
                        "Set-Cookie": (
                            f"{SESSION_COOKIE}={session_id}; Path=/; HttpOnly; "
                            f"SameSite=Lax; Max-Age={SESSION_HOURS * 3600}"
                        )
                    },
                )
        except (sqlite3.Error, ValueError) as exc:
            print(f"Login failed: {exc}")
            self.send_json(500, {"message": "Não foi possível iniciar sessão."})

    def logout(self, body: dict[str, Any]) -> None:
        del body
        try:
            with database_connection() as connection:
                session = self.active_session(connection)
                if session is None:
                    self.send_json(401, {"message": "A sessão terminou."})
                    return
                try:
                    self.require_csrf(session)
                except OperationError as exc:
                    self.send_json(403, {"message": str(exc)})
                    return
                state = load_state(connection)
                audit(state, session[1], "Logout", "Sessão", protected=True)
                replace_state(connection, state)
                connection.execute(
                    "DELETE FROM sessions WHERE session_id = ?", (session[0],)
                )
                self.send_json(
                    200,
                    {"message": "Sessão terminada."},
                    {
                        "Set-Cookie": (
                            f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
                        )
                    },
                )
        except sqlite3.Error as exc:
            print(f"Logout failed: {exc}")
            self.send_json(500, {"message": "Não foi possível terminar a sessão."})

    def operate(self, kind: str, body: dict[str, Any]) -> None:
        try:
            with database_connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                session = self.active_session(connection)
                if session is None:
                    self.send_json(401, {"message": "É necessário iniciar sessão."})
                    return
                try:
                    self.require_csrf(session)
                except OperationError as exc:
                    self.send_json(403, {"message": str(exc)})
                    return
                state = load_state(connection)
                try:
                    message = apply_operation(connection, state, session[1], kind, body)
                    replace_state(connection, state)
                except OperationError as exc:
                    failed_state = load_state(connection)
                    target = (
                        body.get("id")
                        or body.get("id_equipamento")
                        or body.get("id_objeto")
                        or "—"
                    )
                    audit(
                        failed_state,
                        session[1],
                        f"Operação recusada: {kind}",
                        clean(target),
                        result="Recusado",
                        reason=str(exc),
                        protected=True,
                    )
                    replace_state(connection, failed_state)
                    self.send_json(400, {"message": str(exc)})
                    return
                self.send_json(200, {"message": message})
        except sqlite3.IntegrityError as exc:
            print(f"Operation {kind} violates a database constraint: {exc}")
            self.send_json(409, {"message": "A operação viola uma regra de unicidade ou integridade."})
        except sqlite3.Error as exc:
            print(f"Operation {kind} failed: {exc}")
            self.send_json(500, {"message": "Não foi possível guardar a operação."})


def main() -> None:
    initialize()
    server = ThreadingHTTPServer((HOST, PORT), SmartCampusHandler)
    print(f"SmartCampus V1 demo with SQLite: http://{HOST}:{PORT}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor terminado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
