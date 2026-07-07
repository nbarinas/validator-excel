"""
Replicación asíncrona de cambios hacia un espejo MySQL/Postgres.

Cómo funciona:
- En cada commit de la sesión primaria se capturan INSERT/UPDATE/DELETE.
- Se intenta replicar en el espejo en un hilo aparte para no bloquear la API.
- Si el espejo falla, la operación se guarda en una cola SQLite local y se
  reintenta periódicamente o mediante sync_to_mirror.py.
"""

import json
import threading
import traceback
from datetime import datetime
from typing import Any

from sqlalchemy import event, text, Table
from sqlalchemy.orm import Session
from sqlalchemy import inspect as sa_inspect

from .database import (
    mirror_engine,
    Base,
    DB_PATH,
    get_active_db_label,
    is_mirror_configured,
)

# ---------------------------------------------------------------------------
# Cola local de reintentos (siempre en SQLite)
# ---------------------------------------------------------------------------
_QUEUE_URL = f"sqlite:///{DB_PATH}"
_queue_engine = None


def _get_queue_engine():
    global _queue_engine
    if _queue_engine is None:
        _queue_engine = __import__("sqlalchemy", fromlist=["create_engine"]).create_engine(
            _QUEUE_URL,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
        _ensure_queue_table()
    return _queue_engine


def _ensure_queue_table():
    with _get_queue_engine().connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS replication_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                operation TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                attempts INTEGER DEFAULT 0,
                error TEXT
            )
        """))
        conn.commit()


# ---------------------------------------------------------------------------
# Captura de cambios en cada commit
# ---------------------------------------------------------------------------
@event.listens_for(Session, "before_commit")
def _capture_changes(session: Session):
    """Guarda en session.info los cambios que deben replicarse."""
    if not is_mirror_configured():
        return
    if getattr(session, "_replication_skip", False):
        return

    inserts = []
    updates = []
    deletes = []

    for obj in session.new:
        state = sa_inspect(obj)
        data = {col.key: _serialize(getattr(obj, col.key)) for col in state.mapper.column_attrs}
        inserts.append({"table": obj.__tablename__, "data": data})

    for obj in session.dirty:
        if not session.is_modified(obj, include_collections=False):
            continue
        state = sa_inspect(obj)
        data = {col.key: _serialize(getattr(obj, col.key)) for col in state.mapper.column_attrs}
        updates.append({"table": obj.__tablename__, "data": data})

    for obj in session.deleted:
        state = sa_inspect(obj)
        pk = {col.name: _serialize(getattr(obj, col.name)) for col in state.mapper.primary_key}
        deletes.append({"table": obj.__tablename__, "pk": pk})

    session.info["_replication"] = {
        "inserts": inserts,
        "updates": updates,
        "deletes": deletes,
    }


@event.listens_for(Session, "after_commit")
def _replicate_after_commit(session: Session):
    """Dispara la replicación asíncrona después del commit exitoso."""
    if not is_mirror_configured():
        return

    payload = session.info.pop("_replication", None)
    if not payload:
        return

    # Evita reproducir cambios que vengan del propio espejo o de la cola
    if getattr(session, "_replication_skip", False):
        return

    # Lanza replicación en hilo para no bloquear la respuesta HTTP
    threading.Thread(
        target=_apply_to_mirror,
        args=(payload,),
        daemon=True,
    ).start()


@event.listens_for(Session, "after_rollback")
def _clear_on_rollback(session: Session):
    session.info.pop("_replication", None)


# ---------------------------------------------------------------------------
# Serialización / aplicación de cambios
# ---------------------------------------------------------------------------
def _serialize(value: Any) -> Any:
    """Convierte fechas y otros tipos a algo JSON-serializable."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _table_by_name(name: str) -> Table:
    return Base.metadata.tables[name]


def _apply_to_mirror(payload: dict):
    """Aplica un lote de cambios en el espejo. Si falla, encola."""
    if not is_mirror_configured():
        return

    try:
        with mirror_engine.connect() as conn:
            with conn.begin():
                for item in payload["inserts"]:
                    table = _table_by_name(item["table"])
                    conn.execute(table.insert(), item["data"])

                for item in payload["updates"]:
                    table = _table_by_name(item["table"])
                    pk_cols = [c.name for c in table.primary_key.columns]
                    where = []
                    for pk in pk_cols:
                        where.append(getattr(table.c, pk) == item["data"].get(pk))
                    stmt = table.update().where(*where).values(item["data"])
                    conn.execute(stmt)

                for item in payload["deletes"]:
                    table = _table_by_name(item["table"])
                    where = []
                    for pk_name, pk_val in item["pk"].items():
                        where.append(getattr(table.c, pk_name) == pk_val)
                    stmt = table.delete().where(*where)
                    conn.execute(stmt)

        print(f"INFO: Replicación exitosa: {len(payload['inserts'])} inserts, "
              f"{len(payload['updates'])} updates, {len(payload['deletes'])} deletes.")
    except Exception as e:
        print(f"WARN: Replicación al espejo falló: {e}")
        _enqueue_payload(payload, str(e))


