#!/usr/bin/env python3
"""Verifica el cambio de plantillas del call center pedido el 19 de octubre.

Pedido:
  * Quitar del catalogo las 3 plantillas "Concentrado producto Sibate 1/2/3"
    (no deben verse en ningun lado).
  * Agregar 3 plantillas nuevas, visibles en masivo, en 1x1 y en la vista previa
    del front: `sibate_encuesta_final`, `recordatorio_diario_semana_19_de_octubre_`
    e `inicio_semana_19_de_octu` (idioma es).

Comprueba contra el codigo real:
  1. Las 3 quitadas ya no estan en el catalogo ni en ningun dict del backend.
  2. Las 3 nuevas estan en el catalogo con name/language/params correctos y son
     elegibles para 1x1.
  3. El cuerpo del catalogo es byte-exacto respecto del pedido.
  4. El render sustituye todas sus variables (no queda ningun {{...}}).
  5. El masivo y el 1x1 conectan las 3 nuevas por estudio, y un no-elegible sigue
     rechazandose en 1x1.
  6. El front (frontend/call_center.js) guarda los mismos cuerpos como respaldo de
     la vista previa, ya no menciona las 3 quitadas y sustituye mascota/censo.

Uso:    python scripts/tests/check_sibate_oct19_templates.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

# La base temporal tiene que quedar seteada ANTES de importar la app.
DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_sibate_oct19.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

FALLAS = []

# --- Cuerpos esperados (verbatim del pedido) ---
BODY_FINAL = (
    "¡Muy buenos días, señora {{nombre_entrevistada}}! 😊\n"
    "\n"
    "La saluda {{encuestador}}, de AZ Marketing Plus.\n"
    "\n"
    "Le escribo porque hoy tiene programada la videollamada del estudio de mascotas, "
    "relacionada con el producto que le entregamos para que lo probara su perrito. 🐶\n"
    "\n"
    "¿Sería posible realizarla en este momento o prefiere que la contactemos más tarde?\n"
    "\n"
    "Quedo atento a su respuesta. ¡Muchas gracias y feliz día! 🌷"
)

BODY_RECORDATORIO = (
    "🐶 REGISTRO DIARIO – DÍA {{dia}}\n"
    "\n"
    "¡Hola, {{encuestada}}! 👋\n"
    "Te saluda el equipo de AZ Marketing Plus.\n"
    "\n"
    "📅 Hoy corresponde realizar el registro diario del consumo de tu perrita {{mascota}}. 🐾\n"
    "\n"
    "🍽️ Recuerda registrar una sola comida al día, procurando mantener el mismo alimento y "
    "horario durante toda la semana.\n"
    "\n"
    "⏱️ Mide el tiempo desde que le sirves el alimento hasta que termine de comer.\n"
    "\n"
    "👀 Observa su comportamiento al alimentarse y registra tus observaciones en la encuesta.\n"
    "\n"
    "📝 ¡Ya casi terminamos! Recuerda completar el registro diario durante los 7 días del estudio.\n"
    "\n"
    "🔢 Código de registro: {{censo}}\n"
    "\n"
    "🔗 INGRESA AQUÍ A LA ENCUESTA:\n"
    "https://forms.gle/t8yGGbVwugRpNKK67\n"
    "\n"
    "¡Muchas gracias por tu compromiso y participación! 🐶💚"
)

BODY_INICIO = (
    "ENCUESTA DIARIA – 7 DÍAS\n"
    "¡Hola, {{encuestada}}! 👋\n"
    "Te saluda el equipo de AZ Marketing Plus.\n"
    "\n"
    "Hoy iniciamos el registro diario con tu perrito {{mascota}}. 🐾\n"
    "\n"
    "📅 La dinámica completa dura 7 semanas, y durante estos primeros 7 días registrarás "
    "diariamente el tiempo que tarda tu mascota en consumir su alimento habitual.\n"
    "\n"
    "⏱️ ¿Qué debes hacer?\n"
    "\n"
    "Mide el tiempo desde que sirves el alimento hasta que termina de comer.\n"
    "\n"
    "Observa si comienza a comer inmediatamente o si primero olfatea el alimento.\n"
    "\n"
    "Registra la información en la encuesta diaria.\n"
    "\n"
    "🍽️ Realiza el registro en una sola comida al día: desayuno, almuerzo o cena.\n"
    "\n"
    "📌 Importante: mantener  en lo posible, el mismo horario durante estos 7 días.\n"
    "\n"
    "📝 Recuerda diligenciar una encuesta cada día, durante los 7 días.\n"
    "\n"
    "🔑 Código de registro: {{censo}}\n"
    "\n"
    "🔗 Ingresa aquí a la encuesta:\n"
    "https://forms.gle/JtjAMgbwLKG5UrpP6\n"
    "\n"
    "Gracias\n"
    "¡Muchas gracias por tu compromiso y colaboración!"
)

QUITADAS = [
    "concentrado__producto_sibate_3_402",
    "concentrado__producto_sibate_2_203",
    "conce_prodcuto_sibate_1_310",
]

NUEVAS = {
    "sibate_encuesta_final": {
        "params": ["nombre_entrevistada", "encuestador"],
        "body": BODY_FINAL,
    },
    "recordatorio_diario_semana_19_de_octubre_": {
        "params": ["dia", "encuestada", "mascota", "censo"],
        "body": BODY_RECORDATORIO,
    },
    "inicio_semana_19_de_octu": {
        "params": ["encuestada", "mascota", "censo"],
        "body": BODY_INICIO,
    },
}


def check(cond, msg):
    if cond:
        print(f"  OK    {msg}")
    else:
        print(f"  FALLA {msg}")
        FALLAS.append(msg)


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
            username="chk_oct19",
            hashed_password=auth.get_password_hash("x"),
            role="superuser",
            full_name="Admin Oct19",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("[1] Las 3 plantillas quitadas no existen")
        catalogo = {t["key"]: t for t in main.whatsapp_templates_catalog(current_user=admin)}
        for key in QUITADAS:
            check(key not in catalogo, f"{key} no esta en /whatsapp/templates")
            check(key not in main.WHATSAPP_TEMPLATE_MAP, f"{key} no esta en WHATSAPP_TEMPLATE_MAP")
            check(key not in main.WHATSAPP_TEMPLATE_LABELS, f"{key} no esta en WHATSAPP_TEMPLATE_LABELS")
            check(key not in main.WHATSAPP_TEMPLATE_BODIES, f"{key} no esta en WHATSAPP_TEMPLATE_BODIES")

        print("[2] Las 3 plantillas nuevas estan en el catalogo")
        for key, esperado in NUEVAS.items():
            cfg = catalogo.get(key)
            check(cfg is not None, f"{key} esta en el catalogo")
            check(cfg is not None and cfg["name"] == key, f"{key} name = {key}")
            check(cfg is not None and cfg["language"] == "es", f"{key} idioma 'es'")
            check(cfg is not None and cfg["params"] == esperado["params"],
                  f"{key} parametros = {esperado['params']}")
            check(cfg is not None and cfg["single_eligible"] is True, f"{key} es elegible 1x1")

        print("[3] Cuerpos byte-exactos")
        for key, esperado in NUEVAS.items():
            body = main.WHATSAPP_TEMPLATE_BODIES.get(key)
            check(body == esperado["body"], f"{key} cuerpo byte-exacto ({len(esperado['body'])} chars)")
            check(catalogo.get(key, {}).get("body") == esperado["body"],
                  f"{key} el catalogo expone el mismo cuerpo")

        print("[4] Render de variables")
        render_final = main._wa_render_template_body(
            "sibate_encuesta_final",
            {"nombre_entrevistada": "Ana", "encuestador": "Luis", "categoria": "", "hora": "hoy"},
        )
        check(render_final is not None and "Ana" in render_final and "Luis" in render_final
              and "{{" not in render_final, "sibate_encuesta_final sustituye nombre_entrevistada/encuestador")
        for key in ("recordatorio_diario_semana_19_de_octubre_", "inicio_semana_19_de_octu"):
            body = main._wa_render_template_body(
                key,
                {"dia": "3", "encuestada": "Ana", "mascota": "Luna", "censo": "1234"},
            )
            check(body is not None and "Ana" in body and "Luna" in body and "1234" in body
                  and "{{" not in body, f"{key} sustituye encuestada/mascota/censo")
            if key == "recordatorio_diario_semana_19_de_octubre_":
                check(body is not None and body.startswith("🐶 REGISTRO DIARIO – DÍA 3\n"),
                      f"{key} sustituye el dia digitado en el encabezado")


        print("[5] Conexion por estudio (masivo y 1x1)")
        study = models.Study(code="OCT19", name="Octubre 19", is_active=True)
        db.add(study)
        db.commit()
        db.refresh(study)

        main.set_study_templates(
            study.id,
            main.StudyTemplatesUpdate(template_keys=list(NUEVAS.keys())),
            db=db,
            current_user=admin,
        )
        check(main._study_template_keys(db, study.id) == list(NUEVAS.keys()),
              "el masivo acepta las 3 nuevas")

        main.set_study_single_templates(
            study.id,
            main.StudySingleTemplatesUpdate(template_keys=list(NUEVAS.keys()) + ["bono_final"]),
            db=db,
            current_user=admin,
        )
        single = main.get_study_single_templates(study.id, db=db, current_user=admin)["single_template_keys"]
        check(single == list(NUEVAS.keys()), f"el 1x1 acepta las 3 nuevas y filtra bono_final -> {single}")

        print("[6] Front: respaldo de vista previa y limpieza")
        js = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
        for key, esperado in NUEVAS.items():
            literal = '"%s": "%s",' % (key, esperado["body"].replace("\n", "\\n"))
            check(literal in js, f"WA_TEMPLATE_BODIES tiene el cuerpo de {key} (byte-exacto)")
            check(key in js, f"el front menciona {key}")
        for key in QUITADAS:
            check(key not in js, f"el front ya no menciona {key}")

        inline = _func_src(js, "waRenderInlineTemplatePreview")
        new_chat = _func_src(js, "waRenderNewChatPreview")
        final_preview = _func_src(js, "showWhatsAppTemplatePreview")
        for nombre, src in (("waRenderInlineTemplatePreview", inline),
                            ("waRenderNewChatPreview", new_chat),
                            ("showWhatsAppTemplatePreview", final_preview)):
            check(r".replace(/\{\{mascota\}\}/g" in src, f"{nombre} sustituye {{{{mascota}}}}")
            check(r".replace(/\{\{censo\}\}/g" in src, f"{nombre} sustituye {{{{censo}}}}")
            check(r".replace(/\{\{dia\}\}/g" in src, f"{nombre} sustituye {{{{dia}}}}")

        print("[7] El dia se digita y viaja en masivo y 1x1")
        backend = (RAIZ / "backend" / "main.py").read_text(encoding="utf-8")
        check('if "dia" in template_params and not dia' in backend,
              "el backend rechaza el envio sin dia")
        check('"dia": dia,' in backend, "el backend manda dia en los parametros")

        dia_list = next((ln for ln in js.splitlines() if ln.startswith("const BULK_DAY_TEMPLATES")), "")
        check(dia_list != "", "existe BULK_DAY_TEMPLATES")
        for key in ("sibate_2", "registro_diario_fatiga_6_semanas", "sibate_90mas15_dias",
                    "recordatorio_diario_semana_19_de_octubre_"):
            check("'%s'" % key in dia_list, f"{key} esta en BULK_DAY_TEMPLATES")

        for nombre in ("showWhatsAppTemplatePreview", "sendWhatsAppNewChat"):
            check("payload.dia" in _func_src(js, nombre), f"{nombre} manda payload.dia")

        html = (RAIZ / "frontend" / "call_center.html").read_text(encoding="utf-8")
        check('id="waTemplateDay"' in html, "el modal 1x1 tiene input de dia")
        check('id="waNewChatDay"' in html, "el modal de nuevo chat tiene input de dia")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} fallas.")
        sys.exit(1)
    print("\nTodo OK.")
