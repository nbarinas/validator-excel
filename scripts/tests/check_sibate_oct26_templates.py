#!/usr/bin/env python3
"""Verifica el cambio de plantillas del 26 de octubre (Sibate segunda fase).

Pedido del usuario (verbatim):
  * Agregar `plantilla_sibate_2_302_oct_1_26` (es) e `inicio_de_semana_sibate_1_204_oct_26`
    (es) para que el superusuario las vea y las pueda conectar en 1x1 y en envio masivo.
  * (Cambio posterior) El tramo del suplemento termina en `*codigo 302*` / `*código 204*`
    (negrita en Meta) y la vista previa del front lo tiene que mostrar en negrita.
  * Desactivar `sibate_encuesta_final`, `recordatorio_diario_semana_19_de_octubre_` e
    `inicio_semana_19_de_octu`: no deben verse mas porque no se van a usar.

Comprueba contra el codigo real:
  1. Las 2 nuevas estan en el catalogo (/whatsapp/templates) con name/language/params,
     etiqueta legible y elegibles para 1x1.
  2. El cuerpo del catalogo es byte-exacto respecto del pedido, en el backend y en el
     respaldo de vista previa del front.
  3. El render sustituye encuestada/mascota/censo y no deja ningun {{...}}.
  4. El 1x1 y el masivo las aceptan por estudio y el payload a Meta lleva sus parametros.
  5. Las 3 retiradas ya no estan en el catalogo ni en ningun dict del backend ni en el
     front, salieron de BULK_DAY_TEMPLATES y no se pueden enviar por 1x1 ni por masivo.
  6. Regresion: las plantillas con dia que siguen vivas conservan su flujo.

Uso:    python scripts/tests/check_sibate_oct26_templates.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

# La base temporal tiene que quedar seteada ANTES de importar la app.
DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_sibate_oct26.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402
from fastapi import HTTPException  # noqa: E402

FALLAS = []

# --- Cuerpos esperados (verbatim del pedido) ---
# El pedido trae el mismo mensaje para las dos plantillas; la unica diferencia
# entre los dos textos pegados es la linea del codigo de registro.
_CUERPO_BASE = (
    "Hola, {{encuestada}}. ¡Buenos días! Te saluda el equipo de AZ Marketing Plus.\n"
    "\n"
    "¡Hoy comenzamos la segunda fase del estudio con tu mascota {{mascota}}! 🐾 "
    "Muchas gracias por seguir participando y por tu compromiso.\n"
    "\n"
    "📅 Durante los próximos 7 días, deberás medir el tiempo que tu perrito tarda en "
    "comer su concentrado habitual, mezclado con el suplemento que te enviamos__PRODUCTO__.\n"
    "\n"
    "🍽️ ¿Qué debes hacer cada día?\n"
    "\n"
    "1. Sirve el alimento mezclado con el suplemento.\n"
    "2. Mide el tiempo desde que le sirves hasta que termine de comer.\n"
    "3. Observa si empieza a comer de inmediato o si primero olfatea el alimento.\n"
    "4. Al finalizar, diligencia la encuesta del día.\n"
    "\n"
    "⏰ La actividad se realiza una sola vez al día. Puedes elegir el desayuno, "
    "almuerzo o cena, procurando mantener el mismo horario durante los 7 días.\n"
    "\n"
    "__CODIGO__\n"
    "\n"
    "🔗 Enlace para registrar tu actividad diaria:\n"
    "https://forms.gle/kFrKRWKXFRkp6dhT9\n"
    "\n"
    "🎁 Bono de $30.000: Al completar los 7 días, nos comunicaremos contigo por WhatsApp"
)

KEY_302 = "plantilla_sibate_2_302_oct_1_26_fase2"
KEY_204 = "inicio_de_semana_sibate_1_204_oct_26"

NUEVAS = {
    KEY_302: {
        "params": ["encuestada", "mascota", "censo"],
        "body": _CUERPO_BASE.replace("__CODIGO__", "codigo de resistro censo: {{censo}}")
        .replace("__PRODUCTO__", " *codigo 302*"),
        "label": "Sibate 2 — producto 302 (segunda fase)",
    },
    KEY_204: {
        "params": ["encuestada", "mascota", "censo"],
        "body": _CUERPO_BASE.replace("__CODIGO__", "codigo de registro censo: {{censo}}")
        .replace("__PRODUCTO__", " *código 204*"),
        "label": "Inicio de semana Sibate 1 — producto 204",
    },
}

RETIRADAS = [
    "sibate_encuesta_final",
    "recordatorio_diario_semana_19_de_octubre_",
    "inicio_semana_19_de_octu",
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


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="chk_oct26",
            hashed_password=auth.get_password_hash("x"),
            role="superuser",
            full_name="Ana Check",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        study = models.Study(code="OCT26", name="Octubre 26", is_active=True)
        db.add(study)
        db.commit()
        db.refresh(study)

        call = models.Call(
            study_id=study.id,
            phone_number="3001230456",
            person_name="Maria",
            dog_name="Luna",
            census="8877",
            collection_time="5:00 pm",
        )
        db.add(call)
        db.commit()
        db.refresh(call)

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
        for key in NUEVAS:
            body = main._wa_render_template_body(
                key,
                {"encuestada": "Ana", "mascota": "Luna", "censo": "8877"},
            )
            check(body is not None and "Ana" in body and "Luna" in body and "8877" in body
                  and "{{" not in body, f"{key} sustituye encuestada/mascota/censo")
            check(body is not None and body.startswith("Hola, Ana. ¡Buenos días!"),
                  f"{key} el saludo queda con el nombre de la encuestada")

        print("[4] Conexion por estudio (masivo y 1x1) y payload a Meta")
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

        esperado_params = [
            {"type": "text", "text": "Maria", "parameter_name": "encuestada"},
            {"type": "text", "text": "Luna", "parameter_name": "mascota"},
            {"type": "text", "text": "8877", "parameter_name": "censo"},
        ]
        for key in NUEVAS:
            antes = len(enviados)
            try:
                main.whatsapp_send_template(
                    main.WhatsAppSendTemplateRequest(call_id=call.id, template_key=key),
                    db=db, current_user=admin,
                )
            except HTTPException as e:
                check(False, f"1x1 {key} -> HTTP {e.status_code}: {e.detail}")
                continue
            check(len(enviados) == antes + 1, f"1x1 {key} hace exactamente 1 request a Meta")
            if len(enviados) != antes + 1:
                continue
            plantilla = enviados[-1]["template"]
            check(plantilla == {"name": key, "language": {"code": "es"},
                                "components": [{"type": "body", "parameters": esperado_params}]},
                  f"1x1 {key} payload con encuestada/mascota/censo: {plantilla}")

            antes = len(enviados)
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
            except HTTPException as e:
                check(False, f"masivo {key} -> HTTP {e.status_code}: {e.detail}")
                continue
            check(len(enviados) == antes + 1, f"masivo {key} hace exactamente 1 request a Meta")
            if len(enviados) == antes + 1:
                plantilla = enviados[-1]["template"]
                check(plantilla.get("name") == key and plantilla.get("language") == {"code": "es"},
                      f"masivo {key} usa la plantilla y el idioma correctos")

        print("[5] Las 3 plantillas retiradas no estan en ningun lado")
        for key in RETIRADAS:
            check(key not in catalogo, f"{key} no esta en /whatsapp/templates")
            check(key not in main.WHATSAPP_TEMPLATE_MAP, f"{key} no esta en WHATSAPP_TEMPLATE_MAP")
            check(key not in main.WHATSAPP_TEMPLATE_LABELS, f"{key} no esta en WHATSAPP_TEMPLATE_LABELS")
            check(key not in main.WHATSAPP_TEMPLATE_BODIES, f"{key} no esta en WHATSAPP_TEMPLATE_BODIES")
            check(key not in main.WHATSAPP_SINGLE_TEMPLATE_KEYS,
                  f"{key} no esta en WHATSAPP_SINGLE_TEMPLATE_KEYS")
            check(key not in js, f"el front ya no menciona {key}")
            check("'%s'" % key not in dia_list, f"{key} no esta en BULK_DAY_TEMPLATES")

        print("[6] Las retiradas ya no se pueden enviar")
        for key in RETIRADAS:
            for nombre, llamada in (
                ("1x1", lambda k=key: main.whatsapp_send_template(
                    main.WhatsAppSendTemplateRequest(call_id=call.id, template_key=k),
                    db=db, current_user=admin)),
                ("masivo", lambda k=key: main.whatsapp_send_bulk(
                    main.WhatsAppSendBulkRequest(
                        template_key=k,
                        category="",
                        contacts=[main.WhatsAppBulkContact(nombre="Maria", telefono="3001230456")],
                        batch_size=20,
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

        print("[7] Regresion: las plantillas con dia siguen vivas")
        check(dia_list != "", "existe BULK_DAY_TEMPLATES")
        for key in DIAS_VIVAS:
            check("'%s'" % key in dia_list, f"{key} sigue en BULK_DAY_TEMPLATES")
        backend = (RAIZ / "backend" / "main.py").read_text(encoding="utf-8")
        check('if "dia" in template_params and not dia' in backend,
              "el backend sigue rechazando el envio sin dia")

        main.set_study_single_templates(
            study.id,
            main.StudySingleTemplatesUpdate(template_keys=["sibate_2"]),
            db=db,
            current_user=admin,
        )
        antes = len(enviados)
        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(call_id=call.id, template_key="sibate_2", dia="3"),
                db=db, current_user=admin,
            )
        except HTTPException as e:
            check(False, f"1x1 sibate_2 con dia -> HTTP {e.status_code}: {e.detail}")
        if len(enviados) == antes + 1:
            parametros = enviados[-1]["template"]["components"][0]["parameters"]
            check({"type": "text", "text": "3", "parameter_name": "dia"} in parametros,
                  "1x1 sibate_2 sigue mandando el dia digitado")

        print("[8] Las vistas previas del front sustituyen mascota y censo")
        for nombre in ("waRenderInlineTemplatePreview", "waRenderNewChatPreview",
                       "showWhatsAppTemplatePreview"):
            fuente = _func_src(js, nombre)
            check(r".replace(/\{\{mascota\}\}/g" in fuente, f"{nombre} sustituye {{{{mascota}}}}")
            check(r".replace(/\{\{censo\}\}/g" in fuente, f"{nombre} sustituye {{{{censo}}}}")
            check(r".replace(/\{\{encuestada\}\}/g" in fuente, f"{nombre} sustituye {{{{encuestada}}}}")

        print("[9] La negrita de la plantilla se ve en las vistas previas")
        helper = _func_src(js, "waFormatPreviewHtml")
        check(helper != "", "existe waFormatPreviewHtml")
        check("waEsc(" in helper, "waFormatPreviewHtml escapa el texto (waEsc)")
        check(r".replace(/\*([^*\n]+)\*/g, '<strong>$1</strong>')" in helper,
              "waFormatPreviewHtml convierte *texto* en <strong>")
        for nombre in ("waRenderInlineTemplatePreview", "waRenderNewChatPreview",
                       "showWhatsAppTemplatePreview", "bulkLinkRenderTemplatePreview"):
            fuente = _func_src(js, nombre)
            check("waFormatPreviewHtml(body)" in fuente, f"{nombre} usa waFormatPreviewHtml")

        print("[10] La negrita se rinde y el texto se escapa (node, codigo real)")
        waesc = re.search(r"const waEsc = \(s\) => \{.*?\n\};", js, re.S)
        check(waesc is not None, "encontre waEsc en el front")
        if waesc is not None and helper:
            harness = (waesc.group(0) + "\n" + helper +
                       "\nprocess.stdout.write(waFormatPreviewHtml("
                       "'Hola <b>Amiga</b> *código 204*.'));")
            res = subprocess.run(["node", "-e", harness], capture_output=True, text=True)
            check(res.returncode == 0, f"el helper corre en node ({res.stderr.strip()[:80]})")
            check(res.stdout == "Hola &lt;b&gt;Amiga&lt;/b&gt; <strong>código 204</strong>.",
                  f"render: negrita y escape HTML -> {res.stdout!r}")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} fallas.")
        sys.exit(1)
    print("\nTodo OK.")
