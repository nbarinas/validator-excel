"""Configuración Meta para el WhatsApp del CRM.

Uso:
    export WHATSAPP_ACCESS_TOKEN=<token>
    export WHATSAPP_WABA_ID=<id de la WABA del CRM (visible en Meta Business Suite)>
    python scripts/whatsapp/setup_meta.py --template --override

Opciones:
    --template   Crea (o verifica) las plantillas de saludo y alerta.
    --override   Apunta el webhook del número del CRM (1185957884609871) a la app az.
"""
import json
import os
import sys
import urllib.request
import urllib.error

WABA_ID = os.getenv("WHATSAPP_WABA_ID", "1431048488756614")
CRM_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "1185957884609871")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "az_crm_webhook_2026")
WEBHOOK_URL = os.getenv("WHATSAPP_WEBHOOK_URL", "https://validator-excel.onrender.com/whatsapp/webhook")
TEMPLATE_NAME = os.getenv("WHATSAPP_TEMPLATE_NAME", "saludo_encuesta_videollamada")
ALERT_TEMPLATE = os.getenv("WHATSAPP_ALERT_TEMPLATE", "alerta_seguimiento")
API_VERSION = "v21.0"
GRAPH = f"https://graph.facebook.com/{API_VERSION}"

TEMPLATE_BODY = (
    "🔔 Encuesta de AZ Marketing\n\n"
    "Hola {{1}}, le saluda {{2}} del equipo AZ Marketing. "
    "El día de hoy le realizaremos la encuesta en videollamada.\n\n"
    "Por favor indícanos cuándo puedes conectarte para la videollamada. Muchas gracias por tu tiempo."
)
TEMPLATE_EXAMPLE = [["Cliente", "Karol David"]]

ALERT_BODY = (
    "Tienes un mensaje sin atender de {{1}} ({{2}}), porque {{3}}. "
    "Ábrelo en el CRM para gestionarlo: {{4}}. Gracias."
)
ALERT_EXAMPLE = [
    ["Pedro Perez", "573001234567", "no tiene encuestador asignado", "https://validator-excel.onrender.com/call-center-page?chat_phone=573001234567"]
]


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


def create_template(name, body, example, footer="Equipo AZ Marketing"):
    print(f">> Verificando template existente: {name}")
    res = api("GET", f"{WABA_ID}/message_templates?name={name}")
    data = (res.get("data") or []) if "error" not in res else []
    if data:
        print(f"Template {name} ya existe. Estado: {data[0].get('status')}")
        return
    print(f">> Creando template {name}...")
    components = [{"type": "BODY", "text": body}, {"type": "FOOTER", "text": footer}]
    if example:
        components.insert(0, {"type": "BODY", "text": body, "example": {"body_text": [example]}})
    res = api("POST", f"{WABA_ID}/message_templates", {
        "name": name,
        "language": "es",
        "category": "MARKETING",
        "components": components,
    })
    if "error" in res:
        print(f"ERROR creando template {name}:", res["error"])
        sys.exit(1)
    print(f"Template {name} creado:", res)


def setup_template():
    create_template(TEMPLATE_NAME, TEMPLATE_BODY, TEMPLATE_EXAMPLE)
    create_template(ALERT_TEMPLATE, ALERT_BODY, ALERT_EXAMPLE)
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
