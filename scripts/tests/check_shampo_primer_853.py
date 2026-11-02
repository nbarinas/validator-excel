#!/usr/bin/env python3
"""Verifica la plantilla `shampo_primer` alineada al cuerpo aprobado en Meta (producto 853).

Pedido del usuario (verbatim): la plantilla shampo_primer (Spanish) ahora dice
"... Hace 10 días le entregamos el producto 853  y el día de hoy tiene programada
una videollamada a las {{hora}}." y debe aparecer en el envio 1x1 y en el masivo.

Comprueba contra el codigo real:
  1. WHATSAPP_TEMPLATE_BODIES['shampo_primer'] es byte-exacto al texto aprobado
     (conserva el doble espacio de "853  y").
  2. El catalogo (/whatsapp/templates) publica ese mismo cuerpo, con
     single_eligible=True (1x1) y presente en el catalogo completo del masivo.
  3. El render del texto libre sustituye encuestada/encuestador/hora.
  4. frontend/call_center.js guarda el mismo literal como respaldo de la vista
     previa (paridad backend/front, sin el texto viejo de "15 dias").

Uso:    python scripts/tests/check_shampo_primer_853.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

import backend.main as main  # noqa: E402

KEY = "shampo_primer"

# --- Cuerpo esperado (verbatim del pedido, con el doble espacio de "853  y") ---
CUERPO = (
    "Az-Marketing\n"
    "Buenos días, señora {{encuestada}}, ¿cómo está? Mucho gusto.\n"
    "\n"
    "Mi nombre es {{encuestador}}, trabajo para AZ Marketing Plus.\n"
    "\n"
    "El motivo de mi mensaje es que usted nos está colaborando en un estudio de "
    "shampoo. Hace 10 días le entregamos el producto 853  y el día de hoy tiene "
    "programada una videollamada a las {{hora}}.\n"
    "\n"
    "Quería confirmar si está disponible a esa hora o si podemos realizar la "
    "videollamada en este momento.\n"
    "\n"
    "Quedo atento a su pronta respuesta.\n"
    "Muchas gracias. ¡Feliz día!"
)

# Cuerpo anterior: 15 dias y sin codigo de producto.
VIEJO = (
    "Az-Marketing\n"
    "Buenos días, señora {{encuestada}}, ¿cómo está? Mucho gusto.\n"
    "\n"
    "Mi nombre es {{encuestador}}, trabajo para AZ Marketing Plus.\n"
    "\n"
    "El motivo de mi mensaje es que usted nos está colaborando en un estudio de "
    "shampoo. Hace 15 días le entregamos el producto y el día de hoy tiene "
    "programada una videollamada a las {{hora}}.\n"
    "\n"
    "Quería confirmar si está disponible a esa hora o si podemos realizar la "
    "videollamada en este momento.\n"
    "\n"
    "Quedo atento a su pronta respuesta.\n"
    "Muchas gracias. ¡Feliz día!"
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
    print("[1] El cuerpo del backend es el aprobado en Meta")
    real = main.WHATSAPP_TEMPLATE_BODIES.get(KEY)
    check(real == CUERPO, f"{KEY} byte-exacto en WHATSAPP_TEMPLATE_BODIES")
    check(VIEJO not in (real or ""), f"{KEY} ya no repite el cuerpo viejo (15 días)")
    check("Hace 15 días" not in (real or ""), f"{KEY} ya no dice 'Hace 15 días'")
    check("producto 853  y el día" in (real or ""),
          f"{KEY} menciona 'producto 853  y el día' (doble espacio verbatim)")

    print("[2] El catalogo publica ese cuerpo en 1x1 y en el masivo")
    catalogo = main.whatsapp_templates_catalog(db=None, current_user=_SuperUser())
    item = next((t for t in catalogo if t["key"] == KEY), None)
    check(item is not None, f"{KEY} esta en /whatsapp/templates")
    if item:
        check(item["body"] == CUERPO, f"{KEY} body del catalogo byte-exacto")
        check(item["name"] == "shampo_primer", f"{KEY} name del payload a Meta: {item['name']}")
        check(item["language"] == "es", f"{KEY} language: {item['language']}")
        check(item["params"] == ["encuestada", "encuestador", "hora"],
              f"{KEY} params: {item['params']}")
        check(item["single_eligible"] is True, f"{KEY} habilitada para 1x1 (single_eligible)")
        check(item["label"] == "Shampoo — primer contacto", f"{KEY} label: {item['label']}")
    check(KEY in main.WHATSAPP_SINGLE_TEMPLATE_KEYS,
          f"{KEY} esta en WHATSAPP_SINGLE_TEMPLATE_KEYS (boton Plantillas 1x1)")
    claves_masivo = [t["key"] for t in catalogo]
    check(set(claves_masivo) == set(main.WHATSAPP_TEMPLATE_MAP),
          "el masivo conserva todo el catalogo")
    check(KEY in claves_masivo, f"{KEY} aparece en el catalogo del masivo")

    print("[3] El render del texto libre sustituye las variables")
    render = main._wa_render_template_body(
        KEY, {"encuestada": "María", "encuestador": "Juan", "hora": "3:00 p.m."}
    )
    check(render is not None, f"{KEY} se puede renderizar como texto libre")
    check("{{" not in (render or ""), f"{KEY} render sin variables pendientes")
    check("señora María" in (render or ""), f"{KEY} render sustituye encuestada")
    check("Mi nombre es Juan" in (render or ""), f"{KEY} render sustituye encuestador")
    check("a las 3:00 p.m." in (render or ""), f"{KEY} render sustituye hora")

    print("[4] El front guarda el mismo literal (respaldo de la vista previa)")
    js = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
    match = re.search(r'\n\s*"%s":\s*("(?:[^"\\]|\\.)*")\s*,' % KEY, js)
    front_body = json.loads(match.group(1)) if match else None
    check(front_body is not None, f"WA_TEMPLATE_BODIES define {KEY} en el front")
    check(front_body == CUERPO, f"{KEY} del front coincide byte-exacto con el backend")
    check(VIEJO not in (front_body or ""), f"{KEY} del front ya no repite el cuerpo viejo (15 días)")
    check("producto 729" not in (front_body or ""), f"{KEY} del front ya no menciona el producto 729")


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} fallas.")
        sys.exit(1)
    print("\nTodo OK.")
