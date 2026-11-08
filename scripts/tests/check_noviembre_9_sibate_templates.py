#!/usr/bin/env python3
"""Verifica las plantillas del 9 de noviembre (Sibate) en catalogo, 1x1 y masivo.

Pedido del usuario (verbatim, L1 y L4 de odd/tasks/plantillas-noviembre-9-sibate.md):

    quiero agregar las plantillas de 1x1, masivo y en previu
    plantilla_inicio_semana_9_de_noviembre_sibate · Spanish que dice ENCUESTA DIARIA
    – 7 DÍAS ... y (L4, tras el rechazo en Meta) registro_noviembre_9_2026 · Spanish
    (SPA) REGISTRO DIARIO DÍA {{dia}}/7 ...

Decisiones del usuario:
  * L2: el nombre en Meta de la primera es `plantilla_inicio_semana_9_de_noviembre_sibate`
    (con el prefijo `plantilla_`, tal cual lo pego).
  * L4: la de recordatorio se rechazo y la aprobada se llama `registro_noviembre_9_2026`,
    saluda con `{{encuestada}}` y usa `{{mascotica}}` (literal, con t) en vez de `{{mascota}}`.
  * L2/L4: el ruido del chat pegajado ("6:17 pm", "Listo, ya lo llene", "Mas tarde lo
    lleno") no forma parte del cuerpo; el cuerpo cierra en "Muchas gracias" y en el link.

Comprueba contra el codigo real:
  1. Catalogo (/whatsapp/templates): name, idioma `es`, parametros en orden de
     aparicion, etiqueta legible y `single_eligible`.
  2. Cuerpos byte-exactos en WHATSAPP_TEMPLATE_BODIES y en el respaldo del front
     (WA_TEMPLATE_BODIES de frontend/call_center.js).
  3. Render del texto libre: sustituye todas las variables y no deja `{{...}}`.
  4. 1x1 y masivo por estudio (`bulk_link`) mandan el payload exacto a Meta; el
     masivo por lista (`send-bulk`) tambien.
  5. La plantilla de inicio NO exige el dia; la de recordatorio si: sin dia el 1x1,
     el masivo por estudio y `send-bulk` responden 400 sin llamar a Meta ni guardar
     mensajes.
  6. Regresion: el catalogo solo suma las 2 keys (las 30 previas quedan identicas),
     la lista 1x1 solo suma las 2 keys, y las plantillas hermanas que comparten
     codigo conservan su cuerpo byte-exacto.
  7. El front declara el dia en BULK_DAY_TEMPLATES solo para la de recordatorio.

Uso:    python scripts/tests/check_noviembre_9_sibate_templates.py
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
DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_noviembre_9_sibate.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

from fastapi import HTTPException  # noqa: E402

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

KEY_INICIO = "plantilla_inicio_semana_9_de_noviembre_sibate"
KEY_REGISTRO = "registro_noviembre_9_2026"

# --- Cuerpos aprobados (verbatim del pedido; el ruido del chat queda afuera) ---
BODY_INICIO = (
    "ENCUESTA DIARIA – 7 DÍAS\n"
    "¡Hola, {{entrevistada}}👋\n"
    "Te saluda el equipo de AZ Marketing Plus.\n"
    "\n"
    "Hoy iniciamos esta dinámica, que tendrá una duración de 7 semanas.\n"
    "\n"
    "Durante los próximos 7 días, deberás registrar diariamente el tiempo que tu "
    "perrito  {{mascota}}  tarda en consumir el concentrado o alimento que "
    "habitualmente le das.\n"
    "\n"
    "⏱️ ¿Qué debes hacer?\n"
    "\n"
    "Toma el tiempo desde el momento en que le sirves el alimento hasta que termina "
    "de comer.\n"
    "Observa atentamente su comportamiento al momento de alimentarse.\n"
    "Registra si comienza a comer inmediatamente o si primero olfatea el alimento "
    "antes de consumirlo.\n"
    "\n"
    "🍽️ Realiza esta actividad en una sola comida al día: desayuno, almuerzo o cena.\n"
    "\n"
    "📌 Importante: durante estos 7 días, procura mantener el mismo alimento y el "
    "mismo horario de alimentación, para garantizar un seguimiento consistente.\n"
    "\n"
    "📝 Recuerda diligenciar una encuesta cada día durante los 7 días.\n"
    "\n"
    "Tu código de registro es: {{censo}}\n"
    "\n"
    "🔗 INGRESA AQUÍ A LA ENCUESTA:\n"
    "https://forms.gle/cedqXEt1zPQXZcRt6\n"
    "Muchas gracias"
)

BODY_REGISTRO = (
    "REGISTRO DIARIO\n"
    "DÍA {{dia}}/7\n"
    "\n"
    "¡Hola, {{encuestada}}! 👋\n"
    "Te saluda el equipo de AZ Marketing Plus.\n"
    "\n"
    "Recuerda realizar hoy el registro del consumo de concentrado o purina de tu "
    "perro {{mascotica}}.\n"
    "\n"
    "📌 Recuerda:\n"
    "\n"
    "🍽️ Realiza el registro en una sola comida al día y procura mantener la misma "
    "comida y el mismo horario durante toda la semana.\n"
    "⏱️ Mide el tiempo desde que sirves el alimento hasta que tu perro termina de "
    "comer.\n"
    "👀 Observa atentamente su comportamiento durante la alimentación y registra tus "
    "observaciones en la encuesta.\n"
    "📝 Recuerda realizar un registro diario durante los 7 días.\n"
    "\n"
    "Tu código de registro es: {{censo}}\n"
    "\n"
    "🔗 INGRESA AQUÍ A LA ENCUESTA:\n"
    "https://forms.gle/HAtyTHjKxLYmtinz5"
)

NUEVAS = {
    KEY_INICIO: {
        "params": ["entrevistada", "mascota", "censo"],
        "body": BODY_INICIO,
        "label": "Inicio semana 9 de noviembre (Sibate) — encuesta diaria",
        "dia": False,
    },
    KEY_REGISTRO: {
        "params": ["dia", "encuestada", "mascotica", "censo"],
        "body": BODY_REGISTRO,
        "label": "Registro diario 9 de noviembre (Sibate)",
        "dia": True,
    },
}

# --- Baseline: las 30 keys vigentes antes de esta entrega (no deben cambiar) ---
PREVIAS = [
    "saludo_corto",
    "manana_3",
    "shampo_primer",
    "shampo_segundo",
    "in_home_beta_385",
    "fatiga_729_r3",
    "final_beta",
    "primera_recogida_853_",
    "bono_final",
    "bono_parcial",
    "siabate_producto",
    "solo_concentrado",
    "recibido",
    "sibate_2",
    "recordatorio",
    "sigue_interesado",
    "sibate_5_de_octubre",
    "siabate_6_de_octubre",
    "19_octubre",
    "registro_diario_fatiga_6_semanas",
    "sibate_90mas15_dias",
    "producto_310_90_dias",
    "producto_203_90_dias",
    "producto_402_90_dias",
    "sibate_encuesta_final",
    "entrega_sibate_19_oct_sibate_1_204",
    "entrega_sibate_19_oct_sibate_2_302",
    "recordatorio_sibate_1_204",
    "recordatorio_sibate_2_302",
    "729_sin_bono",
]

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
    "729_sin_bono",
]

# Hermana de codigo compartido: el cuerpo masivo que mas se parece a la de inicio.
HERMANAS = {
    "sibate_5_de_octubre": (
        "ENCUESTA DIARIA – 7 DÍAS\n\n¡Hola, {{encuestada}}! 👋\nTe saluda el equipo de "
        "AZ Marketing Plus.\n\nHoy iniciamos esta dinámica, que tendrá una duración de 7 "
        "semanas.\n\nDurante los próximos 7 días, deberás registrar diariamente el tiempo "
        "que tu perrito {{mascota}} tarda en consumir el concentrado o alimento que "
        "habitualmente le das.\n\n⏱️ ¿Qué debes hacer?\n\nToma el tiempo desde el momento "
        "en que le sirves el alimento hasta que termina de comer.\nObserva atentamente su "
        "comportamiento al momento de alimentarse.\nRegistra si comienza a comer "
        "inmediatamente o si primero olfatea el alimento antes de consumirlo.\n\n🍽️ "
        "Realiza esta actividad en una sola comida al día: desayuno, almuerzo o cena.\n\n"
        "📌 Importante: durante estos 7 días, procura mantener el mismo alimento y el "
        "mismo horario de alimentación, para garantizar un seguimiento consistente.\n\n"
        "📝 Recuerda diligenciar una encuesta cada día durante los 7 días.\n\nTu código de "
        "registro es: {{censo}}\n\n🔗 INGRESA AQUÍ A LA ENCUESTA:\n"
        "https://forms.gle/yCQVjX6fHKFqgkE59\n\nGracias"
    ),
    "recordatorio_sibate_1_204": (
        "🐶 REGISTRO DIARIO – DÍA {{dia}}/7\n\n¡Hola, {{entrevistada}}! 👋 Te saluda el "
        "equipo de AZ Marketing Plus.\n\n🐾 Hoy debes registrar el consumo de tu mascota, "
        "{{mascota}}, del concentrado mas  el producto entregado (código 204).\n\n🍽️ "
        "Registra una sola comida al día, manteniendo el mismo horario.\n\n⏱️ Mide el "
        "tiempo que tarda en comer y registra su comportamiento en la encuesta.\n\n🔢 "
        "Código de registro: {{censo}}\n\n🔗 Diligencia aquí la encuesta:\n"
        "https://forms.gle/pP9Fd9v5ZSTGjemX8\n\n¡Gracias por tu compromiso! 💚 Recuerda "
        "completar el registro durante los 7 días del estudio."
    ),
    "recordatorio_sibate_2_302": (
        "🐶 REGISTRO DIARIO – DÍA {{dia}}/7\n\n¡Hola, {{encuestada}}! 👋 Te saluda el "
        "equipo de AZ Marketing Plus.\n\n🐾 Hoy debes registrar el consumo de tu mascota, "
        "{{mascota}}, del concentrado mas  el producto entregado (código 302).\n\n🍽️ "
        "Registra una sola comida al día, manteniendo el mismo horario.\n\n⏱️ Mide el "
        "tiempo que tarda en comer y registra su comportamiento en la encuesta.\n\n🔢 "
        "Código de registro: {{censo}}\n\n🔗 Diligencia aquí la encuesta:\n"
        "https://forms.gle/pP9Fd9v5ZSTGjemX8\n\n¡Gracias por tu compromiso! 💚 Recuerda "
        "completar el registro durante los 7 días del estudio."
    ),
}

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


def linea_dia():
    src = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
    return next((ln for ln in src.splitlines() if ln.startswith("const BULK_DAY_TEMPLATES")), "")


def linea_vars():
    src = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
    return src.split("const BULK_TEMPLATE_VARS = {", 1)[1].split("\n};", 1)[0]


def capturar_envios():
    """Reemplaza el HTTP a Meta y devuelve la lista de payloads enviados."""
    enviados = []

    def _fake(path, payload):
        enviados.append(payload)
        return {"messages": [{"id": f"wamid.NOV9{len(enviados)}"}]}

    main._wa_graph_request = _fake
    return enviados


def payload_esperado(key, dia=None):
    params = NUEVAS[key]["params"]
    valores = {
        "entrevistada": "Maria",
        "encuestada": "Maria",
        "mascota": "Luna",
        "mascotica": "Luna",
        "censo": "8877",
        "dia": dia,
    }
    return [
        {"type": "text", "text": valores.get(p, ""), "parameter_name": p}
        for p in params
    ]


def payload_lista(key, dia):
    """Payload del masivo por lista: el contacto solo trae nombre y telefono.

    La mascota y el censo llegan vacios, igual que en toda la familia previa de
    recordatorios (204/302); para mandarlos hay que usar el masivo por estudio.
    """
    params = NUEVAS[key]["params"]
    nombre_params = {"entrevistada", "encuestada"}
    lista = []
    for p in params:
        if p == "dia":
            lista.append({"type": "text", "text": dia, "parameter_name": "dia"})
        elif p in nombre_params:
            lista.append({"type": "text", "text": "Maria", "parameter_name": p})
        else:
            lista.append({"type": "text", "text": "", "parameter_name": p})
    return lista


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="chk_nov9_admin",
            hashed_password=auth.get_password_hash("x"),
            role="superuser",
            full_name="Ana Check",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("[1] Catalogo del backend")
        catalogo = {t["key"]: t for t in main.whatsapp_templates_catalog(current_user=admin)}
        for key, esperado in NUEVAS.items():
            cfg = main.WHATSAPP_TEMPLATE_MAP.get(key)
            check(cfg is not None, f"{key} esta en WHATSAPP_TEMPLATE_MAP")
            if cfg:
                check(cfg.get("name") == key, f"{key} name de Meta: {cfg.get('name')}")
                check(cfg.get("language") == "es", f"{key} language: {cfg.get('language')}")
                check(cfg.get("params") == esperado["params"],
                      f"{key} params: {cfg.get('params')}")
            check(main.WHATSAPP_TEMPLATE_LABELS.get(key) == esperado["label"],
                  f"{key} label: {main.WHATSAPP_TEMPLATE_LABELS.get(key)}")
            item = catalogo.get(key)
            check(item is not None, f"{key} esta en /whatsapp/templates")
            if item:
                check(item["name"] == key and item["language"] == "es",
                      f"{key} el catalogo publica name/idioma a Meta")
                check(item["params"] == esperado["params"],
                      f"{key} el catalogo publica los params en orden")
                check(item["label"] == esperado["label"], f"{key} label del catalogo")
                check(item["single_eligible"] is True, f"{key} es elegible 1x1")

        print("[2] Cuerpos byte-exactos (backend y respaldo del front)")
        for key, esperado in NUEVAS.items():
            check(main.WHATSAPP_TEMPLATE_BODIES.get(key) == esperado["body"],
                  f"{key} cuerpo byte-exacto en WHATSAPP_TEMPLATE_BODIES "
                  f"({len(esperado['body'])} chars)")
            check(catalogo.get(key, {}).get("body") == esperado["body"],
                  f"{key} el catalogo expone el mismo cuerpo")
            check(front_body(key) == esperado["body"],
                  f"{key} cuerpo del front byte-identico al backend (vista previa)")

        print("[3] Render de las variables")
        body = main._wa_render_template_body(
            KEY_INICIO, {"entrevistada": "Maria", "mascota": "Luna", "censo": "8877"})
        check(body is not None and body.startswith("ENCUESTA DIARIA – 7 DÍAS"),
              f"{KEY_INICIO} arranca con el encabezado aprobado")
        check(body is not None and "¡Hola, Maria👋" in body,
              f"{KEY_INICIO} sustituye entrevistada")
        check(body is not None and "perrito  Luna  tarda" in body,
              f"{KEY_INICIO} sustituye mascota conservando los dobles espacios")
        check(body is not None and "https://forms.gle/cedqXEt1zPQXZcRt6" in body,
              f"{KEY_INICIO} conserva su link de encuesta")
        check(body is not None and "{{" not in body,
              f"{KEY_INICIO} render sin variables pendientes")

        body = main._wa_render_template_body(
            KEY_REGISTRO,
            {"dia": "3", "encuestada": "Maria", "mascotica": "Luna", "censo": "8877"})
        check(body is not None and body.startswith("REGISTRO DIARIO\nDÍA 3/7"),
              f"{KEY_REGISTRO} el encabezado usa el dia digitado en su propia linea")
        check(body is not None and "¡Hola, Maria! 👋" in body,
              f"{KEY_REGISTRO} sustituye encuestada")
        check(body is not None and "perro Luna." in body,
              f"{KEY_REGISTRO} sustituye mascotica (el nombre del parametro aprobado)")
        check(body is not None and "https://forms.gle/HAtyTHjKxLYmtinz5" in body,
              f"{KEY_REGISTRO} conserva su link de encuesta")
        check(body is not None and "{{" not in body,
              f"{KEY_REGISTRO} render sin variables pendientes")

        print("[4] Regresion: el catalogo solo suma las 2 keys")
        check(set(catalogo) == set(PREVIAS) | set(NUEVAS),
              "el catalogo es exactamente las 30 previas + las 2 nuevas")
        check([k for k in catalogo if k not in PREVIAS] == list(NUEVAS),
              "el orden del catalogo solo agrega las 2 nuevas al final")
        check(main.WHATSAPP_SINGLE_TEMPLATE_KEYS == SINGLE_PREVIAS + list(NUEVAS),
              "la lista 1x1 solo suma las 2 keys nuevas")
        for hermana, cuerpo in HERMANAS.items():
            check(main.WHATSAPP_TEMPLATE_BODIES.get(hermana) == cuerpo,
                  f"{hermana} conserva su cuerpo byte-exacto en el backend")
            check(hermana in catalogo, f"{hermana} sigue en el catalogo")
            if front_body(hermana) is not None:
                check(front_body(hermana) == cuerpo,
                      f"{hermana} conserva su cuerpo byte-exacto en el front")
        check(main.WHATSAPP_TEMPLATE_BODIES.get("729_sin_bono") == (
            "¡Muy buenos días, señora {{nombre_entrevistada}}! 😊\n\nLa saluda "
            "{{encuestador}}, de AZ Marketing Plus.\n\nLe escribo para recordarle que hoy "
            "tiene programada la cuarta videollamada del estudio de shampoo 729, a las "
            "{{hora_agendada}}.\n\n¿Podemos realizar la videollamada en este momento a mas "
            "tarde"), "729_sin_bono (la ultima del catalogo antes de esta entrega) no cambio")

        print("[5] El front declara el dia solo donde corresponde")
        dia_line = linea_dia()
        check("'%s'" % KEY_REGISTRO in dia_line,
              f"{KEY_REGISTRO} esta en BULK_DAY_TEMPLATES (pide el dia en el masivo)")
        check("'%s'" % KEY_INICIO not in dia_line,
              f"{KEY_INICIO} no esta en BULK_DAY_TEMPLATES (no usa dia)")
        for key in PREVIAS:
            if key in ("sibate_2", "registro_diario_fatiga_6_semanas", "sibate_90mas15_dias",
                       "recordatorio_sibate_1_204", "recordatorio_sibate_2_302"):
                check("'%s'" % key in dia_line, f"{key} sigue pidiendo el dia en el masivo")
        vars_block = linea_vars()
        for key, esperado in NUEVAS.items():
            vars_key = " · ".join("{{%s}}" % p for p in esperado["params"])
            check("'%s': '%s'" % (key, vars_key) in vars_block,
                  f"BULK_TEMPLATE_VARS documenta las variables de {key}")

        print("[6] Conexion por estudio (masivo y 1x1)")
        estudio = models.Study(code="NOV9", name="Sibate 9 de noviembre", is_active=True)
        db.add(estudio)
        db.commit()
        db.refresh(estudio)
        main.set_study_templates(
            estudio.id,
            main.StudyTemplatesUpdate(template_keys=list(NUEVAS)),
            db=db,
            current_user=admin,
        )
        check(main._study_template_keys(db, estudio.id) == list(NUEVAS),
              "el masivo acepta las 2 nuevas")
        main.set_study_single_templates(
            estudio.id,
            main.StudySingleTemplatesUpdate(template_keys=list(NUEVAS) + ["bono_final"]),
            db=db,
            current_user=admin,
        )
        single = main.get_study_single_templates(
            estudio.id, db=db, current_user=admin)["single_template_keys"]
        check(single == list(NUEVAS),
              f"el 1x1 acepta las 2 nuevas y filtra bono_final -> {single}")

        llamada = models.Call(
            study_id=estudio.id,
            phone_number="3001230789",
            person_name="Maria",
            dog_name="Luna",
            census="8877",
            collection_time="5:00 pm",
        )
        # Llamada aparte para el masivo: el 1x1 tiene guarda de idempotencia de 30 s
        # por llamada+plantilla, asi que reutilizar la misma seria un falso negativo.
        llamada_masiva = models.Call(
            study_id=estudio.id,
            phone_number="3001230790",
            person_name="Maria",
            dog_name="Luna",
            census="8877",
            collection_time="5:00 pm",
        )
        db.add_all([llamada, llamada_masiva])
        db.commit()
        db.refresh(llamada)
        db.refresh(llamada_masiva)

        main._wa_require_send_window = lambda db, user: None
        main._wa_window_open = lambda db, phone: False
        enviados = capturar_envios()

        print("[7] Sin dia, la de registro no se envia (y la de inicio si)")
        antes = len(enviados)
        mensajes_antes = db.query(models.WhatsAppMessage).count()
        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(
                    call_id=llamada.id, template_key=KEY_REGISTRO),
                db=db, current_user=admin,
            )
            check(False, f"1x1 {KEY_REGISTRO} sin dia deberia rechazarse")
        except HTTPException as exc:
            check(exc.status_code == 400
                  and exc.detail == "Indica el día del registro antes de enviar",
                  f"1x1 {KEY_REGISTRO} sin dia -> 400 '{exc.detail}'")
        check(len(enviados) == antes, "el rechazo no llamo a Meta")
        check(db.query(models.WhatsAppMessage).count() == mensajes_antes,
              "el rechazo no guardo ningun mensaje")
        try:
            main.whatsapp_send_bulk(
                main.WhatsAppSendBulkRequest(
                    template_key=KEY_REGISTRO,
                    category="",
                    contacts=[main.WhatsAppBulkContact(nombre="Maria", telefono="3001230789")],
                ),
                db=db, current_user=admin,
            )
            check(False, f"send-bulk {KEY_REGISTRO} sin dia deberia rechazarse")
        except HTTPException as exc:
            check(exc.status_code == 400
                  and exc.detail == "Indica el día del registro antes de enviar",
                  f"send-bulk {KEY_REGISTRO} sin dia -> 400 '{exc.detail}'")
        check(len(enviados) == antes, "send-bulk sin dia no llamo a Meta")

        print("[8] 1x1 con el payload exacto")
        for key, esperado in NUEVAS.items():
            dia = "3" if esperado["dia"] else None
            antes = len(enviados)
            try:
                main.whatsapp_send_template(
                    main.WhatsAppSendTemplateRequest(
                        call_id=llamada.id, template_key=key, dia=dia),
                    db=db, current_user=admin,
                )
            except HTTPException as exc:
                check(False, f"1x1 {key} -> HTTP {exc.status_code}: {exc.detail}")
                continue
            check(len(enviados) == antes + 1, f"1x1 {key} hace exactamente 1 request a Meta")
            if len(enviados) == antes + 1:
                plantilla = enviados[-1].get("template") or {}
                check(plantilla.get("name") == key, f"1x1 {key} usa el name de Meta")
                parametros = (plantilla.get("components") or [{}])[0].get("parameters") or []
                check(parametros == payload_esperado(key, dia),
                      f"1x1 {key} payload exacto: {parametros}")

        print("[9] Masivo por estudio (bulk_link) y masivo por lista (send-bulk)")
        for key, esperado in NUEVAS.items():
            dia = "4" if esperado["dia"] else None
            antes = len(enviados)
            try:
                main.whatsapp_send_template(
                    main.WhatsAppSendTemplateRequest(
                        call_id=llamada_masiva.id,
                        template_key=key,
                        bulk_link=True,
                        person_name="Maria",
                        nombre_mascota="Luna",
                        censo="8877",
                        dia=dia,
                    ),
                    db=db, current_user=admin,
                )
            except HTTPException as exc:
                check(False, f"bulk_link {key} -> HTTP {exc.status_code}: {exc.detail}")
                continue
            check(len(enviados) == antes + 1, f"bulk_link {key} hace 1 request a Meta")
            if len(enviados) == antes + 1:
                parametros = (enviados[-1]["template"].get("components") or [{}])[0].get(
                    "parameters") or []
                check(parametros == payload_esperado(key, dia),
                      f"bulk_link {key} payload exacto: {parametros}")

            antes = len(enviados)
            try:
                main.whatsapp_send_bulk(
                    main.WhatsAppSendBulkRequest(
                        template_key=key,
                        category="",
                        contacts=[main.WhatsAppBulkContact(
                            nombre="Maria", telefono="3001230789")],
                        dia=dia,
                    ),
                    db=db, current_user=admin,
                )
            except HTTPException as exc:
                check(False, f"send-bulk {key} -> HTTP {exc.status_code}: {exc.detail}")
                continue
            check(len(enviados) == antes + 1, f"send-bulk {key} hace 1 request a Meta")
            if len(enviados) == antes + 1:
                parametros = (enviados[-1]["template"].get("components") or [{}])[0].get(
                    "parameters") or []
                # En el masivo por lista el contacto solo trae nombre y telefono, asi
                # que mascota y censo llegan vacios: es el comportamiento previo de
                # toda la familia de recordatorios (204/302), no algo de esta entrega.
                esperado_lista = payload_lista(key, dia)
                check(parametros == esperado_lista,
                      f"send-bulk {key} payload con el nombre y el dia: {parametros}")

        print("[10] Una key 1x1 no conectada a este estudio sigue rechazandose")
        antes = len(enviados)
        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(
                    call_id=llamada.id, template_key="manana_3"),
                db=db, current_user=admin,
            )
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
