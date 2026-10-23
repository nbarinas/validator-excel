#!/usr/bin/env python3
"""Verifica las 2 plantillas de entrega de muestra del 19 de octubre.

Pedido del usuario (texto de cada plantilla, verbatim):
  * `entrega_sibate_19_oct_sibate_1_204` (codigo de producto 204)
  * `entrega_sibate_19_oct_sibate_2_302` (codigo de producto 302)
Ambas en espanol, disponibles en el envio masivo y en el envio "una por una"
(1x1), con vista previa en el front al lado de las demas.

Las dos plantillas no tienen variables, asi que se comprueba tambien que el
payload a Meta no mande un componente `body` vacio.

Comprueba contra el codigo real:
  1. Las 2 estan en el catalogo (/whatsapp/templates) con name/language/params
     correctos, etiqueta legible y elegibles para 1x1.
  2. El cuerpo del catalogo es byte-exacto respecto del pedido y el render no
     deja ningun {{...}} (no hay variables que sustituir).
  3. El 1x1 las envia como plantilla SIN componente body y guarda el registro.
  4. El masivo las envia igual, tambien sin componente body.
  5. Las plantillas que ya existian siguen mandando su componente body con los
     mismos parametros (no hay regresion en el payload de Meta).
  6. El front (frontend/call_center.js) guarda los mismos cuerpos como respaldo
     de la vista previa.

Uso:    python scripts/tests/check_entrega_sibate_oct19_templates.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

# La base temporal tiene que quedar seteada ANTES de importar la app.
DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_entrega_sibate_oct19.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

from fastapi import HTTPException  # noqa: E402

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

FALLAS = []

KEY_204 = "entrega_sibate_19_oct_sibate_1_204"
KEY_302 = "entrega_sibate_19_oct_sibate_2_302"

# --- Cuerpos esperados (verbatim del pedido) ---
_CUERPO_BASE = (
    "¡Buenos días! ¿Cómo estás?\n"
    "\n"
    "Te escribimos para confirmar si el transportador te entregó el muestra que "
    "comenzarás a utilizar a partir del lunes 26 de octubre. Por favor, recuerda no "
    "utilizarla antes de esa fecha.\n"
    "\n"
    "El código del producto que recibiste es {codigo}.\n"
    "\n"
    "¿Nos puedes confirmar si recibiste la muestra, por favor?\n"
    "\n"
    "¡Muchas gracias por tu colaboración!"
)

NUEVAS = {
    KEY_204: {"body": _CUERPO_BASE.format(codigo="204"), "label": "Entrega Sibate 1 — producto 204"},
    KEY_302: {"body": _CUERPO_BASE.format(codigo="302"), "label": "Entrega Sibate 2 — producto 302"},
}


def check(cond, msg):
    if cond:
        print(f"  OK    {msg}")
    else:
        print(f"  FALLA {msg}")
        FALLAS.append(msg)


def _capturar_envios():
    """Reemplaza el HTTP a Meta y devuelve la lista de payloads enviados."""
    enviados = []

    def _fake(path, payload):
        enviados.append(payload)
        return {"messages": [{"id": f"wamid.CHK{len(enviados)}"}]}

    main._wa_graph_request = _fake
    return enviados


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="chk_entrega",
            hashed_password=auth.get_password_hash("x"),
            role="superuser",
            full_name="Ana Check",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        study = models.Study(code="ENT19", name="Entrega 19 oct", is_active=True)
        db.add(study)
        db.commit()
        db.refresh(study)

        call = models.Call(
            study_id=study.id,
            phone_number="3001230456",
            person_name="Maria",
            collection_time="5:00 pm",
        )
        db.add(call)
        db.commit()
        db.refresh(call)

        main._wa_require_send_window = lambda db, user: None
        main._wa_window_open = lambda db, phone: False
        main.time.sleep = lambda *a, **k: None
        enviados = _capturar_envios()

        print("[1] Las 2 plantillas estan en el catalogo")
        catalogo = {t["key"]: t for t in main.whatsapp_templates_catalog(current_user=admin)}
        for key, esperado in NUEVAS.items():
            cfg = catalogo.get(key)
            check(cfg is not None, f"{key} esta en /whatsapp/templates")
            check(cfg is not None and cfg["name"] == key, f"{key} name = {key}")
            check(cfg is not None and cfg["language"] == "es", f"{key} idioma 'es'")
            check(cfg is not None and cfg["params"] == [], f"{key} sin parametros")
            check(cfg is not None and cfg["single_eligible"] is True, f"{key} es elegible 1x1")
            check(cfg is not None and cfg["label"] == esperado["label"], f"{key} etiqueta legible")
            check(key in main.WHATSAPP_SINGLE_TEMPLATE_KEYS, f"{key} esta en WHATSAPP_SINGLE_TEMPLATE_KEYS")

        print("[2] Cuerpos byte-exactos y render sin variables")
        for key, esperado in NUEVAS.items():
            body = main.WHATSAPP_TEMPLATE_BODIES.get(key)
            check(body == esperado["body"], f"{key} cuerpo byte-exacto ({len(esperado['body'])} chars)")
            check(catalogo.get(key, {}).get("body") == esperado["body"],
                  f"{key} el catalogo expone el mismo cuerpo")
            render = main._wa_render_template_body(key, {})
            check(render == esperado["body"], f"{key} el render no altera el cuerpo")
            check("{{" not in (body or ""), f"{key} no tiene variables")

        print("[3] El 1x1 las envia sin componente body")
        main.set_study_single_templates(
            study.id,
            main.StudySingleTemplatesUpdate(template_keys=list(NUEVAS.keys())),
            db=db,
            current_user=admin,
        )
        single = main.whatsapp_single_templates_for_target(study_id=study.id, db=db, current_user=admin)
        check(single["single_template_keys"] == list(NUEVAS.keys()),
              f"/whatsapp/single-templates devuelve las 2 nuevas -> {single['single_template_keys']}")

        for key in NUEVAS:
            antes = len(enviados)
            try:
                res = main.whatsapp_send_template(
                    main.WhatsAppSendTemplateRequest(call_id=call.id, template_key=key),
                    db=db, current_user=admin,
                )
                check(res.get("wa_status") == "sent", f"{key} se envia en 1x1")
            except HTTPException as e:
                check(False, f"{key} -> HTTP {e.status_code}: {e.detail}")
                continue
            check(len(enviados) == antes + 1, f"{key} hace exactamente 1 request a Meta")
            if len(enviados) != antes + 1:
                continue
            plantilla = enviados[-1]["template"]
            check(plantilla == {"name": key, "language": {"code": "es"}},
                  f"{key} payload sin componentes: {plantilla}")
            check("components" not in plantilla, f"{key} no manda un body vacio")

        print("[4] El masivo tambien las envia sin componente body")
        main.set_study_templates(
            study.id,
            main.StudyTemplatesUpdate(template_keys=list(NUEVAS.keys())),
            db=db,
            current_user=admin,
        )
        for key in NUEVAS:
            antes = len(enviados)
            try:
                res = main.whatsapp_send_bulk(
                    main.WhatsAppSendBulkRequest(
                        template_key=key,
                        category="",
                        contacts=[main.WhatsAppBulkContact(nombre="Maria", telefono="3001230456")],
                        batch_size=20,
                    ),
                    db=db, current_user=admin,
                )
                check(res.get("sent") == 1 and not res.get("failed"),
                      f"{key} se envia en masivo -> sent={res.get('sent')} failed={res.get('failed')}")
            except HTTPException as e:
                check(False, f"masivo {key} -> HTTP {e.status_code}: {e.detail}")
                continue
            check(len(enviados) == antes + 1, f"masivo {key} hace exactamente 1 request a Meta")
            if len(enviados) != antes + 1:
                continue
            plantilla = enviados[-1]["template"]
            check(plantilla == {"name": key, "language": {"code": "es"}},
                  f"masivo {key} payload sin componentes: {plantilla}")

        print("[5] Las plantillas existentes conservan su payload con parametros")
        main.set_study_single_templates(
            study.id,
            main.StudySingleTemplatesUpdate(template_keys=["in_home_beta_385"]),
            db=db,
            current_user=admin,
        )
        antes = len(enviados)
        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(call_id=call.id, template_key="in_home_beta_385"),
                db=db, current_user=admin,
            )
        except HTTPException as e:
            check(False, f"in_home_beta_385 -> HTTP {e.status_code}: {e.detail}")
        if len(enviados) == antes + 1:
            plantilla = enviados[-1]["template"]
            esperado = {
                "name": "in_home_beta_385",
                "language": {"code": "es"},
                "components": [{"type": "body", "parameters": [
                    {"type": "text", "text": "Maria", "parameter_name": "encuestada"},
                    {"type": "text", "text": "Ana Check", "parameter_name": "encuestador"},
                    {"type": "text", "text": "5:00 pm", "parameter_name": "hora_asignada"},
                ]}],
            }
            check(plantilla == esperado, f"in_home_beta_385 (1x1) payload identico al previo: {plantilla}")

        antes = len(enviados)
        try:
            main.whatsapp_send_bulk(
                main.WhatsAppSendBulkRequest(
                    template_key="producto_310_90_dias",
                    category="",
                    contacts=[main.WhatsAppBulkContact(nombre="Maria", telefono="3001230456")],
                    batch_size=20,
                ),
                db=db, current_user=admin,
            )
        except HTTPException as e:
            check(False, f"masivo producto_310_90_dias -> HTTP {e.status_code}: {e.detail}")
        if len(enviados) == antes + 1:
            plantilla = enviados[-1]["template"]
            esperado = {
                "name": "producto_310_90_dias",
                "language": {"code": "es"},
                "components": [{"type": "body", "parameters": [
                    {"type": "text", "text": "Maria", "parameter_name": "encuestada"},
                ]}],
            }
            check(plantilla == esperado,
                  f"producto_310_90_dias (masivo) payload identico al previo: {plantilla}")

        print("[6] El front guarda los mismos cuerpos para la vista previa")
        js = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
        for key, esperado in NUEVAS.items():
            literal = '"%s": "%s",' % (key, esperado["body"].replace("\n", "\\n"))
            check(literal in js, f"WA_TEMPLATE_BODIES tiene el cuerpo de {key} (byte-exacto)")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} fallas.")
        sys.exit(1)
    print("\nTodo OK.")
