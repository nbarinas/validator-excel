#!/usr/bin/env python3
"""Verifica las cuatro plantillas del estudio Sibate 250 / SunTea durazno R1.

Pedido del usuario (verbatim, L1 de odd/tasks/plantillas-250-noviembre.md):

    suntea_durazno_r1 · entrega_sibate_250 ·
    concentrado__producto_semana_16_de_noviembre_250 ·
    recordatorio_sibate_semana_16_de_noviembre_250

Decisiones del pedido (L2):
  - La hora del chat ("12:07 pm"), los botones de respuesta rapida ("De una vez",
    "Mas tarde") y los rotulos "· Spanish"/"que dice" NO forman parte del cuerpo.
  - El nombre con doble guion bajo se conserva verbatim: es el identificador de Meta.
  - Los cortes del pedido ("...y explicar", "...del estudi") se conservan verbatim.
  - Ninguna plantilla usa una variable que el envio no resuelva ya.

Comprueba contra el codigo real:
  1. Catalogo (/whatsapp/templates): name, idioma, params en orden, etiqueta, single_eligible.
  2. Cuerpo byte-exacto en WHATSAPP_TEMPLATE_BODIES y en el respaldo del front.
  3. Render de las variables, sin `{{...}}` pendientes.
  4. 1x1 con el payload exacto de Meta para cada plantilla.
  5. Masivo por estudio (bulk_link) con el mismo payload.
  6. Solo la de registro diario pide el dia; la falta del dia se rechaza.
  7. Invariantes del catalogo y regresion de las hermanas Sibate.

Uso:    python scripts/tests/check_plantillas_250_noviembre.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_plantillas_250.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

from fastapi import HTTPException  # noqa: E402

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

SUNTEA = "suntea_durazno_r1"
ENTREGA = "entrega_sibate_250"
CONCENTRADO = "concentrado__producto_semana_16_de_noviembre_250"
RECORDATORIO = "recordatorio_sibate_semana_16_de_noviembre_250"

CUERPO_SUNTEA = (
    "Hola, señora {{encuestada}}, ¿cómo está? 😊\n"
    "\n"
    "Le saluda {{encuestador}}, del equipo de AZ Marketing Plus.\n"
    "\n"
    "El motivo de mi mensaje es recordarle que hace aproximadamente una semana le dejamos "
    "una muestra de SunTea sabor a durazno para que pudiera prepararla y probarla en casa.\n"
    "\n"
    "El día de hoy tenemos programada nuestra videollamada a las {{hora}}.\n"
    "\n"
    "¿En este momento tendría unos minutos disponibles para realizarla?\n"
    "\n"
    "Muchas gracias por su tiempo y colaboración. ¡Que tenga un feliz día! 🌷"
)

CUERPO_ENTREGA = (
    "Hola, {{encuestada}} 😊\n"
    "\n"
    "Te saluda el equipo de AZ Marketing Plus.\n"
    "\n"
    "Te escribimos para confirmar que el transportador ya te hizo entrega del producto, "
    "que comenzarás a utilizar a partir  de hoy\n"
    "\n"
    'Por favor, respóndenos "RECIBIDO" para confirmar que ya lo tienes.\n'
    "\n"
    "¡Muchas gracias! 🙌"
)

CUERPO_CONCENTRADO = (
    "AZ Marketing Plus\n"
    "Hola, {{encuestada}}. ¡Buenos días! Te saluda el equipo de AZ Marketing Plus.\n"
    "\n"
    "¡Hoy comenzamos la segunda fase del estudio con tu mascota {{mascota}}! 🐾 Muchas "
    "gracias por seguir participando y por tu compromiso.\n"
    "\n"
    "📅 Durante los próximos 7 días, deberás medir el tiempo que tu perrito tarda en comer "
    "su concentrado habitual, mezclado con el suplemento que te enviamos.\n"
    "\n"
    "🍽️ ¿Qué debes hacer cada día?\n"
    "\n"
    "1. Sirve el alimento mezclado con el suplemento.\n"
    "2. Mide el tiempo desde que le sirves hasta que termine de comer.\n"
    "3. Observa si empieza a comer de inmediato o si primero olfatea el alimento.\n"
    "4. Al finalizar, diligencia la encuesta del día.\n"
    "\n"
    "⏰ La actividad se realiza una sola vez al día. Puedes elegir el desayuno, almuerzo o "
    "cena, procurando mantener el mismo horario durante los 7 días.\n"
    "\n"
    "codigo {{censo}}\n"
    "\n"
    "🔗 Enlace para registrar tu actividad diaria:\n"
    "https://forms.gle/FQpVjm9oxPRACPUt8\n"
    "\n"
    "Bono de $30.000: Al completar los 7 días, nos comunicaremos contigo por WhatsApp para "
    "realizar la última encuesta y explicar"
)

CUERPO_RECORDATORIO = (
    "Saludos\n"
    "🐶 REGISTRO DIARIO – DÍA {{dia}}/7\n"
    "\n"
    "¡Hola, {{encuestada}}! 👋 Te saluda el equipo de AZ Marketing Plus.\n"
    "\n"
    "🐾 Hoy debes registrar el consumo de tu mascota, {{mascota}}, del concentrado mas  el "
    "producto entregado (código 204).\n"
    "\n"
    "🍽️ Registra una sola comida al día, manteniendo el mismo horario.\n"
    "\n"
    "⏱️ Mide el tiempo que tarda en comer y registra su comportamiento en la encuesta.\n"
    "\n"
    "🔢 Código de registro: {{censo}}\n"
    "\n"
    "🔗 Diligencia aquí la encuesta:\n"
    "https://forms.gle/FQpVjm9oxPRACPUt8\n"
    "\n"
    "¡Gracias por tu compromiso! 💚\n"
    "Recuerda completar el registro durante los 7 días del estudi"
)

PLANTILLAS = [
    {
        "key": SUNTEA,
        "label": "SunTea durazno — recordatorio de videollamada (R1)",
        "params": ["encuestada", "encuestador", "hora"],
        "cuerpo": CUERPO_SUNTEA,
        "vars": "{{encuestada}} · {{encuestador}} · {{hora}}",
        "pide_dia": False,
        "llamada": {"person_name": "Maria", "collection_time": "5:00 pm"},
        "dia": "",
        "render": {
            "encuestada": "Maria",
            "encuestador": "Ana",
            "hora": "5:00 pm",
        },
        "render_debe": [
            ("Hola, señora Maria, ¿cómo está? 😊", "sustituye encuestada"),
            ("Le saluda Ana, del equipo", "sustituye encuestador"),
            ("videollamada a las 5:00 pm.", "sustituye hora"),
        ],
        "payload": [
            {"type": "text", "text": "Maria", "parameter_name": "encuestada"},
            {"type": "text", "text": "Ana Check", "parameter_name": "encuestador"},
            {"type": "text", "text": "5:00 pm", "parameter_name": "hora"},
        ],
        "ruido": ["12:07"],
    },
    {
        "key": ENTREGA,
        "label": "Sibate 250 — confirmación de entrega del producto",
        "params": ["encuestada"],
        "cuerpo": CUERPO_ENTREGA,
        "vars": "{{encuestada}}",
        "pide_dia": False,
        "llamada": {"person_name": "Maria"},
        "dia": "",
        "render": {"encuestada": "Maria"},
        "render_debe": [
            ("Hola, Maria 😊", "sustituye encuestada"),
            ('respóndenos "RECIBIDO"', "conserva las comillas del pedido"),
        ],
        "payload": [
            {"type": "text", "text": "Maria", "parameter_name": "encuestada"},
        ],
        "ruido": ["12:07"],
    },
    {
        "key": CONCENTRADO,
        "label": "Sibate 250 — concentrado + producto (semana 16 de noviembre)",
        "params": ["encuestada", "mascota", "censo"],
        "cuerpo": CUERPO_CONCENTRADO,
        "vars": "{{encuestada}} · {{mascota}} · {{censo}}",
        "pide_dia": False,
        "llamada": {"person_name": "Maria", "dog_name": "Firulais", "census": "C250-01"},
        "dia": "",
        "render": {"encuestada": "Maria", "mascota": "Firulais", "censo": "C250-01"},
        "render_debe": [
            ("Hola, Maria. ¡Buenos días!", "sustituye encuestada"),
            ("con tu mascota Firulais! 🐾", "sustituye mascota"),
            ("codigo C250-01", "sustituye censo"),
        ],
        "payload": [
            {"type": "text", "text": "Maria", "parameter_name": "encuestada"},
            {"type": "text", "text": "Firulais", "parameter_name": "mascota"},
            {"type": "text", "text": "C250-01", "parameter_name": "censo"},
        ],
        "ruido": ["12:07"],
    },
    {
        "key": RECORDATORIO,
        "label": "Sibate 250 — recordatorio diario (semana 16 de noviembre)",
        "params": ["dia", "encuestada", "mascota", "censo"],
        "cuerpo": CUERPO_RECORDATORIO,
        "vars": "{{dia}} · {{encuestada}} · {{mascota}} · {{censo}}",
        "pide_dia": True,
        "llamada": {"person_name": "Maria", "dog_name": "Firulais", "census": "C250-02"},
        "dia": "3",
        "render": {"dia": "3", "encuestada": "Maria", "mascota": "Firulais",
                   "censo": "C250-02"},
        "render_debe": [
            ("DÍA 3/7", "sustituye dia"),
            ("¡Hola, Maria! 👋", "sustituye encuestada"),
            ("tu mascota, Firulais,", "sustituye mascota"),
            ("Código de registro: C250-02", "sustituye censo"),
        ],
        "payload": [
            {"type": "text", "text": "3", "parameter_name": "dia"},
            {"type": "text", "text": "Maria", "parameter_name": "encuestada"},
            {"type": "text", "text": "Firulais", "parameter_name": "mascota"},
            {"type": "text", "text": "C250-02", "parameter_name": "censo"},
        ],
        "ruido": ["12:08"],
    },
]

# Hermanas Sibate: comparten codigo (masivo, dia, censo) y no deben cambiar de forma.
HERMANAS = {
    "recordatorio_sibate_1_204": ["dia", "entrevistada", "mascota", "censo"],
    "recordatorio_sibate_2_302": ["dia", "encuestada", "mascota", "censo"],
    "recordatorio_semana_9_de_noviembre_sibate": ["dia", "encuestada", "mascotica", "censo"],
    "plantilla_inicio_semana_9_de_noviembre_sibate": ["entrevistada", "mascota", "censo"],
    "entrega_sibate_19_oct_sibate_1_204": [],
    "recibido": ["encuestada"],
}

FALLAS = []


def check(cond, msg):
    if cond:
        print(f"  OK    {msg}")
    else:
        print(f"  FALLA {msg}")
        FALLAS.append(msg)


def front_src():
    return (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")


def front_body(key):
    src = front_src()
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
        return {"messages": [{"id": f"wamid.P250{len(enviados)}"}]}

    main._wa_graph_request = _fake
    return enviados


def parametros_de(payload):
    plantilla = payload.get("template") or {}
    return (plantilla.get("components") or [{}])[0].get("parameters") or []


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="chk_250_admin",
            hashed_password=auth.get_password_hash("x"),
            role="superuser",
            full_name="Ana Check",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("[1] Catalogo del backend y vista previa del front")
        catalogo = {t["key"]: t for t in main.whatsapp_templates_catalog(current_user=admin)}
        for p in PLANTILLAS:
            key = p["key"]
            cfg = main.WHATSAPP_TEMPLATE_MAP.get(key)
            check(cfg is not None, f"{key} esta en WHATSAPP_TEMPLATE_MAP")
            if cfg:
                check(cfg.get("name") == key, f"{key} name de Meta: {cfg.get('name')}")
                check(cfg.get("language") == "es", f"{key} language: {cfg.get('language')}")
                check(cfg.get("params") == p["params"], f"{key} params: {cfg.get('params')}")
            check(main.WHATSAPP_TEMPLATE_LABELS.get(key) == p["label"],
                  f"{key} label: {main.WHATSAPP_TEMPLATE_LABELS.get(key)}")
            item = catalogo.get(key)
            check(item is not None, f"{key} esta en /whatsapp/templates")
            if item:
                check(item["params"] == p["params"] and item["language"] == "es",
                      f"{key} el catalogo publica params e idioma")
                check(item["single_eligible"] is True, f"{key} es elegible 1x1")

            print(f"[2] Cuerpo byte-exacto de {key}")
            cuerpo = p["cuerpo"]
            check(main.WHATSAPP_TEMPLATE_BODIES.get(key) == cuerpo,
                  f"{key} cuerpo byte-exacto ({len(cuerpo)} chars)")
            check(catalogo.get(key, {}).get("body") == cuerpo,
                  f"{key} el catalogo expone el mismo cuerpo")
            check(front_body(key) == cuerpo,
                  f"{key} cuerpo del front byte-identico al backend (vista previa)")
            for ruido in p["ruido"]:
                check(ruido not in cuerpo, f"{ruido!r} (hora del chat) no esta en el cuerpo")

        print("[3] Render de las variables")
        for p in PLANTILLAS:
            key = p["key"]
            body = main._wa_render_template_body(key, p["render"])
            check(body is not None, f"{key} tiene cuerpo renderizable")
            if body is None:
                continue
            for fragmento, desc in p["render_debe"]:
                check(fragmento in body, f"{key} {desc}")
            check("{{" not in body, f"{key} render sin variables pendientes")

        print("[4] Invariantes del catalogo")
        check(set(main.WHATSAPP_TEMPLATE_BODIES) <= set(main.WHATSAPP_TEMPLATE_MAP),
              "toda key con cuerpo existe en WHATSAPP_TEMPLATE_MAP")
        check(set(main.WHATSAPP_SINGLE_TEMPLATE_KEYS) <= set(main.WHATSAPP_TEMPLATE_MAP),
              "toda key 1x1 existe en WHATSAPP_TEMPLATE_MAP")
        sin_label = [k for k in main.WHATSAPP_TEMPLATE_MAP
                     if not main.WHATSAPP_TEMPLATE_LABELS.get(k)]
        check(sin_label == [], f"toda key del catalogo tiene etiqueta (faltan: {sin_label})")
        single_lista = main.WHATSAPP_SINGLE_TEMPLATE_KEYS
        for previa, siguiente in [(SUNTEA, ENTREGA), (ENTREGA, CONCENTRADO),
                                  (CONCENTRADO, RECORDATORIO)]:
            if previa in single_lista and siguiente in single_lista:
                check(single_lista.index(previa) < single_lista.index(siguiente),
                      f"{siguiente} se agrega despues de {previa}")
        check("shampo_729" in single_lista and SUNTEA in single_lista and
              single_lista.index("shampo_729") < single_lista.index(SUNTEA),
              f"{SUNTEA} se agrega despues de shampo_729")
        for hermana, params in HERMANAS.items():
            check(main.WHATSAPP_TEMPLATE_MAP.get(hermana, {}).get("params") == params,
                  f"{hermana} conserva sus parametros")
            check(hermana in catalogo, f"{hermana} sigue en el catalogo")

        print("[5] Front: variables del masivo y campo dia")
        src = front_src()
        dia_linea = next((ln for ln in src.splitlines()
                          if ln.startswith("const BULK_DAY_TEMPLATES")), "")
        vars_bloque = src.split("const BULK_TEMPLATE_VARS = {", 1)[1].split("\n};", 1)[0]
        for p in PLANTILLAS:
            key = p["key"]
            esperado = "'%s': '%s'" % (key, p["vars"])
            check(esperado in vars_bloque, f"BULK_TEMPLATE_VARS documenta {key}")
            en_dia = "'%s'" % key in dia_linea
            if p["pide_dia"]:
                check(en_dia, f"{key} esta en BULK_DAY_TEMPLATES (pide el dia)")
            else:
                check(not en_dia, f"{key} no esta en BULK_DAY_TEMPLATES")

        print("[6] Conexion por estudio (1x1 y masivo)")
        estudio = models.Study(code="B250Q", name="250 noviembre", is_active=True)
        db.add(estudio)
        db.commit()
        db.refresh(estudio)
        todas = [p["key"] for p in PLANTILLAS]
        main.set_study_templates(estudio.id, main.StudyTemplatesUpdate(template_keys=todas),
                                 db=db, current_user=admin)
        check(main._study_template_keys(db, estudio.id) == todas,
              "el masivo acepta las cuatro")
        main.set_study_single_templates(
            estudio.id, main.StudySingleTemplatesUpdate(template_keys=todas + ["bono_final"]),
            db=db, current_user=admin)
        single = main.get_study_single_templates(
            estudio.id, db=db, current_user=admin)["single_template_keys"]
        check(single == todas, f"el 1x1 acepta las cuatro y filtra bono_final -> {single}")

        llamadas = []
        for p in PLANTILLAS:
            n = len(llamadas) + 1
            una = models.Call(study_id=estudio.id, phone_number=f"30099900{n:02d}", **p["llamada"])
            otra = models.Call(study_id=estudio.id, phone_number=f"30099901{n:02d}", **p["llamada"])
            db.add_all([una, otra])
            db.commit()
            db.refresh(una)
            db.refresh(otra)
            llamadas.append((p, una, otra))

        main._wa_require_send_window = lambda db, user: None
        main._wa_window_open = lambda db, phone: False
        enviados = capturar_envios()

        print("[7] 1x1 con el payload exacto")
        for p, llamada, _ in llamadas:
            key = p["key"]
            antes = len(enviados)
            peticion = main.WhatsAppSendTemplateRequest(call_id=llamada.id, template_key=key)
            if p["dia"]:
                peticion.dia = p["dia"]
            try:
                main.whatsapp_send_template(peticion, db=db, current_user=admin)
            except HTTPException as exc:
                check(False, f"1x1 {key} -> HTTP {exc.status_code}: {exc.detail}")
                continue
            check(len(enviados) == antes + 1, f"1x1 {key} hace exactamente 1 request a Meta")
            if len(enviados) == antes + 1:
                check(enviados[-1]["template"].get("name") == key,
                      f"1x1 {key} usa el name de Meta")
                params = parametros_de(enviados[-1])
                check(params == p["payload"], f"1x1 {key} payload exacto: {params}")

        print("[8] Masivo por estudio (bulk_link)")
        for p, _, masiva in llamadas:
            key = p["key"]
            antes = len(enviados)
            peticion = main.WhatsAppSendTemplateRequest(
                call_id=masiva.id, template_key=key, bulk_link=True, person_name="Maria")
            if p["dia"]:
                peticion.dia = p["dia"]
            try:
                main.whatsapp_send_template(peticion, db=db, current_user=admin)
            except HTTPException as exc:
                check(False, f"bulk_link {key} -> HTTP {exc.status_code}: {exc.detail}")
                continue
            check(len(enviados) == antes + 1, f"bulk_link {key} hace 1 request a Meta")
            if len(enviados) == antes + 1:
                params = parametros_de(enviados[-1])
                check(params == p["payload"], f"bulk_link {key} payload exacto: {params}")

        print("[9] La plantilla de registro diario exige el dia")
        p, _, _ = next(x for x in llamadas if x[0]["pide_dia"])
        # Llamada aparte: la idempotencia de 30 s devolveria un duplicado en las ya usadas.
        sin_dia = models.Call(study_id=estudio.id, phone_number="3009990099",
                              person_name="Maria", dog_name="Firulais", census="C250-09")
        db.add(sin_dia)
        db.commit()
        db.refresh(sin_dia)
        antes = len(enviados)
        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(call_id=sin_dia.id, template_key=p["key"]),
                db=db, current_user=admin)
            check(False, f"{p['key']} sin dia deberia dar 400")
        except HTTPException as exc:
            check(exc.status_code == 400, f"{p['key']} sin dia -> {exc.status_code}")
        check(len(enviados) == antes, "el rechazo no llamo a Meta")

        print("[10] Una key 1x1 no conectada a este estudio sigue rechazandose")
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
