#!/usr/bin/env python3
"""Verifica la plantilla `fatiga_729_r3` y el retiro de `r2_729`.

Pedido del usuario (verbatim):
  * Agregar `fatiga_729_r3` (es) para la vista previa y el llenado.
  * Eliminar/dejar de usar `r2_729` ("Shampoo 729 — segunda videollamada (R2)").

Comprueba contra el codigo real:
  1. El catalogo expone `fatiga_729_r3` con name, idioma, parametros, etiqueta y
     elegibilidad 1x1.
  2. El cuerpo es byte-exacto y el render sustituye las 3 variables.
  3. El respaldo de vista previa del front es byte-identico al del backend.
  4. `r2_729` salio de MAP/LABELS/BODIES/SINGLE_KEYS, del front y del render.
  5. Conectada al 1x1 del estudio, el envio manda los 3 parametros a Meta.
  6. `r2_729` se rechaza con 400 "Plantilla no valida" en 1x1 y en masivo,
     sin llamar a Meta.

Uso:    python scripts/tests/check_fatiga_729_r3.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

# La base temporal tiene que quedar seteada ANTES de importar la app.
DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_fatiga_729_r3.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

from fastapi import HTTPException  # noqa: E402

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

FALLAS = []

KEY = "fatiga_729_r3"
RETIRADA = "r2_729"
BODY = """¡Muy buenos días, señora {{nombre_entrevistada}}! 😊

La saluda {{encuestador}}, de AZ Marketing Plus.

Le escribo para recordarle que hoy tiene programada la tercera videollamada del estudio de shampoo 729, a las {{hora_agendada}}.

Al finalizar la videollamada, le explicaremos cómo recibirá su primer bono de $20.000 por su participación en el estudio.

¿Podemos realizar la videollamada en este momento o prefiere que la contactemos más tarde?

