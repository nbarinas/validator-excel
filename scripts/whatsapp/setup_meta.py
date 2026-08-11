"""Configuración Meta para el WhatsApp del CRM.

Uso:
    export WHATSAPP_ACCESS_TOKEN=<token del bot/WABA 1431048488756614>
    python scripts/whatsapp/setup_meta.py --template --override

Opciones:
    --template   Crea (o verifica) el template de saludo.
    --override   Apunta el webhook del número 1244308882101954 (CRM) a la app az.
                 NO toca el número del bot (1007467589118202).
"""
import json
import os
import sys
import urllib.request
import urllib.error

WABA_ID = os.getenv("WHATSAPP_WABA_ID", "1431048488756614")
CRM_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "1244308882101954")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "az_crm_webhook_2026")
WEBHOOK_URL = os.getenv("WHATSAPP_WEBHOOK_URL", "https://validator-excel.onrender.com/whatsapp/webhook")
TEMPLATE_NAME = os.getenv("WHATSAPP_TEMPLATE_NAME", "saludo_encuesta_videollamada")
API_VERSION = "v21.0"
GRAPH = f"https://graph.facebook.com/{API_VERSION}"

TEMPLATE_BODY = "¡Hola {{1}}! Soy {{2}}, la persona que el día de hoy le realizará la encuesta. ¿Podemos hacer la videollamada de una vez? Muchas gracias."


def token():
    t = os.getenv("WHATSAPP_ACCESS_TOKEN")
    if not t:
        print("ERROR: exporta WHATSAPP_ACCESS_TOKEN (token del WABA 1431048488756614).")
        sys.exit(1)
    return t


def api(method, path, payload=None):
    req = urllib.request.Request(
        f"{GRAPH}/{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return {"error": json.loads(body)}
        except Exception:
            return {"error": {"raw": body}}


def setup_template():
    print(">> Verificando template existente:", TEMPLATE_NAME)
    res = api("GET", f"{WABA_ID}/message_templates?name={TEMPLATE_NAME}")
    data = (res.get("data") or []) if "error" not in res else []
    if data:
        print("Template ya existe. Estado:", data[0].get("status"))
        return
    print(">> Creando template...")
    res = api("POST", f"{WABA_ID}/message_templates", {
        "name": TEMPLATE_NAME,
        "language": "es",
        "category": "MARKETING",
        "components": [
            {"type": "BODY", "text": TEMPLATE_BODY},
            {"type": "FOOTER", "text": "Equipo AZ Marketing"},
        ],
    })
    if "error" in res:
        print("ERROR creando template:", res["error"])
        sys.exit(1)
    print("Template creado:", res)
    print("IMPORTANTE: espera la aprobación de Meta antes de enviar (minutos/horas).")


def setup_override():
    print(">> Configurando webhook del número CRM", CRM_PHONE_ID, "->", WEBHOOK_URL)
    res = api("POST", CRM_PHONE_ID, {
        "webhook_configuration": {
            "override_callback_uri": WEBHOOK_URL,
            "verify_token": VERIFY_TOKEN,
        }
    })
    if "error" in res:
        print("ERROR:", res["error"])
        sys.exit(1)
    print("Override configurado:", res)
    print("IMPORTANTE: el webhook de la app az debe estar desplegado y responder el handshake GET antes/justo al configurar esto.")


if __name__ == "__main__":
    if "--template" in sys.argv:
        setup_template()
    if "--override" in sys.argv:
        setup_override()
    if len(sys.argv) < 2 or "--help" in sys.argv:
        print(__doc__)
