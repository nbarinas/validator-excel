#!/usr/bin/env python3
"""Verifica la plantilla `729_sin_bono` en el catalogo, en 1x1 y en el masivo.

Pedido del usuario (verbatim):

    quiero agregar una plantilla en 1x1 y masivo se llama 729_sin_bono · Spanish
    y dice ¡Muy buenos días, señora {{nombre_entrevistada}}! 😊

    La saluda {{encuestador}}, de AZ Marketing Plus.

    Le escribo para recordarle que hoy tiene programada la cuarta videollamada del
    estudio de shampoo 729, a las {{hora_agendada}}.

    ¿Podemos realizar la videollamada en este momento a mas tarde

Decision del usuario: el body cierra en esa pregunta (sin punto final y sin la
linea suelta "."); "2:00 pm", "Si, llámeme de una vez" y "Mas tarde, porfa" son
botones de respuesta rapida de la plantilla en Meta y no forman parte del body.

Comprueba contra el codigo real:
  1. WHATSAPP_TEMPLATE_MAP/LABELS/BODIES: name, idioma `es`, parametros y cuerpo
     byte-exacto.
  2. El catalogo la publica en 1x1 (single_eligible) y en el catalogo del masivo.
  3. El render del texto libre sustituye las 3 variables.
  4. frontend/call_center.js guarda el mismo literal (vista previa).
  5. Regresion: las plantillas hermanas que comparten codigo (fatiga_729_r3,
     primera_recogida_853_ y sibate_encuesta_final) conservan configuracion y
     cuerpo byte-exacto, y la lista 1x1 conserva el orden previo y suma la key nueva.
  6. Conectada al 1x1 del estudio, el envio manda los 3 parametros a Meta; una
     key no conectada sigue rechazandose con 403 sin llamar a Meta.

Uso:    python scripts/tests/check_729_sin_bono.py
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
DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_729_sin_bono.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

from fastapi import HTTPException  # noqa: E402

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

KEY = "729_sin_bono"
LABEL = "Shampoo 729 — cuarta videollamada (sin bono)"
PARAMS = ["nombre_entrevistada", "encuestador", "hora_agendada"]

# --- Cuerpo aprobado (verbatim del pedido) ---
CUERPO = (
    "¡Muy buenos días, señora {{nombre_entrevistada}}! 😊\n"
    "\n"
    "La saluda {{encuestador}}, de AZ Marketing Plus.\n"
    "\n"
    "Le escribo para recordarle que hoy tiene programada la cuarta videollamada del "
    "estudio de shampoo 729, a las {{hora_agendada}}.\n"
    "\n"
    "¿Podemos realizar la videollamada en este momento a mas tarde"
)

# --- Baseline de las plantillas hermanas (no deben cambiar) ---
HERMANAS = {
    "fatiga_729_r3": (
        "¡Muy buenos días, señora {{nombre_entrevistada}}! 😊\n\nLa saluda {{encuestador}}, "
        "de AZ Marketing Plus.\n\nLe escribo para recordarle que hoy tiene programada la "
        "tercera videollamada del estudio de shampoo 729, a las {{hora_agendada}}.\n\nAl "
        "finalizar la videollamada, le explicaremos cómo recibirá su primer bono de $20.000 "
        "por su participación en el estudio.\n\n¿Podemos realizar la videollamada en este "
        "momento o prefiere que la contactemos más tarde?\n\n¡Muchas gracias por su "
        "compromiso! Le deseo un feliz día. 🌷"
    ),
    "primera_recogida_853_": (
        "¡Hola, señora {{nombre_entrevistada}}! ¿Cómo está? 😊\n\nMucho gusto, mi nombre es "
        "{{nombre_encuestador}}, del equipo de AZ Marketing Plus.\n\nLe escribo porque hace "
        "10 días le dejamos el shampoo 853 y para el día de hoy tiene programada una "
        "videollamada.\n\nEl objetivo es realizar un seguimiento al uso del shampoo, conocer "
        "cómo le ha ido con el producto y registrar su experiencia durante estos días.\n\n"
        "¿Me confirma si todavía tiene disponibilidad para realizarla a las "
        "{{hora_agendada}} o si prefiere que la hagamos en este momento?\n\nQuedo atento a "
        "su respuesta. ¡Muchas gracias y feliz día!"
    ),
    "sibate_encuesta_final": (
        "¡Muy buenos días, señora {{nombre_entrevistada}}! 😊\n\nLa saluda {{encuestador}}, "
        "de AZ Marketing Plus.\n\nLe escribo porque hoy tiene programada la videollamada del "
        "estudio de mascotas, relacionada con el producto que le entregamos para que lo "
        "probara su perrito. 🐶\n\n¿Sería posible realizarla en este momento o prefiere que "
        "la contactemos más tarde?\n\nQuedo atento a su respuesta. ¡Muchas gracias y feliz "
        "día! 🌷"
    ),
}

# --- Lista 1x1 vigente antes de esta entrega (solo debe sumarse KEY) ---
SINGLE_PREVIAS = [
    "manana_3",
    "shampo_primer",
    "shampo_segundo",
    "in_home_beta_385",
    "fatiga_729_r3",
    "sibate_encuesta_final",
    "final_beta",
    "primera_recogida_853_",
    "entrega_sibate_19_oct_sibate_1_204",
    "entrega_sibate_19_oct_sibate_2_302",
    "recordatorio_sibate_1_204",
    "recordatorio_sibate_2_302",
    "recibido",
]

# Key fuera del 1x1 de cualquier estudio: el envio debe seguir rechazandose.
NO_CONECTADA = "manana_3"

FALLAS = []


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


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="chk_729_admin",
            hashed_password=auth.get_password_hash("x"),
            role="superuser",
            full_name="Admin Check",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("[1] Catalogo del backend")
        cfg = main.WHATSAPP_TEMPLATE_MAP.get(KEY)
        check(cfg is not None, f"{KEY} esta en WHATSAPP_TEMPLATE_MAP")
        if cfg:
            check(cfg.get("name") == KEY, f"{KEY} name: {cfg.get('name')}")
            check(cfg.get("language") == "es", f"{KEY} language: {cfg.get('language')}")
            check(cfg.get("params") == PARAMS, f"{KEY} params: {cfg.get('params')}")
        check(main.WHATSAPP_TEMPLATE_LABELS.get(KEY) == LABEL,
              f"{KEY} label: {main.WHATSAPP_TEMPLATE_LABELS.get(KEY)}")
        check(main.WHATSAPP_TEMPLATE_BODIES.get(KEY) == CUERPO,
              f"{KEY} body byte-exacto en WHATSAPP_TEMPLATE_BODIES")

        print("[2] El catalogo la publica en 1x1 y en el masivo")
        catalogo = {t["key"]: t for t in main.whatsapp_templates_catalog(db=None, current_user=admin)}
        item = catalogo.get(KEY)
        check(item is not None, f"{KEY} esta en /whatsapp/templates")
        if item:
            check(item["body"] == CUERPO, f"{KEY} body del catalogo byte-exacto")
            check(item["name"] == KEY, f"{KEY} name del payload a Meta: {item['name']}")
            check(item["language"] == "es", f"{KEY} language del payload: {item['language']}")
            check(item["params"] == PARAMS, f"{KEY} params del payload: {item['params']}")
            check(item["label"] == LABEL, f"{KEY} label del catalogo: {item['label']}")
            check(item["single_eligible"] is True, f"{KEY} habilitada para 1x1 (single_eligible)")
        check(KEY in main.WHATSAPP_SINGLE_TEMPLATE_KEYS,
              f"{KEY} esta en WHATSAPP_SINGLE_TEMPLATE_KEYS (boton Plantillas 1x1)")
        check(set(catalogo) == set(main.WHATSAPP_TEMPLATE_MAP),
              "el masivo conserva todo el catalogo")
        check(KEY in catalogo, f"{KEY} aparece en el catalogo del masivo")

        print("[3] Render de las 3 variables")
        body = main._wa_render_template_body(
            KEY, {"nombre_entrevistada": "Ana", "encuestador": "Luis", "hora_agendada": "2:00 pm"}
        )
        check(body is not None, f"{KEY} se puede renderizar como texto libre")
        check(body is not None and "señora Ana" in body, "sustituye nombre_entrevistada")
        check(body is not None and "La saluda Luis" in body, "sustituye encuestador")
        check(body is not None and "a las 2:00 pm." in body, "sustituye hora_agendada")
        check(body is not None and "{{" not in body, f"{KEY} render sin variables pendientes")

        print("[4] Respaldo de vista previa del front")
        check(front_body(KEY) == CUERPO, f"{KEY} cuerpo del front byte-identico al backend")

        print("[5] Regresion de las plantillas hermanas y de la lista 1x1")
        for hermana, cuerpo in HERMANAS.items():
            check(main.WHATSAPP_TEMPLATE_BODIES.get(hermana) == cuerpo,
                  f"{hermana} conserva su cuerpo byte-exacto")
            check(front_body(hermana) == cuerpo,
                  f"{hermana} conserva su cuerpo byte-exacto en el front")
            check(hermana in main.WHATSAPP_SINGLE_TEMPLATE_KEYS,
                  f"{hermana} sigue en 1x1")
            check(hermana in catalogo, f"{hermana} sigue en el catalogo")
        check(main.WHATSAPP_SINGLE_TEMPLATE_KEYS[:len(SINGLE_PREVIAS) + 1] == SINGLE_PREVIAS + [KEY],
              "la lista 1x1 conserva el orden previo y suma la key nueva justo despues")

        print("[6] Conexion 1x1 y llenado en el envio")
        estudio = models.Study(code="B729", name="729 Sin Bono", is_active=True)
        db.add(estudio)
        db.commit()
        db.refresh(estudio)
        main.set_study_single_templates(
            estudio.id,
            main.StudySingleTemplatesUpdate(template_keys=[KEY]),
            db=db,
            current_user=admin,
        )
        keys = main.get_study_single_templates(
            estudio.id, db=db, current_user=admin)["single_template_keys"]
        check(keys == [KEY], f"{KEY} se conecta al 1x1 del estudio -> {keys}")

        llamada = models.Call(
            study_id=estudio.id,
            phone_number="3001234567",
            person_name="Ana Gomez",
            collection_time="2:00 pm",
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
        plantilla = (enviados[0].get("template") if enviados else {}) or {}
        check(plantilla.get("name") == KEY, f"el payload usa el name de Meta: {plantilla.get('name')}")
        componentes = plantilla.get("components") or []
        parametros = (componentes[0].get("parameters") if componentes else []) or []
        check([p.get("parameter_name") for p in parametros] == PARAMS,
              f"payload con los 3 parametros -> {[p.get('parameter_name') for p in parametros]}")
        check([p.get("text") for p in parametros] == ["Ana Gomez", "Admin Check", "2:00 pm"],
              f"payload con los valores llenados -> {[p.get('text') for p in parametros]}")

        antes = len(enviados)
        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(call_id=llamada.id, template_key=NO_CONECTADA),
                db=db,
                current_user=admin,
            )
            check(False, f"{NO_CONECTADA} no conectada deberia dar 403")
        except HTTPException as exc:
            check(exc.status_code == 403, f"{NO_CONECTADA} no conectada -> {exc.status_code}")
        check(len(enviados) == antes, "el rechazo no llamo a Meta")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} falla(s).")
        sys.exit(1)
    print("\nTodo OK.")