def _enqueue_payload(payload: dict, error: str):
    """Guarda el lote fallido en la cola SQLite."""
    try:
        _ensure_queue_table()
        with _get_queue_engine().connect() as conn:
            with conn.begin():
                for item in payload["inserts"]:
                    conn.execute(text("""
                        INSERT INTO replication_queue (table_name, operation, payload, error)
                        VALUES (:table_name, 'INSERT', :payload, :error)
                    """), {
                        "table_name": item["table"],
                        "payload": json.dumps({"data": item["data"]}, default=str),
                        "error": error,
                    })
                for item in payload["updates"]:
                    conn.execute(text("""
                        INSERT INTO replication_queue (table_name, operation, payload, error)
                        VALUES (:table_name, 'UPDATE', :payload, :error)
                    """), {
                        "table_name": item["table"],
                        "payload": json.dumps({"data": item["data"]}, default=str),
                        "error": error,
                    })
                for item in payload["deletes"]:
                    conn.execute(text("""
                        INSERT INTO replication_queue (table_name, operation, payload, error)
                        VALUES (:table_name, 'DELETE', :payload, :error)
                    """), {
                        "table_name": item["table"],
                        "payload": json.dumps({"pk": item["pk"]}, default=str),
                        "error": error,
                    })
        print("INFO: Cambios encolados para replicación posterior.")
    except Exception as e2:
        print(f"CRITICAL: No se pudo encolar la replicación: {e2}")


# ---------------------------------------------------------------------------
# Reintentos y sincronización
# ---------------------------------------------------------------------------
def retry_failed_replications(limit: int = 100) -> dict:
    """Reintenta los cambios pendientes en la cola local."""
    if not is_mirror_configured():
        return {"status": "mirror_not_configured", "processed": 0, "failed": 0}

    _ensure_queue_table()
    processed = 0
    failed = 0
    errors = []

    try:
        with _get_queue_engine().connect() as qconn:
            rows = qconn.execute(text(
                "SELECT id, table_name, operation, payload FROM replication_queue ORDER BY id LIMIT :limit"
            ), {"limit": limit}).fetchall()

        with mirror_engine.connect() as conn:
            with conn.begin():
                for row in rows:
                    try:
                        payload = json.loads(row.payload)
                        table = _table_by_name(row.table_name)

                        if row.operation == "INSERT":
                            conn.execute(table.insert(), payload["data"])
                        elif row.operation == "UPDATE":
                            pk_cols = [c.name for c in table.primary_key.columns]
                            where = [getattr(table.c, pk) == payload["data"].get(pk) for pk in pk_cols]
                            conn.execute(table.update().where(*where).values(payload["data"]))
                        elif row.operation == "DELETE":
                            where = [getattr(table.c, pk) == val for pk, val in payload["pk"].items()]
                            conn.execute(table.delete().where(*where))

                        _remove_from_queue(row.id)
                        processed += 1
                    except Exception as e:
                        failed += 1
                        errors.append(str(e))
                        _mark_queue_attempt(row.id, str(e))

        return {"status": "ok", "processed": processed, "failed": failed, "errors": errors[:5]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _remove_from_queue(qid: int):
    with _get_queue_engine().connect() as conn:
        with conn.begin():
            conn.execute(text("DELETE FROM replication_queue WHERE id = :id"), {"id": qid})


def _mark_queue_attempt(qid: int, error: str):
    with _get_queue_engine().connect() as conn:
        with conn.begin():
            conn.execute(text("""
                UPDATE replication_queue
                SET attempts = attempts + 1, error = :error
                WHERE id = :id
            """), {"id": qid, "error": error})


def get_replication_status() -> dict:
    """Devuelve el estado de la cola de replicación."""
    try:
        _ensure_queue_table()
        with _get_queue_engine().connect() as conn:
            pending = conn.execute(text(
                "SELECT COUNT(*) FROM replication_queue"
            )).scalar()
            oldest = conn.execute(text(
                "SELECT MIN(created_at) FROM replication_queue"
            )).scalar()
        return {
            "mirror_configured": is_mirror_configured(),
            "active_db": get_active_db_label(),
            "pending_items": pending,
            "oldest_pending": str(oldest) if oldest else None,
        }
    except Exception as e:
        return {"mirror_configured": is_mirror_configured(), "error": str(e)}
