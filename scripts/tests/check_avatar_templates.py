#!/usr/bin/env python3
"""Verifica las plantillas del estudio de freidoras de aire (Avatar) en catalogo, 1x1 y masivo.

Pedido del usuario (verbatim, L1 de odd/tasks/plantillas-avatar.md):

    ahora quiero cargar esta plantillas inicia_avatar · Spanish que dice Hola,
    {{encuestada}}! 😊 ¿Cómo estás? ... y esta recordatorio_avatar · Spanish que dice
    ¡Hola, {{entrevistado}}! 😊 ¿Cómo estás? ...

Decision del usuario (L2): los dos cuerpos se copian TAL CUAL, cortados como vienen en
el pedido ("...por confiar en AZ MARKETING" y "...por continuar participando con"), y el
ruido del chat ("10:25 pm", "Listo, ya la llene", "Mas tarde la lleno") queda afuera.

Comprueba contra el codigo real:
  1. Catalogo (/whatsapp/templates): name, idioma `es`, parametros en orden de
     aparicion, etiqueta legible y `single_eligible`.
  2. Cuerpos byte-exactos en WHATSAPP_TEMPLATE_BODIES y en el respaldo del front.
  3. Render: sustituye las variables, incluida {{entrevistado}}, sin dejar `{{...}}`.
  4. 1x1, masivo por estudio y masivo por lista mandan el payload exacto a Meta.
  5. Ninguna de las dos usa `dia`: no estan en BULK_DAY_TEMPLATES y se envian sin dia.
  6. Regresion: el catalogo solo suma las 2 keys (las 32 previas quedan igual y en el
     mismo orden) y la lista 1x1 solo suma las 2 al final.

Uso:    python scripts/tests/check_avatar_templates.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

# La base temporal tiene que quedar seteada ANTES de importar la app.
DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_avatar.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

from fastapi import HTTPException  # noqa: E402

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

KEY_INICIA = "inicia_avatar"
KEY_RECORDATORIO = "recordatorio_avatar"

# --- Cuerpos aprobados (verbatim del pedido, con los cortes tal cual) ---
BODY_INICIA = (
    "Hola, {{encuestada}}! 😊 ¿Cómo estás?\n"
    "\n"
    "Te saluda AZ MARKETING PLUS. Mi nombre es {{encuestador}}.\n"
    "\n"
    "Te contamos que hoy, 9 de noviembre, iniciamos nuestro estudio sobre el uso de las "
    "freidoras de aire (Air Fryer). \n"
    "\n"
    "📅 ¿Qué debes hacer?\n"
    "\n"
    "Desde hoy, 9 de noviembre, hasta el 9 de diciembre, debes diligenciar un formulario "
    "todos los días.\n"
    "\n"
    "Es muy sencillo:\n"
    "\n"
    "✅ Si utilizaste la freidora de aire, cuéntanos qué preparación realizaste y envíanos "
    "una fotografía de la preparación.\n"
    "\n"
    "✅ Si NO la utilizaste, simplemente selecciona la opción NO LA USÉ.\n"
    "\n"
    "🔢 Tu número de registro es: {{censo}}.\n"
    "\n"
    "📲 Ingresa diariamente a este enlace para responder el formulario:\n"
    "\n"
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSesadqYtsGrKwJ-un7GIGH1jTinLG_-HgYcdTjPmEiD7zRbcA/formResponse\n"
    "\n"
    "⚠️ ¡IMPORTANTE! Recuerda diligenciarlo TODOS LOS DÍAS, incluso si no utilizaste la "
    "freidora de aire.\n"
    "¡Muchas gracias por participar y por confiar en AZ MARKETING"
)

BODY_RECORDATORIO = (
    "¡Hola, {{entrevistado}}! 😊 ¿Cómo estás?\n"
    "\n"
    "Te saluda el equipo de AZ MARKETING PLUS.\n"
    "\n"
    "Hoy continuamos con nuestro estudio sobre el uso de tu freidora de aire (Air Fryer). 🍟\n"
    "\n"
    "Te recordamos que es muy importante seguir diligenciando el formulario TODOS LOS DÍAS, "
    "independientemente de si utilizaste o no tu freidora de aire.\n"
    "\n"
    "✅ Si la usaste, cuéntanos qué preparación realizaste y adjunta una fotografía del "
    "plato o alimento preparado.\n"
    "\n"
    "✅ Si no la usaste, simplemente selecciona la opción NO LA USÉ.\n"
    "\n"
    "🔢 Recuerda que tu número de registro es: {{censo}}.\n"
    "\n"
    "📲 Ingresa aquí para diligenciar la encuesta:\n"
    "\n"
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSesadqYtsGrKwJ-un7GIGH1jTinLG_-HgYcdTjPmEiD7zRbcA/viewform\n"
    "\n"
    "Si tienes alguna duda o inquietud, con mucho gusto estamos disponibles para ayudarte.\n"
    "¡Gracias por tu compromiso y por continuar participando con"
)

NUEVAS = {
    KEY_INICIA: {
        "params": ["encuestada", "encuestador", "censo"],
        "body": BODY_INICIA,
        "label": "Avatar — inicio del estudio (Air Fryer)",
    },
    KEY_RECORDATORIO: {
        "params": ["entrevistado", "censo"],
        "body": BODY_RECORDATORIO,
        "label": "Avatar — recordatorio diario (Air Fryer)",
    },
}

# --- Baseline: las 32 keys vigentes antes de esta entrega (no deben cambiar) ---
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
    "plantilla_inicio_semana_9_de_noviembre_sibate",
    "registro_noviembre_9_2026",
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
    "plantilla_inicio_semana_9_de_noviembre_sibate",
    "registro_noviembre_9_2026",
]

# Tripwire de largo para las hermanas de la entrega anterior (su cuerpo byte-exacto lo
# fija check_noviembre_9_sibate_templates.py; aca se detecta una edicion accidental).
LARGOS_HERMANAS = {
    "plantilla_inicio_semana_9_de_noviembre_sibate": 1021,
    "registro_noviembre_9_2026": 692,
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
    prefijo = '"%s": "' % key
    if prefijo not in bloque:
        return None
    inicio = bloque.index(prefijo) + len(prefijo)
    return json.loads('"' + bloque[inicio:bloque.index('",', inicio)] + '"')


def linea_front(nombre):
    src = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
    return next((ln for ln in src.splitlines() if ln.startswith("const " + nombre)), "")


def vars_front():
    src = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
    return src.split("const BULK_TEMPLATE_VARS = {", 1)[1].split("\n};", 1)[0]


def capturar_envios():
    enviados = []

    def _fake(path, payload):
        enviados.append(payload)
        return {"messages": [{"id": f"wamid.AVTR{len(enviados)}"}]}

    main._wa_graph_request = _fake
    return enviados


def valores_esperados():
    return {
        "encuestada": "Maria",
        "encuestado": "Maria",
        "entrevistado": "Maria",
        "entrevistada": "Maria",
        "encuestador": "Ana Check",
        "censo": "8877",
    }


def payload_esperado(key):
    valores = valores_esperados()
    return [
        {"type": "text", "text": valores.get(p, ""), "parameter_name": p}
        for p in NUEVAS[key]["params"]
    ]


def payload_lista(key):
    """Masivo por lista: el contacto solo trae nombre y telefono (censo vacio)."""
    valores = valores_esperados()
    valores["censo"] = ""
    return [
        {"type": "text", "text": valores.get(p, ""), "parameter_name": p}
        for p in NUEVAS[key]["params"]
    ]


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="chk_avatar_admin",
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
                check(item["label"] == esperado["label"] and item["language"] == "es",
                      f"{key} el catalogo publica label e idioma")
                check(item["params"] == esperado["params"],
                      f"{key} el catalogo publica los params en orden")
                check(item["single_eligible"] is True, f"{key} es elegible 1x1")

        print("[2] Cuerpos byte-exactos (backend y respaldo del front)")
        for key, esperado in NUEVAS.items():
            check(main.WHATSAPP_TEMPLATE_BODIES.get(key) == esperado["body"],
                  f"{key} cuerpo byte-exacto ({len(esperado['body'])} chars)")
            check(catalogo.get(key, {}).get("body") == esperado["body"],
                  f"{key} el catalogo expone el mismo cuerpo")
            check(front_body(key) == esperado["body"],
                  f"{key} cuerpo del front byte-identico al backend (vista previa)")

        print("[3] Render de las variables")
        body = main._wa_render_template_body(
            KEY_INICIA, {"encuestada": "Maria", "encuestador": "Ana", "censo": "8877"})
        check(body is not None and "Hola, Maria! 😊" in body, f"{KEY_INICIA} sustituye encuestada")
        check(body is not None and "Mi nombre es Ana." in body, f"{KEY_INICIA} sustituye encuestador")
        check(body is not None and "registro es: 8877." in body, f"{KEY_INICIA} sustituye censo")
        check(body is not None and "formResponse" in body, f"{KEY_INICIA} conserva su link")
        check(body is not None and "{{" not in body, f"{KEY_INICIA} render sin variables pendientes")

        body = main._wa_render_template_body(
            KEY_RECORDATORIO, {"entrevistado": "Maria", "censo": "8877"})
        check(body is not None and "¡Hola, Maria! 😊" in body,
              f"{KEY_RECORDATORIO} sustituye entrevistado")
        check(body is not None and "registro es: 8877." in body, f"{KEY_RECORDATORIO} sustituye censo")
        check(body is not None and "/viewform" in body, f"{KEY_RECORDATORIO} conserva su link")
        check(body is not None and "{{" not in body,
              f"{KEY_RECORDATORIO} render sin variables pendientes")

        print("[4] Regresion: el catalogo solo suma las 2 keys")
        check(set(catalogo) == set(PREVIAS) | set(NUEVAS),
              "el catalogo es exactamente las 32 previas + las 2 nuevas")
        check([k for k in catalogo if k not in PREVIAS] == list(NUEVAS),
              "el orden del catalogo solo agrega las 2 nuevas al final")
        check(main.WHATSAPP_SINGLE_TEMPLATE_KEYS == SINGLE_PREVIAS + list(NUEVAS),
              "la lista 1x1 solo suma las 2 keys nuevas al final")
        for key, largo in LARGOS_HERMANAS.items():
            actual = main.WHATSAPP_TEMPLATE_BODIES.get(key)
            check(actual is not None and len(actual) == largo,
                  f"{key} conserva su cuerpo (largo {largo})")
            check(front_body(key) is not None and len(front_body(key)) == largo,
                  f"{key} conserva su cuerpo en el front")

        print("[5] Ninguna usa el dia")
        dia_line = linea_front("BULK_DAY_TEMPLATES")
        for key in NUEVAS:
            check("'%s'" % key not in dia_line, f"{key} no esta en BULK_DAY_TEMPLATES")
            check("dia" not in NUEVAS[key]["params"], f"{key} no declara el parametro dia")
        vars_block = vars_front()
        check("'inicia_avatar': '{{encuestada}} · {{encuestador}} · {{censo}}'" in vars_block,
              "BULK_TEMPLATE_VARS documenta las variables de inicia_avatar")
        check("'recordatorio_avatar': '{{entrevistado}} · {{censo}}'" in vars_block,
              "BULK_TEMPLATE_VARS documenta las variables de recordatorio_avatar")

        print("[6] Conexion por estudio (masivo y 1x1)")
        estudio = models.Study(code="AVTR", name="Avatar Air Fryer", is_active=True)
        db.add(estudio)
        db.commit()
        db.refresh(estudio)
        main.set_study_templates(
            estudio.id, main.StudyTemplatesUpdate(template_keys=list(NUEVAS)),
            db=db, current_user=admin)
        check(main._study_template_keys(db, estudio.id) == list(NUEVAS),
              "el masivo acepta las 2 nuevas")
        main.set_study_single_templates(
            estudio.id, main.StudySingleTemplatesUpdate(template_keys=list(NUEVAS) + ["bono_final"]),
            db=db, current_user=admin)
        single = main.get_study_single_templates(
            estudio.id, db=db, current_user=admin)["single_template_keys"]
        check(single == list(NUEVAS), f"el 1x1 acepta las 2 nuevas y filtra bono_final -> {single}")

        llamada = models.Call(
            study_id=estudio.id, phone_number="3005550001", person_name="Maria",
            census="8877", collection_time="5:00 pm")
        llamada_masiva = models.Call(
            study_id=estudio.id, phone_number="3005550002", person_name="Maria",
            census="8877", collection_time="5:00 pm")
        db.add_all([llamada, llamada_masiva])
        db.commit()
        db.refresh(llamada)
        db.refresh(llamada_masiva)

        main._wa_require_send_window = lambda db, user: None
        main._wa_window_open = lambda db, phone: False
        enviados = capturar_envios()

        print("[7] 1x1 con el payload exacto")
        for key in NUEVAS:
            antes = len(enviados)
            try:
                main.whatsapp_send_template(
                    main.WhatsAppSendTemplateRequest(call_id=llamada.id, template_key=key),
                    db=db, current_user=admin)
            except HTTPException as exc:
                check(False, f"1x1 {key} -> HTTP {exc.status_code}: {exc.detail}")
                continue
            check(len(enviados) == antes + 1, f"1x1 {key} hace exactamente 1 request a Meta")
            if len(enviados) == antes + 1:
                plantilla = enviados[-1].get("template") or {}
                check(plantilla.get("name") == key, f"1x1 {key} usa el name de Meta")
                parametros = (plantilla.get("components") or [{}])[0].get("parameters") or []
                check(parametros == payload_esperado(key),
                      f"1x1 {key} payload exacto: {parametros}")

        print("[8] Masivo por estudio (bulk_link) y masivo por lista (send-bulk)")
        for key in NUEVAS:
            antes = len(enviados)
            try:
                main.whatsapp_send_template(
                    main.WhatsAppSendTemplateRequest(
                        call_id=llamada_masiva.id, template_key=key, bulk_link=True,
                        person_name="Maria", censo="8877"),
                    db=db, current_user=admin)
            except HTTPException as exc:
                check(False, f"bulk_link {key} -> HTTP {exc.status_code}: {exc.detail}")
                continue
            check(len(enviados) == antes + 1, f"bulk_link {key} hace 1 request a Meta")
            if len(enviados) == antes + 1:
                parametros = (enviados[-1]["template"].get("components") or [{}])[0].get(
                    "parameters") or []
                check(parametros == payload_esperado(key),
                      f"bulk_link {key} payload exacto: {parametros}")

            antes = len(enviados)
            try:
                main.whatsapp_send_bulk(
                    main.WhatsAppSendBulkRequest(
                        template_key=key, category="",
                        contacts=[main.WhatsAppBulkContact(nombre="Maria", telefono="3005550001")]),
                    db=db, current_user=admin)
            except HTTPException as exc:
                check(False, f"send-bulk {key} -> HTTP {exc.status_code}: {exc.detail}")
                continue
            check(len(enviados) == antes + 1, f"send-bulk {key} hace 1 request a Meta")
            if len(enviados) == antes + 1:
                parametros = (enviados[-1]["template"].get("components") or [{}])[0].get(
                    "parameters") or []
                check(parametros == payload_lista(key),
                      f"send-bulk {key} payload con el nombre (censo vacio): {parametros}")

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
