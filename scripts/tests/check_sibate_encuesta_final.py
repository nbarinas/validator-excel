#!/usr/bin/env python3
"""Verifica que `sibate_encuesta_final` vuelva al catalogo (1x1 y masivo).

Pedido del usuario (verbatim): *"sibate_encuesta_final · Spanish ... esta ya en
plantillas pero esta desactivada, quiero que aparezca de nuevo en 1x1 y masivos"*.

La plantilla estaba en el catalogo y se retiro en bb51a59 (set del 19 de octubre).
Se restituye con la misma configuracion y el mismo cuerpo verbatim aprobado en Meta.

Comprueba contra el codigo real:
  1. WHATSAPP_TEMPLATE_MAP/MAP+lable+cuerpo: name `sibate_encuesta_final`, idioma `es`,
     parametros nombre_entrevistada/encuestador y el cuerpo byte-exacto.
  2. El catalogo (/whatsapp/templates) la publica en 1x1 (single_eligible) y en el
     catalogo completo del masivo.
  3. El render del texto libre sustituye nombre_entrevistada y encuestador.
  4. frontend/call_center.js guarda el mismo literal (vista previa).
  5. Las pruebas de visibilidad ya no la usan como "plantilla retirada" (ese rol pasa
     a una key que sigue retirada).

Uso:    python scripts/tests/check_sibate_encuesta_final.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

import backend.main as main  # noqa: E402

KEY = "sibate_encuesta_final"
LABEL = "Sibate — encuesta final (videollamada)"
PARAMS = ["nombre_entrevistada", "encuestador"]

# --- Cuerpo aprobado (verbatim del pedido) ---
CUERPO = (
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

FALLAS = []


def check(cond, msg):
    if cond:
        print(f"  OK    {msg}")
    else:
        print(f"  FALLA {msg}")
        FALLAS.append(msg)


class _SuperUser:
    role = "superuser"


def correr():
    print("[1] La plantilla vuelve al backend con su configuracion")
    cfg = main.WHATSAPP_TEMPLATE_MAP.get(KEY)
    check(cfg is not None, f"{KEY} esta en WHATSAPP_TEMPLATE_MAP")
    if cfg:
        check(cfg.get("name") == "sibate_encuesta_final", f"{KEY} name: {cfg.get('name')}")
        check(cfg.get("language") == "es", f"{KEY} language: {cfg.get('language')}")
        check(cfg.get("params") == PARAMS, f"{KEY} params: {cfg.get('params')}")
    check(main.WHATSAPP_TEMPLATE_LABELS.get(KEY) == LABEL,
          f"{KEY} label: {main.WHATSAPP_TEMPLATE_LABELS.get(KEY)}")
    real = main.WHATSAPP_TEMPLATE_BODIES.get(KEY)
    check(real == CUERPO, f"{KEY} body byte-exacto en WHATSAPP_TEMPLATE_BODIES")

    print("[2] El catalogo la publica en 1x1 y en el masivo")
    catalogo = main.whatsapp_templates_catalog(db=None, current_user=_SuperUser())
    item = next((t for t in catalogo if t["key"] == KEY), None)
    check(item is not None, f"{KEY} esta en /whatsapp/templates")
    if item:
        check(item["body"] == CUERPO, f"{KEY} body del catalogo byte-exacto")
        check(item["name"] == "sibate_encuesta_final", f"{KEY} name del payload a Meta: {item['name']}")
        check(item["language"] == "es", f"{KEY} language: {item['language']}")
        check(item["params"] == PARAMS, f"{KEY} params: {item['params']}")
        check(item["label"] == LABEL, f"{KEY} label del catalogo: {item['label']}")
        check(item["single_eligible"] is True, f"{KEY} habilitada para 1x1 (single_eligible)")
    check(KEY in main.WHATSAPP_SINGLE_TEMPLATE_KEYS,
          f"{KEY} esta en WHATSAPP_SINGLE_TEMPLATE_KEYS (boton Plantillas 1x1)")
    claves_masivo = [t["key"] for t in catalogo]
    check(set(claves_masivo) == set(main.WHATSAPP_TEMPLATE_MAP),
          "el masivo conserva todo el catalogo")
    check(KEY in claves_masivo, f"{KEY} aparece en el catalogo del masivo")

    print("[3] El render del texto libre sustituye las variables")
    render = main._wa_render_template_body(
        KEY, {"nombre_entrevistada": "Ana", "encuestador": "Luis"}
    )
    check(render is not None, f"{KEY} se puede renderizar como texto libre")
    check("{{" not in (render or ""), f"{KEY} render sin variables pendientes")
    check("señora Ana" in (render or ""), f"{KEY} render sustituye nombre_entrevistada")
    check("La saluda Luis" in (render or ""), f"{KEY} render sustituye encuestador")

    print("[4] El front guarda el mismo literal (vista previa)")
    js = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
    match = re.search(r'\n\s*"%s":\s*("(?:[^"\\]|\\.)*")\s*,' % KEY, js)
    front_body = json.loads(match.group(1)) if match else None
    check(front_body is not None, f"WA_TEMPLATE_BODIES define {KEY} en el front")
    check(front_body == CUERPO, f"{KEY} del front coincide byte-exacto con el backend")

    print("[5] Las pruebas de visibilidad ya no la tratan como retirada")
    for nombre in ("check_template_visibility.py", "check_template_visibility_edges.py"):
        fuente = (RAIZ / "scripts" / "tests" / nombre).read_text(encoding="utf-8")
        m = re.search(r'^RETIRADA = "([^"]+)"', fuente, re.MULTILINE)
        clave = m.group(1) if m else None
        check(clave is not None, f"{nombre} define RETIRADA")
        check(clave != KEY, f"{nombre} no usa {KEY} como plantilla retirada (usa {clave})")
        check(clave not in main.WHATSAPP_TEMPLATE_MAP,
              f"{clave} sigue retirada de WHATSAPP_TEMPLATE_MAP ({nombre})")


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} fallas.")
        sys.exit(1)
    print("\nTodo OK.")
