#!/usr/bin/env python3
"""Verifica la plantilla `el_azul` (recordatorio del estudio Air Fryer).

Pedido del usuario (verbatim, L6 de odd/tasks/plantillas-avatar.md):

    el_azul · SpanishSaludos
    ¡Hola, {{encuestada}}! 😊 ¿Cómo estás? ... ¡Gracias por tu compromiso y por
    continuar participando con

Decisiones del usuario sobre el pegado: "Saludos" es la primera linea del cuerpo, y
el cierre se copia tal cual, cortado en "...participando con".

Notas del pedido:
  - Entra en lugar de `nuevo_recordatorio_avatar_noviembre`, que quedo en revision en
    Meta: misma familia, mismo link corto https://forms.gle/jhwUsEbh1Bf6rMG79, mismo
    saludo {{encuestada}} y {{censo}} como unicos parametros.
  - El ruido del chat ("7:02 pm", "Listo, ya lo llene", "Mas tarde lo lleno") queda afuera.
  - No usa {{dia}}.

Comprueba contra el codigo real:
  1. Catalogo (/whatsapp/templates): name, idioma `es`, parametros en orden, etiqueta y
     `single_eligible`.
  2. Cuerpo byte-exacto en WHATSAPP_TEMPLATE_BODIES y en el respaldo del front.
  3. Render: sustituye encuestada y censo sin dejar `{{...}}`.
  4. 1x1, masivo por estudio (bulk_link) y masivo por lista (send-bulk): payload exacto.
  5. No exige `dia` y no esta en BULK_DAY_TEMPLATES.
  6. Regresion: el catalogo conserva las 32 keys previas y suma esta al final; la lista
     1x1 conserva su prefijo de 16 y suma esta al final.

Uso:    python scripts/tests/check_recordatorio_avatar_noviembre.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_recordatorio_avatar_noviembre.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

from fastapi import HTTPException  # noqa: E402

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

KEY = "el_azul"
LABEL = "Air Fryer — recordatorio diario (azul)"
PARAMS = ["encuestada", "censo"]

CUERPO = (
    "Saludos\n"
    "¡Hola, {{encuestada}}! 😊 ¿Cómo estás?\n"
    "\n"
    "Te saluda el equipo de AZ MARKETING PLUS.\n"
    "\n"
    "Hoy continuamos con nuestro estudio sobre el uso de tu freidora de aire "
    "(Air Fryer). 🍟\n"
    "\n"
    "Te recordamos que es muy importante seguir diligenciando el formulario TODOS LOS "
    "DÍAS, independientemente de si utilizaste o no tu freidora de aire.\n"
    "\n"
    "✅ Si la usaste, cuéntanos qué preparación realizaste y adjunta una fotografía del "
    "plato o alimento preparado.\n"
    "\n"
    "✅ Si no la usaste, simplemente selecciona la opción NO LA USÉ.\n"
    "\n"
    "🔢 Recuerda que tu número de registro es: {{censo}}.\n"
    "\n"
    "📲 Ingresa aquí para diligenciar la encuesta:\n"
    "https://forms.gle/jhwUsEbh1Bf6rMG79\n"
    "\n"
    "Si tienes alguna duda o inquietud, con mucho gusto estamos disponibles para "
    "ayudarte.\n"
    "¡Gracias por tu compromiso y por continuar participando con"
)

# --- Baseline: las 32 keys vigentes antes de esta entrega ---
PREVIAS = [
    "saludo_corto", "manana_3", "shampo_primer", "shampo_segundo", "in_home_beta_385",
    "fatiga_729_r3", "final_beta", "primera_recogida_853_", "bono_final", "bono_parcial",
    "siabate_producto", "solo_concentrado", "recibido", "sibate_2", "recordatorio",
    "sigue_interesado", "sibate_5_de_octubre", "siabate_6_de_octubre", "19_octubre",
    "registro_diario_fatiga_6_semanas", "sibate_90mas15_dias", "producto_310_90_dias",
    "producto_203_90_dias", "producto_402_90_dias", "sibate_encuesta_final",
    "entrega_sibate_19_oct_sibate_1_204", "entrega_sibate_19_oct_sibate_2_302",
    "recordatorio_sibate_1_204", "recordatorio_sibate_2_302", "729_sin_bono",
    "plantilla_inicio_semana_9_de_noviembre_sibate",
    "recordatorio_semana_9_de_noviembre_sibate",
]

SINGLE_PREVIAS = [
    "manana_3", "shampo_primer", "shampo_segundo", "in_home_beta_385", "fatiga_729_r3",
    "sibate_encuesta_final", "final_beta", "primera_recogida_853_",
    "entrega_sibate_19_oct_sibate_1_204", "entrega_sibate_19_oct_sibate_2_302",
    "recordatorio_sibate_1_204", "recordatorio_sibate_2_302", "recibido", "729_sin_bono",
    "plantilla_inicio_semana_9_de_noviembre_sibate",
    "recordatorio_semana_9_de_noviembre_sibate",
]

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
        return {"messages": [{"id": f"wamid.AVNOV{len(enviados)}"}]}

    main._wa_graph_request = _fake
    return enviados


def payload_esperado(censo="8877"):
    return [
        {"type": "text", "text": "Maria", "parameter_name": "encuestada"},
        {"type": "text", "text": censo, "parameter_name": "censo"},
    ]


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="chk_av_nov_admin",
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
            check(item["label"] == LABEL and item["language"] == "es",
                  f"{KEY} el catalogo publica label e idioma")
            check(item["params"] == PARAMS, f"{KEY} el catalogo publica los params en orden")
            check(item["single_eligible"] is True, f"{KEY} es elegible 1x1")

        print("[2] Cuerpo byte-exacto (backend y respaldo del front)")
        check(main.WHATSAPP_TEMPLATE_BODIES.get(KEY) == CUERPO,
              f"{KEY} cuerpo byte-exacto ({len(CUERPO)} chars)")
        check(catalogo.get(KEY, {}).get("body") == CUERPO,
              f"{KEY} el catalogo expone el mismo cuerpo")
        check(front_body(KEY) == CUERPO,
              f"{KEY} cuerpo del front byte-identico al backend (vista previa)")

        print("[3] Render de las variables")
        body = main._wa_render_template_body(KEY, {"encuestada": "Maria", "censo": "8877"})
        check(body is not None and body.startswith("Saludos\n¡Hola, Maria! 😊"),
              f"{KEY} arranca con Saludos y sustituye encuestada")
        check(body is not None and "registro es: 8877." in body, f"{KEY} sustituye censo")
        check(body is not None and "forms.gle/jhwUsEbh1Bf6rMG79" in body,
              f"{KEY} conserva el link corto del formulario")
        check(body is not None and body.endswith("participando con"),
              f"{KEY} cierra el texto tal cual, cortado en 'participando con'")
        check(body is not None and "{{" not in body, f"{KEY} render sin variables pendientes")

        print("[4] Regresion: el catalogo solo suma esta key")
        check(set(PREVIAS) | {KEY} <= set(catalogo),
              "las 32 previas + la nueva siguen todas en el catalogo")
        check([k for k in catalogo if k not in PREVIAS][:1] == [KEY],
              "el orden del catalogo agrega la nueva justo despues de las previas")
        check(main.WHATSAPP_SINGLE_TEMPLATE_KEYS[:len(SINGLE_PREVIAS) + 1] ==
              SINGLE_PREVIAS + [KEY],
              "la lista 1x1 conserva el prefijo previo y suma la nueva al final")
        for hermana, largo in (("plantilla_inicio_semana_9_de_noviembre_sibate", 1021),
                               ("recordatorio_semana_9_de_noviembre_sibate", 581)):
            actual = main.WHATSAPP_TEMPLATE_BODIES.get(hermana)
            check(actual is not None and len(actual) == largo,
                  f"{hermana} conserva su cuerpo (largo {largo})")

        print("[5] No usa el dia")
        dia_line = next((ln for ln in leer_front().splitlines()
                         if ln.startswith("const BULK_DAY_TEMPLATES")), "")
        check("'%s'" % KEY not in dia_line, f"{KEY} no esta en BULK_DAY_TEMPLATES")
        check("dia" not in PARAMS, f"{KEY} no declara el parametro dia")
        vars_block = leer_front().split("const BULK_TEMPLATE_VARS = {", 1)[1].split("\n};", 1)[0]
        check("'%s': '{{encuestada}} · {{censo}}'" % KEY in vars_block,
              "BULK_TEMPLATE_VARS documenta las variables de la plantilla")

        print("[6] Conexion por estudio (masivo y 1x1)")
        estudio = models.Study(code="AVNOV", name="Avatar Noviembre", is_active=True)
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
            study_id=estudio.id, phone_number="3007770001", person_name="Maria",
            census="8877", collection_time="5:00 pm")
        llamada_masiva = models.Call(
            study_id=estudio.id, phone_number="3007770002", person_name="Maria",
            census="8877", collection_time="5:00 pm")
        db.add_all([llamada, llamada_masiva])
        db.commit()
        db.refresh(llamada)
        db.refresh(llamada_masiva)

        main._wa_require_send_window = lambda db, user: None
        main._wa_window_open = lambda db, phone: False
        enviados = capturar_envios()

        print("[7] 1x1 sin dia, con el payload exacto")
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

        print("[8] Masivo por estudio (bulk_link) y masivo por lista (send-bulk)")
        antes = len(enviados)
        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(
                    call_id=llamada_masiva.id, template_key=KEY, bulk_link=True,
                    person_name="Maria", censo="8877"),
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

        antes = len(enviados)
        try:
            main.whatsapp_send_bulk(
                main.WhatsAppSendBulkRequest(
                    template_key=KEY, category="",
                    contacts=[main.WhatsAppBulkContact(nombre="Maria", telefono="3007770001")]),
                db=db, current_user=admin)
        except HTTPException as exc:
            check(False, f"send-bulk {KEY} -> HTTP {exc.status_code}: {exc.detail}")
        else:
            check(len(enviados) == antes + 1, f"send-bulk {KEY} hace 1 request a Meta")
            if len(enviados) == antes + 1:
                parametros = (enviados[-1]["template"].get("components") or [{}])[0].get(
                    "parameters") or []
                check(parametros == payload_esperado(censo=""),
                      f"send-bulk {KEY} manda el nombre (censo vacio en el masivo por lista): "
                      f"{parametros}")

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