¡Muchas gracias por su compromiso! Le deseo un feliz día. 🌷"""


def check(cond, msg):
    if cond:
        print(f"  OK    {msg}")
    else:
        print(f"  FALLA {msg}")
        FALLAS.append(msg)


def front_body(key):
    """Extrae y decodifica el cuerpo de WA_TEMPLATE_BODIES en el front."""
    src = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
    bloque = src.split("const WA_TEMPLATE_BODIES = {", 1)[1].split("\n};", 1)[0]
    match = re.search(r'"%s":\s*"((?:[^"\\]|\\.)*)"' % re.escape(key), bloque)
    if not match:
        return None
    return json.loads('"' + match.group(1) + '"')


def rechazo(func, nombre):
    try:
        func()
        check(False, f"{nombre} con {RETIRADA} deberia dar 400")
    except HTTPException as exc:
        check(exc.status_code == 400 and exc.detail == "Plantilla no válida",
              f"{nombre} con {RETIRADA} -> 400 Plantilla no válida")


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="chk_fatiga_admin",
            hashed_password=auth.get_password_hash("x"),
            role="superuser",
            full_name="Admin Check",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("[1] Catalogo")
        catalogo = {t["key"]: t for t in main.whatsapp_templates_catalog(current_user=admin)}
        cfg = catalogo.get(KEY)
        check(cfg is not None, f"{KEY} esta en el catalogo")
        check(cfg and cfg["name"] == KEY, f"{KEY} name = {KEY}")
        check(cfg and cfg["language"] == "es", f"{KEY} idioma 'es'")
        check(cfg and cfg["params"] == ["nombre_entrevistada", "encuestador", "hora_agendada"],
              f"{KEY} parametros = nombre_entrevistada, encuestador, hora_agendada")
        check(cfg and cfg["label"] == "Shampoo 729 — tercera videollamada (R3)",
              f"{KEY} etiqueta legible")
        check(cfg and cfg["body"] == BODY, f"{KEY} cuerpo byte-exacto")
        check(cfg and cfg["single_eligible"] is True, f"{KEY} es elegible 1x1")

        print("[2] Render de las 3 variables")
        body = main._wa_render_template_body(
            KEY,
            {"nombre_entrevistada": "Ana", "encuestador": "Luis", "hora_agendada": "3:30 pm"},
        )
        check(body is not None and "Ana" in body and "Luis" in body and "3:30 pm" in body,
              "sustituye nombre_entrevistada / encuestador / hora_agendada")
        check(body is not None and "{{" not in body, f"{KEY} no deja variables sin sustituir")

        print("[3] Respaldo de vista previa del front")
        check(front_body(KEY) == BODY, f"{KEY} cuerpo del front byte-identico al backend")

        print("[4] Retiro de r2_729")
        check(RETIRADA not in main.WHATSAPP_TEMPLATE_MAP, f"{RETIRADA} fuera de WHATSAPP_TEMPLATE_MAP")
        check(RETIRADA not in main.WHATSAPP_TEMPLATE_LABELS, f"{RETIRADA} fuera de WHATSAPP_TEMPLATE_LABELS")
        check(RETIRADA not in main.WHATSAPP_TEMPLATE_BODIES, f"{RETIRADA} fuera de WHATSAPP_TEMPLATE_BODIES")
        check(RETIRADA not in main.WHATSAPP_SINGLE_TEMPLATE_KEYS,
              f"{RETIRADA} fuera de WHATSAPP_SINGLE_TEMPLATE_KEYS")
        check(RETIRADA not in catalogo, f"{RETIRADA} ya no aparece en el catalogo")
        check(main._wa_render_template_body(RETIRADA, {}) is None,
              f"{RETIRADA} ya no se puede renderizar")
        check(front_body(RETIRADA) is None, f"{RETIRADA} fuera del respaldo del front")

        print("[5] Conexion 1x1 y llenado en el envio")
        estudio = models.Study(code="FAT1", name="Fatiga 729", is_active=True)
        db.add(estudio)
        db.commit()
        db.refresh(estudio)
        main.set_study_single_templates(
            estudio.id,
            main.StudySingleTemplatesUpdate(template_keys=[KEY]),
            db=db,
            current_user=admin,
        )
        keys = main.get_study_single_templates(estudio.id, db=db, current_user=admin)["single_template_keys"]
        check(keys == [KEY], f"{KEY} se conecta al 1x1 del estudio -> {keys}")

        llamada = models.Call(
            study_id=estudio.id,
            phone_number="3001234567",
            person_name="Ana Gomez",
            collection_time="3:30 pm",
        )
        db.add(llamada)
        db.commit()
        db.refresh(llamada)

        main._wa_require_send_window = lambda db, user: None
        main._wa_window_open = lambda db, phone: False
        enviados = []

        def fake_graph(path, payload):
            enviados.append(payload)
            return {"messages": [{"id": "wamid.TEST"}]}

        main._wa_graph_request = fake_graph
        res = main.whatsapp_send_template(
            main.WhatsAppSendTemplateRequest(call_id=llamada.id, template_key=KEY),
            db=db,
            current_user=admin,
        )
        check(res.get("wa_status") == "sent" and res.get("template_key") == KEY,
              f"{KEY} conectada se envia (envio simulado)")
        componentes = (enviados[0].get("template") or {}).get("components") or []
        parametros = (componentes[0].get("parameters") if componentes else []) or []
        check([p.get("parameter_name") for p in parametros] ==
              ["nombre_entrevistada", "encuestador", "hora_agendada"],
              f"payload con los 3 parametros -> {[p.get('parameter_name') for p in parametros]}")
        check([p.get("text") for p in parametros] == ["Ana Gomez", "Admin Check", "3:30 pm"],
              f"payload con los valores llenados -> {[p.get('text') for p in parametros]}")

        print("[6] r2_729 rechazada en 1x1 y en masivo")
        antes = len(enviados)
        rechazo(
            lambda: main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(call_id=llamada.id, template_key=RETIRADA),
                db=db,
                current_user=admin,
            ),
            "send-template",
        )
        rechazo(
            lambda: main.whatsapp_send_bulk(
                main.WhatsAppSendBulkRequest(template_key=RETIRADA, contacts=[]),
                db=db,
                current_user=admin,
            ),
            "send-bulk",
        )
        check(len(enviados) == antes, "ningun rechazo llamo a Meta")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} falla(s).")
        sys.exit(1)
    print("\nTodo OK.")
