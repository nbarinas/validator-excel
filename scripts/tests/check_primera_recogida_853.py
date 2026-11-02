#!/usr/bin/env python3
"""Verifica la plantilla `primera_recogida_853_` (1x1 y envio masivo).

Pedido del usuario (verbatim):
  "solo necesitare agregar esa plantilla no hacer lo otro y commit"
  (plantilla `primera_recogida_853_`, Spanish, 1x1 y masivo)

Comprueba contra el codigo real:
  1. El catalogo expone `primera_recogida_853_` con name, idioma, parametros,
     etiqueta y elegibilidad 1x1.
  2. El cuerpo es byte-exacto y el render sustituye las 3 variables.
  3. El respaldo de vista previa del front es byte-identico al del backend.
  4. Conectada al 1x1 del estudio, el envio manda los 3 parametros a Meta con
     nombre de la persona, encuestador y hora de recogida.
  5. El envio masivo la acepta y manda los 3 parametros (la hora va "hoy",
     comportamiento pre-existente del masivo por lista).
  6. Regresion: `final_beta` y `fatiga_729_r3` (misma familia de 3 variables)
     siguen igual.

Uso:    python scripts/tests/check_primera_recogida_853.py
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
DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_primera_recogida_853.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

FALLAS = []

KEY = "primera_recogida_853_"
VECINAS = {
    "final_beta": {
        "params": ["nombre_entrevistada", "nombre_encuestador", "hora_agendada"],
    },
    "fatiga_729_r3": {
        "params": ["nombre_entrevistada", "encuestador", "hora_agendada"],
    },
}
PARAMS = ["nombre_entrevistada", "nombre_encuestador", "hora_agendada"]
LABEL = "Shampoo 853 — primera recogida"
BODY = """¡Hola, señora {{nombre_entrevistada}}! ¿Cómo está? 😊

Mucho gusto, mi nombre es {{nombre_encuestador}}, del equipo de AZ Marketing Plus.

Le escribo porque hace 10 días le dejamos el shampoo 853 y para el día de hoy tiene programada una videollamada.

El objetivo es realizar un seguimiento al uso del shampoo, conocer cómo le ha ido con el producto y registrar su experiencia durante estos días.

¿Me confirma si todavía tiene disponibilidad para realizarla a las {{hora_agendada}} o si prefiere que la hagamos en este momento?

Quedo atento a su respuesta. ¡Muchas gracias y feliz día!"""


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


def parametros_enviados(payload):
    componentes = (payload.get("template") or {}).get("components") or []
    parametros = (componentes[0].get("parameters") if componentes else []) or []
    return [(p.get("parameter_name"), p.get("text")) for p in parametros]


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="chk_primera_853_admin",
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
        check(cfg and cfg["params"] == PARAMS,
              f"{KEY} parametros = {', '.join(PARAMS)}")
        check(cfg and cfg["label"] == LABEL, f"{KEY} etiqueta legible = {LABEL}")
        check(cfg and cfg["body"] == BODY, f"{KEY} cuerpo byte-exacto")
        check(cfg and cfg["single_eligible"] is True, f"{KEY} es elegible 1x1")
        check(KEY in main.WHATSAPP_TEMPLATE_MAP, f"{KEY} esta en WHATSAPP_TEMPLATE_MAP (masivo)")
        check(KEY in main.WHATSAPP_SINGLE_TEMPLATE_KEYS,
              f"{KEY} esta en WHATSAPP_SINGLE_TEMPLATE_KEYS (1x1)")

        print("[2] Render de las 3 variables")
        body = main._wa_render_template_body(
            KEY,
            {"nombre_entrevistada": "Ana", "nombre_encuestador": "Luis", "hora_agendada": "3:30 pm"},
        )
        check(body is not None and "Ana" in body and "Luis" in body and "3:30 pm" in body,
              "sustituye nombre_entrevistada / nombre_encuestador / hora_agendada")
        check(body is not None and "{{" not in body, f"{KEY} no deja variables sin sustituir")

        print("[3] Respaldo de vista previa del front")
        check(front_body(KEY) == BODY, f"{KEY} cuerpo del front byte-identico al backend")

        print("[4] Conexion 1x1 y llenado en el envio")
        estudio = models.Study(code="P853", name="Primera recogida 853", is_active=True)
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
        try:
            res = main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(call_id=llamada.id, template_key=KEY),
                db=db,
                current_user=admin,
            )
            check(res.get("wa_status") == "sent" and res.get("template_key") == KEY,
                  f"{KEY} conectada se envia por 1x1 (envio simulado)")
            check(parametros_enviados(enviados[0]) ==
                  [("nombre_entrevistada", "Ana Gomez"), ("nombre_encuestador", "Admin Check"),
                   ("hora_agendada", "3:30 pm")],
                  f"payload 1x1 con los 3 parametros llenados -> {parametros_enviados(enviados[0])}")
        except Exception as exc:
            check(False, f"{KEY} conectada se envia por 1x1 -> {exc!r}")

        print("[5] Envio masivo")
        antes = len(enviados)
        try:
            res_bulk = main.whatsapp_send_bulk(
                main.WhatsAppSendBulkRequest(
                    template_key=KEY,
                    contacts=[main.WhatsAppBulkContact(nombre="Ana Gomez", telefono="3001234567")],
                ),
                db=db,
                current_user=admin,
            )
            check(res_bulk.get("sent") == 1 and res_bulk.get("failed") == [],
                  f"{KEY} se envia por masivo (simulado) -> {res_bulk.get('sent')} enviado(s)")
            check(len(enviados) == antes + 1, "el masivo llamo a Meta una sola vez")
            check(parametros_enviados(enviados[-1]) ==
                  [("nombre_entrevistada", "Ana Gomez"), ("nombre_encuestador", "Admin Check"),
                   ("hora_agendada", "hoy")],
                  f"payload masivo con los 3 parametros -> {parametros_enviados(enviados[-1])}")
        except Exception as exc:
            check(False, f"{KEY} se envia por masivo -> {exc!r}")

        print("[6] Regresion de las vecinas con las mismas 3 variables")
        for vecina, esperado in VECINAS.items():
            cfg_v = catalogo.get(vecina)
            check(cfg_v is not None and cfg_v["params"] == esperado["params"],
                  f"{vecina} conserva sus parametros")
            check(cfg_v is not None and cfg_v["body"] == main.WHATSAPP_TEMPLATE_BODIES[vecina],
                  f"{vecina} conserva su cuerpo")
            check(vecina in main.WHATSAPP_SINGLE_TEMPLATE_KEYS,
                  f"{vecina} sigue elegible 1x1")
            check(front_body(vecina) == main.WHATSAPP_TEMPLATE_BODIES[vecina],
                  f"{vecina} sigue byte-identica en el front")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} falla(s).")
        sys.exit(1)
    print("\nTodo OK.")
