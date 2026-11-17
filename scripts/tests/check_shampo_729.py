#!/usr/bin/env python3
"""Verifica la plantilla `shampo_729` (quinta videollamada del shampoo 729).

Pedido del usuario (verbatim, L1 de odd/tasks/plantilla-shampo-729.md):

    shampo_729 · Spanish que dice ¡Muy buenos días, señora {{entrevistada}}! 😊
    ... ¿Podemos realizar la videollamada en este momento a mas tarde?

Decisiones del pedido:
  - Los botones de respuesta rapida ("En este momento", "Mas tarde") y la hora del chat
    ("4:25 pm") NO forman parte del cuerpo, igual que en `729_sin_bono` y `853_sin_bono`.
  - `{{hora_agendada}}` se resuelve con `collection_time` del registro, como las hermanas.
  - El cuerpo se conserva verbatim, incluido el punto suelto de la linea siguiente a la hora.

Comprueba contra el codigo real:
  1. Catalogo (/whatsapp/templates): name, idioma, params en orden, etiqueta, single_eligible.
  2. Cuerpo byte-exacto en WHATSAPP_TEMPLATE_BODIES y en el respaldo del front.
  3. Render: entrevistada, encuestador y hora_agendada, sin `{{...}}`.
  4. 1x1 y masivo por estudio mandan los 3 parametros, con la hora del registro.
  5. No usa `dia`.
  6. Invariantes del catalogo: toda key de BODIES y de SINGLE existe en MAP, toda key de
     MAP tiene etiqueta, y las hermanas de la familia 729/853 conservan sus parametros.

Uso:    python scripts/tests/check_shampo_729.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_shampo_729.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

from fastapi import HTTPException  # noqa: E402

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

KEY = "shampo_729"
LABEL = "Shampoo 729 — quinta videollamada"
PARAMS = ["entrevistada", "encuestador", "hora_agendada"]

CUERPO = (
    "¡Muy buenos días, señora {{entrevistada}}! 😊\n"
    "\n"
    "La saluda {{encuestador}}, de AZ Marketing Plus.\n"
    "\n"
    "Le escribo para recordarle que hoy tiene programada la quinta videollamada del estudio "
    "de shampoo 729, a las {{hora_agendada}}.\n"
    ".\n"
    "\n"
    "¿Podemos realizar la videollamada en este momento a mas tarde?"
)

# Hermanas de la familia 729/853: comparten codigo y hora, no deben cambiar de forma.
HERMANAS = {
    "729_sin_bono": ["nombre_entrevistada", "encuestador", "hora_agendada"],
    "fatiga_729_r3": ["nombre_entrevistada", "encuestador", "hora_agendada"],
    "primera_recogida_853_": ["nombre_entrevistada", "nombre_encuestador", "hora_agendada"],
    "853_sin_bono": ["encuestada", "encuestador", "hora"],
}

FALLAS = []


def check(cond, msg):
    if cond:
        print(f"  OK    {msg}")
    else:
        print(f"  FALLA {msg}")
        FALLAS.append(msg)


def front_body(key):
    src = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
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
        return {"messages": [{"id": f"wamid.BS729{len(enviados)}"}]}

    main._wa_graph_request = _fake
    return enviados


def payload_esperado():
    return [
        {"type": "text", "text": "Maria", "parameter_name": "entrevistada"},
        {"type": "text", "text": "Ana Check", "parameter_name": "encuestador"},
        {"type": "text", "text": "5:00 pm", "parameter_name": "hora_agendada"},
    ]


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="chk_729_admin",
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
        for ruido in ("En este momento", "Mas tarde", "4:25"):
            check(ruido not in CUERPO, f"{ruido!r} (boton del chat) no esta en el cuerpo")

        print("[3] Render de las 3 variables")
        body = main._wa_render_template_body(
            KEY, {"entrevistada": "Maria", "encuestador": "Ana", "hora_agendada": "5:00 pm"})
        check(body is not None and body.startswith("¡Muy buenos días, señora Maria! 😊"),
              f"{KEY} sustituye entrevistada")
        check(body is not None and "La saluda Ana," in body, f"{KEY} sustituye encuestador")
        check(body is not None and "a las 5:00 pm.\n.\n" in body,
              f"{KEY} sustituye hora_agendada conservando el punto de la linea siguiente")
        check(body is not None and "{{" not in body, f"{KEY} render sin variables pendientes")

        print("[4] Invariantes del catalogo")
        check(set(main.WHATSAPP_TEMPLATE_BODIES) <= set(main.WHATSAPP_TEMPLATE_MAP),
              "toda key con cuerpo existe en WHATSAPP_TEMPLATE_MAP")
        check(set(main.WHATSAPP_SINGLE_TEMPLATE_KEYS) <= set(main.WHATSAPP_TEMPLATE_MAP),
              "toda key 1x1 existe en WHATSAPP_TEMPLATE_MAP")
        sin_label = [k for k in main.WHATSAPP_TEMPLATE_MAP
                     if not main.WHATSAPP_TEMPLATE_LABELS.get(k)]
        check(sin_label == [], f"toda key del catalogo tiene etiqueta (faltan: {sin_label})")
        check(KEY in main.WHATSAPP_SINGLE_TEMPLATE_KEYS,
              f"{KEY} esta en la lista 1x1")
        single_lista = main.WHATSAPP_SINGLE_TEMPLATE_KEYS
        check("853_sin_bono" in single_lista and
              single_lista.index("853_sin_bono") < single_lista.index(KEY),
              f"{KEY} se agrega despues de 853_sin_bono")
        for hermana, params in HERMANAS.items():
            check(main.WHATSAPP_TEMPLATE_MAP.get(hermana, {}).get("params") == params,
                  f"{hermana} conserva sus parametros")
            check(hermana in catalogo, f"{hermana} sigue en el catalogo")

        print("[5] No usa el dia")
        check("dia" not in PARAMS, f"{KEY} no declara el parametro dia")
        src = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
        dia_line = next((ln for ln in src.splitlines()
                         if ln.startswith("const BULK_DAY_TEMPLATES")), "")
        check("'%s'" % KEY not in dia_line, f"{KEY} no esta en BULK_DAY_TEMPLATES")
        vars_block = src.split("const BULK_TEMPLATE_VARS = {", 1)[1].split("\n};", 1)[0]
        check("'%s': '{{entrevistada}} · {{encuestador}} · {{hora_agendada}}'" % KEY
              in vars_block,
              "BULK_TEMPLATE_VARS documenta las variables de la plantilla")

        print("[6] Conexion por estudio (masivo y 1x1)")
        estudio = models.Study(code="B729Q", name="729 quinta", is_active=True)
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
            study_id=estudio.id, phone_number="3009990001", person_name="Maria",
            collection_time="5:00 pm")
        llamada_masiva = models.Call(
            study_id=estudio.id, phone_number="3009990002", person_name="Maria",
            collection_time="5:00 pm")
        db.add_all([llamada, llamada_masiva])
        db.commit()
        db.refresh(llamada)
        db.refresh(llamada_masiva)

        main._wa_require_send_window = lambda db, user: None
        main._wa_window_open = lambda db, phone: False
        enviados = capturar_envios()

        print("[7] 1x1 con el payload exacto (hora del registro)")
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
