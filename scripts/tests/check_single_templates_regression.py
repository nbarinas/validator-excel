#!/usr/bin/env python3
"""Regresion de las plantillas 1x1: no romper el envio por registro que ya existia.

Los checks del verificador independiente (B1/B2) quedan versionados aca:

  R1/R2. `bono_final` y `bono_parcial` siguen enviandose en llamadas con estudio
         (no estan en el catalogo 1x1, asi que la validacion por estudio no aplica).
  R3.    Una plantilla del catalogo 1x1 no conectada al estudio sigue dando 403.
  R4.    `POST /whatsapp/send-bulk` acepta `in_home_beta_385` y sigue rechazando
         una key que no esta en el catalogo (p. ej. 'filter', el default viejo roto).
  R5.    En un estudio sin ninguna 1x1 conectada, una plantilla fuera del catalogo
         (bono_final) sigue enviandose.
  R6.    Una 1x1 no conectada tambien se bloquea cuando el estudio viene explicito
         (`phone_number` + `study_id`, el camino del modal "Nuevo chat").

Uso:    python scripts/tests/check_single_templates_regression.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_single_templates_regression.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

from fastapi import HTTPException  # noqa: E402

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

FALLAS = []


def check(cond, msg):
    if cond:
        print(f"  OK    {msg}")
    else:
        print(f"  FALLA {msg}")
        FALLAS.append(msg)


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="reg_admin",
            hashed_password=auth.get_password_hash("x"),
            role="superuser",
            full_name="Reg Check",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        study = models.Study(code="REG1", name="Reg 1x1", is_active=True)
        db.add(study)
        db.commit()
        db.refresh(study)

        main._wa_require_send_window = lambda db, user: None
        main._wa_window_open = lambda db, phone: False
        main._wa_graph_request = lambda path, payload: {"messages": [{"id": "wamid.REG"}]}

        # El estudio solo tiene conectada in_home_beta_385 como 1x1.
        main.set_study_single_templates(
            study.id,
            main.StudySingleTemplatesUpdate(template_keys=["in_home_beta_385"]),
            db=db,
            current_user=admin,
        )

        call = models.Call(study_id=study.id, phone_number="3001230001", person_name="Ana",
                           collection_time="5:00 pm")
        db.add(call)
        db.commit()
        db.refresh(call)

        print("[R1] bono_final en llamada con estudio")
        try:
            res = main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(call_id=call.id, template_key="bono_final"),
                db=db, current_user=admin,
            )
            check(res.get("wa_status") == "sent", "bono_final sigue enviando (no esta en el catalogo 1x1)")
        except HTTPException as e:
            check(False, f"bono_final -> HTTP {e.status_code}: {e.detail}")

        print("[R2] bono_parcial en llamada con estudio")
        try:
            res = main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(
                    call_id=call.id, template_key="bono_parcial",
                    dia_y_hora="lunes 5:00 pm", monto="50000",
                ),
                db=db, current_user=admin,
            )
            check(res.get("wa_status") == "sent", "bono_parcial sigue enviando")
        except HTTPException as e:
            check(False, f"bono_parcial -> HTTP {e.status_code}: {e.detail}")

        print("[R3] plantilla 1x1 no conectada")
        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(call_id=call.id, template_key="shampo_segundo"),
                db=db, current_user=admin,
            )
            check(False, "shampo_segundo no conectada deberia ser 403")
        except HTTPException as e:
            check(e.status_code == 403, "shampo_segundo (1x1) no conectada -> 403")

        print("[R4] envio masivo")
        try:
            main.whatsapp_send_bulk(
                main.WhatsAppSendBulkRequest(template_key="in_home_beta_385", category="",
                                            contacts=[], batch_size=20),
                db=db, current_user=admin,
            )
            check(True, "send-bulk acepta in_home_beta_385")
        except HTTPException as e:
            check(False, f"send-bulk in_home_beta_385 -> {e.status_code}: {e.detail}")

        try:
            main.whatsapp_send_bulk(
                main.WhatsAppSendBulkRequest(template_key="filter", category="x",
                                            contacts=[], batch_size=20),
                db=db, current_user=admin,
            )
            check(False, "send-bulk 'filter' deberia ser 400")
        except HTTPException as e:
            check(e.status_code == 400, "send-bulk rechaza 'filter' -> 400")

        print("[R5] estudio sin 1x1: bono_final sigue enviando")
        study_empty = models.Study(code="REG2", name="Reg sin 1x1", is_active=True)
        db.add(study_empty)
        db.commit()
        db.refresh(study_empty)
        call_empty = models.Call(study_id=study_empty.id, phone_number="3001230002", person_name="Beto")
        db.add(call_empty)
        db.commit()
        db.refresh(call_empty)
        try:
            res = main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(call_id=call_empty.id, template_key="bono_final"),
                db=db, current_user=admin,
            )
            check(res.get("wa_status") == "sent", "estudio sin 1x1 no bloquea una plantilla fuera del catalogo")
        except HTTPException as e:
            check(False, f"bono_final en estudio sin 1x1 -> HTTP {e.status_code}: {e.detail}")

        print("[R6] 1x1 no conectada por phone_number + study_id")
        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(
                    phone_number="3001230001", study_id=study.id, template_key="shampo_primer",
                ),
                db=db, current_user=admin,
            )
            check(False, "shampo_primer con study_id explicito deberia ser 403")
        except HTTPException as e:
            check(e.status_code == 403, "1x1 no conectada con study_id explicito -> 403")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} falla(s).")
        sys.exit(1)
    print("\nTodo OK.")
