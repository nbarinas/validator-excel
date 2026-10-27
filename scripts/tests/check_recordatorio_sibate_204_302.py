#!/usr/bin/env python3
"""Verifica las plantillas de recordatorio diario Sibate 204 y 302.

Pedido del usuario (verbatim):
  * Agregar en 1x1 y en plantillas masivas `recordatorio_sibate_1_204` (es) y
    `recordatorio_sibate_2_302` (es), con el encabezado `DÍA {{dia}}/7`.
  * El dia se digita antes de enviar: la persona escribe el numero.
  * Retirar `inicio_de_semana_sibate_1_204_oct_26` y
    `plantilla_sibate_2_302_oct_1_26_fase2` porque no se van a usar.

Comprueba contra el codigo real:
  1. Las 2 nuevas estan en el catalogo (/whatsapp/templates) con name/language/params,
     etiqueta legible y elegibles para 1x1.
  2. El cuerpo del catalogo es byte-exacto, en el backend y en el respaldo del front.
  3. El render sustituye dia/entrevistada-o-encuestada/mascota/censo y no deja {{...}}.
  4. El 1x1 y el masivo por estudio (bulk_link) mandan los parametros correctos a Meta.
  5. Sin dia, el 1x1 y el masivo se rechazan sin mandar nada ni guardar registro.
  6. Las 2 retiradas salieron de todos los diccionarios y de BULK_DAY_TEMPLATES.
  7. Regresion: las plantillas con dia que siguen vivas conservan su flujo.

Uso:    python scripts/tests/check_recordatorio_sibate_204_302.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

# La base temporal tiene que quedar seteada ANTES de importar la app.
DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_recordatorio_sibate_204_302.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

from fastapi import HTTPException  # noqa: E402

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

FALLAS = []

KEY_204 = "recordatorio_sibate_1_204"
KEY_302 = "recordatorio_sibate_2_302"

# --- Cuerpos esperados (verbatim del pedido) ---
_CUERPO_BASE = (
    "🐶 REGISTRO DIARIO – DÍA {{dia}}/7\n"
    "\n"
    "¡Hola, __SALUDO__! 👋 Te saluda el equipo de AZ Marketing Plus.\n"
    "\n"
    "🐾 Hoy debes registrar el consumo de tu mascota, {{mascota}}, del concentrado mas  "
    "el producto entregado (código __CODIGO__).\n"
    "\n"
    "🍽️ Registra una sola comida al día, manteniendo el mismo horario.\n"
    "\n"
    "⏱️ Mide el tiempo que tarda en comer y registra su comportamiento en la encuesta.\n"
    "\n"
    "🔢 Código de registro: {{censo}}\n"
    "\n"
    "🔗 Diligencia aquí la encuesta:\n"
    "https://forms.gle/pP9Fd9v5ZSTGjemX8\n"
    "\n"
    "¡Gracias por tu compromiso! 💚 Recuerda completar el registro durante los 7 días del estudio."
)

NUEVAS = {
    KEY_204: {
        "params": ["dia", "entrevistada", "mascota", "censo"],
        "body": _CUERPO_BASE.replace("__SALUDO__", "{{entrevistada}}").replace("__CODIGO__", "204"),
        "label": "Recordatorio Sibate 1 — producto 204",
        "saludo": "entrevistada",
        "codigo": "204",
    },
    KEY_302: {
        "params": ["dia", "encuestada", "mascota", "censo"],
        "body": _CUERPO_BASE.replace("__SALUDO__", "{{encuestada}}").replace("__CODIGO__", "302"),
        "label": "Recordatorio Sibate 2 — producto 302",
        "saludo": "encuestada",
        "codigo": "302",
    },
}

RETIRADAS = [
    "inicio_de_semana_sibate_1_204_oct_26",
    "plantilla_sibate_2_302_oct_1_26_fase2",
]

DIAS_VIVAS = ["sibate_2", "registro_diario_fatiga_6_semanas", "sibate_90mas15_dias"]


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


def _linea_dia(js):
    return next((ln for ln in js.splitlines() if ln.startswith("const BULK_DAY_TEMPLATES")), "")


def _func_src(js, name):
    """Devuelve el texto de `function <name>(...) {...}` (conteo de llaves)."""
    anchor = "function " + name + "("
    i = js.find(anchor)
    if i == -1:
        return ""
    j = js.find("{", i)
    depth = 0
    while j < len(js):
        if js[j] == "{":
            depth += 1
        elif js[j] == "}":
            depth -= 1
            if depth == 0:
                return js[i:j + 1]
        j += 1
    return ""


def _payload(saludo_param, dia):
    return [
        {"type": "text", "text": dia, "parameter_name": "dia"},
        {"type": "text", "text": "Maria", "parameter_name": saludo_param},
        {"type": "text", "text": "Luna", "parameter_name": "mascota"},
        {"type": "text", "text": "8877", "parameter_name": "censo"},
    ]


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="chk_recordatorio",
            hashed_password=auth.get_password_hash("x"),
            role="superuser",
            full_name="Ana Check",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        study = models.Study(code="REC204", name="Recordatorio 204/302", is_active=True)
        db.add(study)
        db.commit()
        db.refresh(study)

        call_single = models.Call(
            study_id=study.id,
            phone_number="3001230456",
            person_name="Maria",
            dog_name="Luna",
            census="8877",
            collection_time="5:00 pm",
        )
        call_bulk = models.Call(
            study_id=study.id,
            phone_number="3001230456",
            person_name="Maria",
            dog_name="Luna",
            census="8877",
            collection_time="5:00 pm",
        )
        db.add_all([call_single, call_bulk])
        db.commit()
        db.refresh(call_single)
        db.refresh(call_bulk)

        js = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
        dia_list = _linea_dia(js)

        print("[1] Las 2 plantillas nuevas estan en el catalogo")
        catalogo = {t["key"]: t for t in main.whatsapp_templates_catalog(current_user=admin)}
        for key, esperado in NUEVAS.items():
            cfg = catalogo.get(key)
            check(cfg is not None, f"{key} esta en /whatsapp/templates")
            check(cfg is not None and cfg["name"] == key, f"{key} name = {key}")
            check(cfg is not None and cfg["language"] == "es", f"{key} idioma 'es'")
            check(cfg is not None and cfg["params"] == esperado["params"],
                  f"{key} parametros = {esperado['params']}")
            check(cfg is not None and cfg["label"] == esperado["label"],
                  f"{key} etiqueta legible = {esperado['label']}")
            check(cfg is not None and cfg["single_eligible"] is True, f"{key} es elegible 1x1")

        print("[2] Cuerpos byte-exactos (backend y respaldo del front)")
        for key, esperado in NUEVAS.items():
            body = main.WHATSAPP_TEMPLATE_BODIES.get(key)
            check(body == esperado["body"], f"{key} cuerpo byte-exacto ({len(esperado['body'])} chars)")
            check(catalogo.get(key, {}).get("body") == esperado["body"],
                  f"{key} el catalogo expone el mismo cuerpo")
            literal = '"%s": "%s",' % (key, esperado["body"].replace("\n", "\\n"))
            check(literal in js, f"WA_TEMPLATE_BODIES tiene el cuerpo de {key} (byte-exacto)")

        print("[3] Render de variables")
        for key, esperado in NUEVAS.items():
            body = main._wa_render_template_body(
                key,
                {
                    "dia": "3",
                    "entrevistada": "Maria",
                    "encuestada": "Maria",
                    "mascota": "Luna",
                    "censo": "8877",
                },
            )
            check(body is not None and body.startswith("🐶 REGISTRO DIARIO – DÍA 3/7"),
                  f"{key} el encabezado usa el dia digitado")
            check(body is not None and "Maria" in body and "Luna" in body and "8877" in body
                  and "{{" not in body, f"{key} sustituye nombre/mascota/censo")
            check(body is not None and f"(código {esperado['codigo']})" in body,
                  f"{key} conserva el codigo de producto {esperado['codigo']}")

        print("[4] Conexion por estudio (masivo y 1x1)")
        main.set_study_templates(
            study.id,
            main.StudyTemplatesUpdate(template_keys=list(NUEVAS.keys())),
            db=db,
            current_user=admin,
        )
        check(main._study_template_keys(db, study.id) == list(NUEVAS.keys()),
              "el masivo acepta las 2 nuevas")

        main.set_study_single_templates(
            study.id,
            main.StudySingleTemplatesUpdate(template_keys=list(NUEVAS.keys()) + ["bono_final"]),
            db=db,
            current_user=admin,
        )
        single = main.get_study_single_templates(study.id, db=db, current_user=admin)["single_template_keys"]
        check(single == list(NUEVAS.keys()), f"el 1x1 acepta las 2 nuevas y filtra bono_final -> {single}")

        main._wa_require_send_window = lambda db, user: None
        main._wa_window_open = lambda db, phone: False
        main.time.sleep = lambda *a, **k: None
        enviados = _capturar_envios()

        print("[5] Sin dia no se envia nada")
        for key in NUEVAS:
            for nombre, llamada in (
                ("1x1", lambda k=key: main.whatsapp_send_template(
                    main.WhatsAppSendTemplateRequest(call_id=call_single.id, template_key=k),
                    db=db, current_user=admin)),
                ("masivo", lambda k=key: main.whatsapp_send_template(
                    main.WhatsAppSendTemplateRequest(
                        call_id=call_bulk.id,
                        template_key=k,
                        bulk_link=True,
                    ),
                    db=db, current_user=admin)),
            ):
                antes = len(enviados)
                mensajes_antes = db.query(models.WhatsAppMessage).count()
                try:
                    llamada()
                    check(False, f"{nombre} {key} sin dia deberia rechazarse")
                except HTTPException as e:
                    check(e.status_code == 400
                          and e.detail == "Indica el día del registro antes de enviar",
                          f"{nombre} {key} sin dia -> 400 con el mensaje exacto "
                          f"({e.status_code}: {e.detail})")
                check(len(enviados) == antes, f"{nombre} {key} sin dia no manda nada a Meta")
                check(db.query(models.WhatsAppMessage).count() == mensajes_antes,
                      f"{nombre} {key} sin dia no guarda ningun registro")

        print("[6] Con dia, 1x1 y masivo mandan los parametros correctos")
        for idx, (key, esperado) in enumerate(NUEVAS.items(), start=3):
            dia = str(idx)
            esperado_params = _payload(esperado["saludo"], dia)

            antes = len(enviados)
            try:
                main.whatsapp_send_template(
                    main.WhatsAppSendTemplateRequest(
                        call_id=call_single.id,
                        template_key=key,
                        dia=dia,
                    ),
                    db=db, current_user=admin,
                )
            except HTTPException as e:
                check(False, f"1x1 {key} con dia -> HTTP {e.status_code}: {e.detail}")
                continue
            check(len(enviados) == antes + 1, f"1x1 {key} hace exactamente 1 request a Meta")
            if len(enviados) == antes + 1:
                plantilla = enviados[-1]["template"]
                check(plantilla == {"name": key, "language": {"code": "es"},
                                    "components": [{"type": "body", "parameters": esperado_params}]},
                      f"1x1 {key} payload con dia/entrevistada-o-encuestada/mascota/censo: {plantilla}")

            antes = len(enviados)
            try:
                main.whatsapp_send_template(
                    main.WhatsAppSendTemplateRequest(
                        call_id=call_bulk.id,
                        template_key=key,
                        bulk_link=True,
                        person_name="Maria",
                        nombre_mascota="Luna",
                        censo="8877",
                        dia=dia,
                    ),
                    db=db, current_user=admin,
                )
            except HTTPException as e:
                check(False, f"masivo {key} con dia -> HTTP {e.status_code}: {e.detail}")
                continue
            check(len(enviados) == antes + 1, f"masivo {key} hace exactamente 1 request a Meta")
            if len(enviados) == antes + 1:
                plantilla = enviados[-1]["template"]
                check(plantilla == {"name": key, "language": {"code": "es"},
                                    "components": [{"type": "body", "parameters": esperado_params}]},
                      f"masivo {key} payload con el dia y los datos del contacto: {plantilla}")

        print("[6b] El envio masivo por lista (send-bulk) tambien exige y manda el dia")
        for key in NUEVAS:
            antes = len(enviados)
            mensajes_antes = db.query(models.WhatsAppMessage).count()
            try:
                main.whatsapp_send_bulk(
                    main.WhatsAppSendBulkRequest(
                        template_key=key,
                        category="",
                        contacts=[main.WhatsAppBulkContact(nombre="Maria", telefono="3001230456")],
                        batch_size=20,
                    ),
                    db=db, current_user=admin,
                )
                check(False, f"send-bulk {key} sin dia deberia rechazarse")
            except HTTPException as e:
                check(e.status_code == 400
                      and e.detail == "Indica el día del registro antes de enviar",
                      f"send-bulk {key} sin dia -> 400 con el mensaje exacto "
                      f"({e.status_code}: {e.detail})")
            check(len(enviados) == antes, f"send-bulk {key} sin dia no manda nada a Meta")
            check(db.query(models.WhatsAppMessage).count() == mensajes_antes,
                  f"send-bulk {key} sin dia no guarda ningun registro")

        for key, esperado in NUEVAS.items():
            antes = len(enviados)
            try:
                main.whatsapp_send_bulk(
                    main.WhatsAppSendBulkRequest(
                        template_key=key,
                        category="",
                        contacts=[main.WhatsAppBulkContact(nombre="Maria", telefono="3001230456")],
                        batch_size=20,
                        dia="7",
                    ),
                    db=db, current_user=admin,
                )
            except HTTPException as e:
                check(False, f"send-bulk {key} con dia -> HTTP {e.status_code}: {e.detail}")
                continue
            check(len(enviados) == antes + 1, f"send-bulk {key} con dia hace 1 request a Meta")
            if len(enviados) == antes + 1:
                parametros = enviados[-1]["template"]["components"][0]["parameters"]
                check({"type": "text", "text": "7", "parameter_name": "dia"} in parametros,
                      f"send-bulk {key} manda el dia digitado (7)")
                check({"type": "text", "text": "Maria", "parameter_name": esperado["saludo"]} in parametros,
                      f"send-bulk {key} manda el nombre en {esperado['saludo']}")

        print("[7] Las 2 plantillas retiradas no estan en ningun lado")
        for key in RETIRADAS:
            check(key not in catalogo, f"{key} no esta en /whatsapp/templates")
            check(key not in main.WHATSAPP_TEMPLATE_MAP, f"{key} no esta en WHATSAPP_TEMPLATE_MAP")
            check(key not in main.WHATSAPP_TEMPLATE_LABELS, f"{key} no esta en WHATSAPP_TEMPLATE_LABELS")
            check(key not in main.WHATSAPP_TEMPLATE_BODIES, f"{key} no esta en WHATSAPP_TEMPLATE_BODIES")
            check(key not in main.WHATSAPP_SINGLE_TEMPLATE_KEYS,
                  f"{key} no esta en WHATSAPP_SINGLE_TEMPLATE_KEYS")
            check(key not in js, f"el front ya no menciona {key}")
            check("'%s'" % key not in dia_list, f"{key} no esta en BULK_DAY_TEMPLATES")

        print("[8] Las retiradas ya no se pueden enviar")
        for key in RETIRADAS:
            for nombre, llamada in (
                ("1x1", lambda k=key: main.whatsapp_send_template(
                    main.WhatsAppSendTemplateRequest(call_id=call_single.id, template_key=k),
                    db=db, current_user=admin)),
                ("masivo", lambda k=key: main.whatsapp_send_template(
                    main.WhatsAppSendTemplateRequest(
                        call_id=call_bulk.id,
                        template_key=k,
                        bulk_link=True,
                    ),
                    db=db, current_user=admin)),
            ):
                antes = len(enviados)
                mensajes_antes = db.query(models.WhatsAppMessage).count()
                try:
                    llamada()
                    check(False, f"{nombre} {key} deberia rechazarse")
                except HTTPException as e:
                    check(e.status_code == 400 and e.detail == "Plantilla no válida",
                          f"{nombre} {key} -> 400 Plantilla no válida ({e.status_code}: {e.detail})")
                check(len(enviados) == antes, f"{nombre} {key} no manda nada a Meta")
                check(db.query(models.WhatsAppMessage).count() == mensajes_antes,
                      f"{nombre} {key} no guarda ningun registro")

        print("[9] Las plantillas con dia que siguen vivas conservan su flujo")
        check(dia_list != "", "existe BULK_DAY_TEMPLATES")
        for key in NUEVAS:
            check("'%s'" % key in dia_list, f"{key} esta en BULK_DAY_TEMPLATES")
        for key in DIAS_VIVAS:
            check("'%s'" % key in dia_list, f"{key} sigue en BULK_DAY_TEMPLATES")
        backend = (RAIZ / "backend" / "main.py").read_text(encoding="utf-8")
        check('if "dia" in template_params and not dia' in backend,
              "el backend sigue rechazando el envio sin dia")

        print("[10] El front reemplaza entrevistada y muestra el dia en las vistas previas")
        for nombre in ("waRenderInlineTemplatePreview", "waRenderNewChatPreview",
                       "showWhatsAppTemplatePreview"):
            fuente = _func_src(js, nombre)
            check(r".replace(/\{\{entrevistada\}\}/g" in fuente,
                  f"{nombre} sustituye {{{{entrevistada}}}}")
            check(r".replace(/\{\{mascota\}\}/g" in fuente, f"{nombre} sustituye {{{{mascota}}}}")
            check(r".replace(/\{\{censo\}\}/g" in fuente, f"{nombre} sustituye {{{{censo}}}}")
        for nombre in ("waToggleNewChatLink", "waNewChatTemplateParams"):
            fuente = _func_src(js, nombre)
            check("params.includes('entrevistada')" in fuente,
                  f"{nombre} reconoce el parametro entrevistada")
        fuente_bulk = _func_src(js, "sendWhatsAppBulk")
        check("document.getElementById('waNewChatDay').value" in fuente_bulk,
              "sendWhatsAppBulk lee el dia digitado")
        check("payload.dia = dia" in fuente_bulk,
              "sendWhatsAppBulk manda el dia en el payload")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} fallas.")
        sys.exit(1)
    print("\nTodo OK.")
