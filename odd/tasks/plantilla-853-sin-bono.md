# Plantilla `853_sin_bono` (segunda videollamada del shampoo 853)

**Feature:** agregar `853_sin_bono` (idioma `es`) al catálogo de WhatsApp, al envío **1×1**, al
**masivo** y a la **vista previa** del front.
**Rama:** `main` (misma convención que las entregas anteriores de plantillas).

## Specs

**S1.** El catálogo incluye `853_sin_bono` (nombre de Meta idéntico, idioma `es`) con las
variables `{{encuestada}}`, `{{encuestador}}` y `{{hora}}`, en ese orden de aparición, y este
cuerpo verbatim:

```
Muy buenos días, señora {{encuestada}}! 😊

La saluda {{encuestador}}, de AZ Marketing Plus.

Le escribo porque hoy tiene programada la segunda videollamada del estudio de shampoo 853, a la(s) {{hora}} .

¿Sería posible realizarla en este momento o prefiere que la contactemos más tarde?

Quedo atento a su respuesta. ¡Muchas gracias y feliz día! 🌷
```

**S2.** Queda habilitada para el envío **1×1** y para el **masivo**, con **vista previa** en el
front byte-idéntica a la del backend.

**S3.** `{{hora}}` se resuelve con `collection_time` del registro, igual que en `primera_recogida_853_`
y `fatiga_729_r3`.

**S4.** Nada que no sea cuerpo de la plantilla entra: la hora del chat ("12:25 pm") y los botones
de respuesta rápida ("Listo, de una vez", "Mas tarde, porfa") quedan afuera, como se hizo en
`729_sin_bono`.

**S5.** No usa `{{dia}}`: no muestra el campo Día y el envío no lo exige ni lo manda.

## Tasks

| ID | Spec | Ruta | Evidencia |
|---|---|---|---|
| T1 | S1, S2, S3, S5 | `backend/main.py`: `WHATSAPP_TEMPLATE_MAP`, `WHATSAPP_TEMPLATE_LABELS`, `WHATSAPP_TEMPLATE_BODIES`, `WHATSAPP_SINGLE_TEMPLATE_KEYS` | ver L2 |
| T2 | S1, S2 | `frontend/call_center.js`: `WA_TEMPLATE_BODIES` y `BULK_TEMPLATE_VARS` | ver L2 |
| T3 | S1-S5 | `scripts/tests/check_853_sin_bono.py` | ver L2 |
| T4 | S1-S5 | `scripts/tests/check_853_sin_bono_preview.js` | ver L2 |

## Log

**L1** (pedido del usuario, verbatim):

> ahora quiero agregrar la plantilla 853_sin_bono · Spanish que dice Muy buenos días, señora {{encuestada}}! 😊
>
> La saluda {{encuestador}}, de AZ Marketing Plus.
>
> Le escribo porque hoy tiene programada la segunda videollamada del estudio de shampoo 853, a la(s) {{hora}} .
>
> ¿Sería posible realizarla en este momento o prefiere que la contactemos más tarde?
>
> Quedo atento a su respuesta. ¡Muchas gracias y feliz día! 🌷
> 12:25 pm
> Listo, de una vez
> Mas tarde, porfa

**L2** (implementación y verificación):

- Catálogo: `853_sin_bono` (params `encuestada`, `encuestador`, `hora`; label "Shampoo 853 —
  segunda videollamada (sin bono)"), al final de `WHATSAPP_SINGLE_TEMPLATE_KEYS`. Catálogo en
  **34 keys** y lista 1×1 en **18**.
- El cuerpo conserva el detalle verbatim de "a la(s) {{hora}} ." (espacio antes del punto) y el
  cierre completo "¡Muchas gracias y feliz día! 🌷".
- No hizo falta tocar el mapeo de variables: `encuestada`, `encuestador` y `hora` ya se resuelven
  en `whatsapp_send_template` y en `whatsapp_send_bulk`, y las vistas previas del front ya
  sustituyen las tres.
- Test-first: `check_853_sin_bono.py` y `check_853_sin_bono_preview.js` fallan contra `HEAD` (la
  key no existe: el js contra el `call_center.js` de `HEAD` → exit 1) y quedan **GREEN** con el
  cambio.
- Regresión: en vez de fijar otra vez el catálogo completo por lista (que se rompe en cada
  entrega), el check verifica invariantes estructurales — toda key con cuerpo o 1×1 existe en
  `WHATSAPP_TEMPLATE_MAP`, toda key tiene etiqueta, la nueva queda al final de la lista 1×1 — y
  que las hermanas de la familia 853/729 (`729_sin_bono`, `primera_recogida_853_`,
  `fatiga_729_r3`) conservan sus parámetros y siguen en el catálogo.
- Envío cubierto: 1×1 y masivo por estudio mandan los 3 parámetros con la hora del registro
  ("5:00 pm") contra Meta simulado; una key 1×1 no conectada al estudio sigue rechazándose con
  403 sin llamar a Meta.
- Verificación: suite `scripts/tests` **30/30 OK** (19 `.py` + 11 `.js`); `python -m py_compile
  backend/main.py` y `node --check frontend/call_center.js` OK. El cuerpo se comparó byte a byte
  contra el texto de L1, tipeado de nuevo en un script aparte.
- Pendiente fuera del código: que Meta tenga `853_sin_bono` (`es`) aprobada con esos
  `parameter_name` y que el superusuario la conecte al estudio en "Plantillas 1×1" y
  "Plantillas".
