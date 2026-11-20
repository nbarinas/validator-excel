#!/usr/bin/env python3
"""Verifica la plantilla `serum_1_llamada` (primera videollamada de sérum/óleo).

Pedido del usuario (verbatim):

    quiero agregar serum_1_llamada · Spanish que dice Hola, señora {{encuestada}}! 😊
    ¿Cómo está? Le saluda {{encuestador}}, del equipo de AZ Marketing Plus.
    Hace aproximadamente 15 días nos comunicamos con usted y le dejamos un producto para el
    cuidado del cabello (sérum, óleo o aceite). El día de hoy tenemos programada nuestra
    primera videollamada para conocer cómo le ha ido con el producto. Quería preguntarle si
    tiene unos minuticos disponibles para realizarla en este momento o si prefiere que la
    contactemos un poquito más tarde. Quedo atento a su respuesta. ¡Muchas gracias y que
    tenga un feliz día! 🌷
    Si de una vez / Mas tarde porfa
    que quede en 1x1 y masivo asi como en la previsualizacion

Decisiones del pedido:
  - Los botones de respuesta rápida ("Si de una vez", "Mas tarde porfa") y la hora del chat
    ("12:34 pm") NO forman parte del cuerpo, igual que en `853_sin_bono` y `729_sin_bono`.
  - Params `encuestada` y `encuestador`: el texto no menciona la hora de la videollamada.

Comprueba contra el codigo real:
  1. Catalogo (/whatsapp/templates): name, idioma, params en orden, etiqueta, single_eligible.
  2. Cuerpo byte-exacto en WHATSAPP_TEMPLATE_BODIES y en el respaldo del front.
  3. Render: sustituye encuestada y encuestador, sin `{{...}}` pendientes.
  4. Invariantes del catalogo: toda key de BODIES y de SINGLE existe en MAP, toda key de MAP
     tiene etiqueta, y las hermanas de videollamada conservan sus parametros.
  5. No usa `dia`.
  6. Conexion por estudio: el masivo y el 1x1 aceptan la nueva key.
  7. 1x1 y masivo por estudio mandan exactamente los 2 parametros.

Uso:    python scripts/tests/check_serum_1_llamada.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_serum_1_llamada.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

from fastapi import HTTPException  # noqa: E402

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

KEY = "serum_1_llamada"
LABEL = "Sérum / óleo — primera videollamada"
PARAMS = ["encuestada", "encuestador"]

CUERPO = (
    "Hola, señora {{encuestada}}! 😊 ¿Cómo está?\n"
    "\n"
    "Le saluda {{encuestador}}, del equipo de AZ Marketing Plus.\n"
    "\n"
    "Hace aproximadamente 15 días nos comunicamos con usted y le dejamos un producto "
    "para el cuidado del cabello (sérum, óleo o aceite).\n"
    "\n"
    "El día de hoy tenemos programada nuestra primera videollamada para conocer cómo le ha "
    "ido con el producto.\n"
    "\n"
    "Quería preguntarle si tiene unos minuticos disponibles para realizarla en este momento "
    "o si prefiere que la contactemos un poquito más tarde.\n"
    "\n"
    "Quedo atento a su respuesta. ¡Muchas gracias y que tenga un feliz día! 🌷"
)

# Hermanas de videollamada: comparten codigo, no deben cambiar de forma.
HERMANAS = {
    "853_sin_bono": ["encuestada", "encuestador", "hora"],
    "suntea_durazno_r1": ["encuestada", "encuestador", "hora"],
    "shampo_729": ["entrevistada", "encuestador", "hora_agendada"],
}

FALLAS = []


def check(cond, msg):
    if cond:
        print(f"  OK    {msg}")
    else:
        print(f"  FALLA {msg}")
        FALLAS.append(msg)


def leer_front():
    return (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")


def front_body(key):
    src = leer_front()
    bloque = src.split("const WA_TEMPLATE_BODIES = {", 1)[1].split("\n};", 1)[0]
    prefijo = '"%s": "' % key
    if prefijo not in bloque:
        return None
    inicio = bloque.index(prefijo) + len(prefijo)
    return json.loads('"' + bloque[inicio:bloque.index('",', inicio)] + '"')


def capturar_envios():
    enviados = []

    def _fake(path, payload):
        enviados.append(payload)
        return {"messages": [{"id": f"wamid.BSERUM{len(enviados)}"}]}

    main._wa_graph_request = _fake
    return enviados


def payload_esperado():
    return [
        {"type": "text", "text": "Maria", "parameter_name": "encuestada"},
        {"type": "text", "text": "Ana Check", "parameter_name": "encuestador"},
    ]


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="chk_serum_admin",
            hashed_password=auth.get_password_hash("x"),
            role="superuser",
            full_name="Ana Check",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("[1] Catalogo del backend")
        cfg = main.WHATSAPP_TEMPLATE_MAP.get(KEY)
        check(cfg is not None, f"{KEY} esta en WHATSAPP_TEMPLATE_MAP")
        if cfg:
            check(cfg.get("name") == KEY, f"{KEY} name de Meta: {cfg.get('name')}")
            check(cfg.get("language") == "es", f"{KEY} language: {cfg.get('language')}")
            check(cfg.get("params") == PARAMS, f"{KEY} params: {cfg.get('params')}")
        check(main.WHATSAPP_TEMPLATE_LABELS.get(KEY) == LABEL,
              f"{KEY} label: {main.WHATSAPP_TEMPLATE_LABELS.get(KEY)}")
        catalogo = {t["key"]: t for t in main.whatsapp_templates_catalog(current_user=admin)}
        item = catalogo.get(KEY)
        check(item is not None, f"{KEY} esta en /whatsapp/templates")
        if item:
            check(item["params"] == PARAMS and item["language"] == "es",
                  f"{KEY} el catalogo publica params e idioma")
            check(item["single_eligible"] is True, f"{KEY} es elegible 1x1")

        print("[2] Cuerpo byte-exacto (backend y respaldo del front)")
        check(main.WHATSAPP_TEMPLATE_BODIES.get(KEY) == CUERPO,
              f"{KEY} cuerpo byte-exacto ({len(CUERPO)} chars)")
        check(catalogo.get(KEY, {}).get("body") == CUERPO,
              f"{KEY} el catalogo expone el mismo cuerpo")
        check(front_body(KEY) == CUERPO,
              f"{KEY} cuerpo del front byte-identico al backend (vista previa)")
        for ruido in ("Si de una vez", "Mas tarde porfa", "12:34"):
            check(ruido not in CUERPO, f"{ruido!r} (boton del chat) no esta en el cuerpo")

        print("[3] Render de las 2 variables")
        body = main._wa_render_template_body(
            KEY, {"encuestada": "Maria", "encuestador": "Ana"})
        check(body is not None and body.startswith("Hola, señora Maria! 😊 ¿Cómo está?"),
              f"{KEY} sustituye encuestada")
        check(body is not None and "Le saluda Ana, del equipo de AZ Marketing Plus." in body,
              f"{KEY} sustituye encuestador")
        check(body is not None and body.endswith("¡Muchas gracias y que tenga un feliz día! 🌷"),
              f"{KEY} cierra el texto tal cual")
        check(body is not None and "{{" not in body, f"{KEY} render sin variables pendientes")

        print("[4] Invariantes del catalogo")
        check(set(main.WHATSAPP_TEMPLATE_BODIES) <= set(main.WHATSAPP_TEMPLATE_MAP),
              "toda key con cuerpo existe en WHATSAPP_TEMPLATE_MAP")
        check(set(main.WHATSAPP_SINGLE_TEMPLATE_KEYS) <= set(main.WHATSAPP_TEMPLATE_MAP),
              "toda key 1x1 existe en WHATSAPP_TEMPLATE_MAP")
        sin_label = [k for k in main.WHATSAPP_TEMPLATE_MAP
                     if not main.WHATSAPP_TEMPLATE_LABELS.get(k)]
        check(sin_label == [], f"toda key del catalogo tiene etiqueta (faltan: {sin_label})")
        check(KEY in main.WHATSAPP_SINGLE_TEMPLATE_KEYS, f"{KEY} esta en la lista 1x1")
        check(main.WHATSAPP_SINGLE_TEMPLATE_KEYS[-1] == KEY,
              f"{KEY} se anexa al final de la lista 1x1 (no reordena las previas)")
        check(list(main.WHATSAPP_TEMPLATE_MAP)[-1] == KEY,
              f"{KEY} se anexa al final de WHATSAPP_TEMPLATE_MAP")
        for hermana, params in HERMANAS.items():
            check(main.WHATSAPP_TEMPLATE_MAP.get(hermana, {}).get("params") == params,
                  f"{hermana} conserva sus parametros")
            check(hermana in catalogo, f"{hermana} sigue en el catalogo")

        print("[5] No usa el dia")
        check("dia" not in PARAMS, f"{KEY} no declara el parametro dia")
        dia_line = next((ln for ln in leer_front().splitlines()
                         if ln.startswith("const BULK_DAY_TEMPLATES")), "")
        check("'%s'" % KEY not in dia_line, f"{KEY} no esta en BULK_DAY_TEMPLATES")
        vars_block = leer_front().split("const BULK_TEMPLATE_VARS = {", 1)[1].split("\n};", 1)[0]
        check("'%s': '{{encuestada}} · {{encuestador}}'" % KEY in vars_block,
              "BULK_TEMPLATE_VARS documenta las variables de la plantilla")

        print("[6] Conexion por estudio (masivo y 1x1)")
        estudio = models.Study(code="SERUM1", name="Serum primera llamada", is_active=True)
        db.add(estudio)
        db.commit()
        db.refresh(estudio)
        main.set_study_templates(estudio.id, main.StudyTemplatesUpdate(template_keys=[KEY]),
                                 db=db, current_user=admin)
        check(main._study_template_keys(db, estudio.id) == [KEY], "el masivo acepta la nueva")
        main.set_study_single_templates(
            estudio.id, main.StudySingleTemplatesUpdate(template_keys=[KEY, "bono_final"]),
            db=db, current_user=admin)
        single = main.get_study_single_templates(
            estudio.id, db=db, current_user=admin)["single_template_keys"]
        check(single == [KEY], f"el 1x1 acepta la nueva y filtra bono_final -> {single}")

        llamada = models.Call(
            study_id=estudio.id, phone_number="3008890001", person_name="Maria")
        llamada_masiva = models.Call(
            study_id=estudio.id, phone_number="3008890002", person_name="Maria")
        db.add_all([llamada, llamada_masiva])
        db.commit()
        db.refresh(llamada)
        db.refresh(llamada_masiva)

        main._wa_require_send_window = lambda db, user: None
        main._wa_window_open = lambda db, phone: False
        enviados = capturar_envios()

        print("[7] 1x1 con el payload exacto")
        antes = len(enviados)
        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(call_id=llamada.id, template_key=KEY),
                db=db, current_user=admin)
        except HTTPException as exc:
            check(False, f"1x1 {KEY} -> HTTP {exc.status_code}: {exc.detail}")
        else:
            check(len(enviados) == antes + 1, f"1x1 {KEY} hace exactamente 1 request a Meta")
            if len(enviados) == antes + 1:
                plantilla = enviados[-1].get("template") or {}
                check(plantilla.get("name") == KEY, f"1x1 {KEY} usa el name de Meta")
                parametros = (plantilla.get("components") or [{}])[0].get("parameters") or []
                check(parametros == payload_esperado(),
                      f"1x1 {KEY} payload exacto: {parametros}")

        print("[8] Masivo por estudio (bulk_link)")
        antes = len(enviados)
        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(
                    call_id=llamada_masiva.id, template_key=KEY, bulk_link=True,
                    person_name="Maria"),
                db=db, current_user=admin)
        except HTTPException as exc:
            check(False, f"bulk_link {KEY} -> HTTP {exc.status_code}: {exc.detail}")
        else:
            check(len(enviados) == antes + 1, f"bulk_link {KEY} hace 1 request a Meta")
            if len(enviados) == antes + 1:
                parametros = (enviados[-1]["template"].get("components") or [{}])[0].get(
                    "parameters") or []
                check(parametros == payload_esperado(),
                      f"bulk_link {KEY} payload exacto: {parametros}")

        print("[9] Una key 1x1 no conectada a este estudio sigue rechazandose")
        antes = len(enviados)
        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(call_id=llamada.id, template_key="manana_3"),
                db=db, current_user=admin)
            check(False, "manana_3 no conectada deberia dar 403")
        except HTTPException as exc:
            check(exc.status_code == 403, f"manana_3 no conectada -> {exc.status_code}")
        check(len(enviados) == antes, "el rechazo no llamo a Meta")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} falla(s).")
        sys.exit(1)
    print("\nTodo OK.")
