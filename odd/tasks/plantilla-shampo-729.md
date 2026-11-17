# Plantilla `shampo_729` (quinta videollamada del shampoo 729)

**Feature:** agregar `shampo_729` (idioma `es`) al catálogo de WhatsApp, al envío **1×1**, al
**masivo** y a la **vista previa** del front.
**Rama:** `main` (misma convención que las entregas anteriores de plantillas).

## Specs

**S1.** El catálogo incluye `shampo_729` (nombre de Meta idéntico, idioma `es`) con las
variables `{{entrevistada}}`, `{{encuestador}}` y `{{hora_agendada}}`, en ese orden de
aparición, y este cuerpo verbatim:

```
¡Muy buenos días, señora {{entrevistada}}! 😊

La saluda {{encuestador}}, de AZ Marketing Plus.

Le escribo para recordarle que hoy tiene programada la quinta videollamada del estudio de shampoo 729, a las {{hora_agendada}}.
.

¿Podemos realizar la videollamada en este momento a mas tarde?
```

**S2.** Queda habilitada para el envío **1×1** y para el **masivo**, con **vista previa** en el
front byte-idéntica a la del backend.

**S3.** `{{hora_agendada}}` se resuelve con `collection_time` del registro, igual que en
`729_sin_bono` y `fatiga_729_r3`.

**S4.** Nada que no sea cuerpo de la plantilla entra: la hora del chat ("4:25 pm") y los
botones de respuesta rápida ("En este momento", "Mas tarde") quedan afuera, como se hizo en
`729_sin_bono` y `853_sin_bono`.

**S5.** No usa `{{dia}}`: no muestra el campo Día y el envío no lo exige ni lo manda.

**S6.** El cuerpo se conserva verbatim, incluido el punto suelto de la línea siguiente a
`{{hora_agendada}}`. Si el texto aprobado en Meta no lo tiene, se corrige el cuerpo acá.

## Tasks

| ID | Spec | Ruta | Evidencia |
|---|---|---|---|
| T1 | S1, S2, S3, S5 | `backend/main.py`: `WHATSAPP_TEMPLATE_MAP`, `WHATSAPP_TEMPLATE_LABELS`, `WHATSAPP_TEMPLATE_BODIES`, `WHATSAPP_SINGLE_TEMPLATE_KEYS` | ver L2 |
| T2 | S1, S2 | `frontend/call_center.js`: `WA_TEMPLATE_BODIES` y `BULK_TEMPLATE_VARS` | ver L2 |
| T3 | S1-S6 | `scripts/tests/check_shampo_729.py` | ver L2 |
| T4 | S1-S6 | `scripts/tests/check_shampo_729_preview.js` | ver L2 |
| T5 | S1-S6 | `scripts/tests/run_checks.py`: clasificar los dos checks nuevos en el area `templates` | ver L2 |

## Log

**L1** (pedido del usuario, verbatim):

> quiero agregar la plantilla shampo_729 · Spanish que dice ¡Muy buenos días, señora {{entrevistada}}! 😊
>
> La saluda {{encuestador}}, de AZ Marketing Plus.
>
> Le escribo para recordarle que hoy tiene programada la quinta videollamada del estudio de shampoo 729, a las {{hora_agendada}}.
> .
>
> ¿Podemos realizar la videollamada en este momento a mas tarde?
> 4:25 pm
> En este momento
> Mas tarde en 1x1 masivo y previsualizacion me puedes ayudar y haciendo el commit al termianr

**L2** (implementación y verificación):

- Catálogo: `shampo_729` (params `entrevistada`, `encuestador`, `hora_agendada`; label "Shampoo
  729 — quinta videollamada"), al final de `WHATSAPP_SINGLE_TEMPLATE_KEYS`. Catálogo en **35
  keys** y lista 1×1 en **19**.
- El key y el `name` de Meta son `shampo_729` tal como los pidió el usuario (con "shampo", sin
  doble o), distinto de la hermana `729_sin_bono` (cuarta videollamada).
- Los tres parámetros ya se resuelven: `entrevistada` y `encuestador` en
  `whatsapp_send_template` / `whatsapp_send_bulk`, y `hora_agendada` desde `collection_time`
  del registro (mismo camino que `729_sin_bono`). Las tres vistas previas del front
  (`waRenderInlineTemplatePreview`, `waRenderNewChatPreview`, `waRenderNewChatPreview` vía
  "Nuevo chat") sustituyen los tres placeholders; `hora_agendada` ya está en `needsHora`.
- Test-first: `check_shampo_729.py` y `check_shampo_729_preview.js` fallan contra `HEAD` (la key
  no existe: el py da 16 fallas y el js aborta al no encontrar el cuerpo) y quedan **GREEN** con
  el cambio. El cuerpo se tipeó de nuevo en el check y se comparó byte a byte contra L1 (289
  chars).
- Regresión: los checks verifican invariantes estructurales del catálogo (toda key con cuerpo o
  1×1 existe en `WHATSAPP_TEMPLATE_MAP`, toda key tiene etiqueta, la nueva queda después de
  `853_sin_bono` en la lista 1×1) y que las hermanas de la familia 729/853 (`729_sin_bono`,
  `fatiga_729_r3`, `primera_recogida_853_`, `853_sin_bono`) conservan sus parámetros y siguen en
  el catálogo.
- `check_853_sin_bono.py` pasa su aserción de lista 1×1 de "es la última" a presencia + orden
  después de `el_azul`: fijar la última posición se rompe en cada entrega nueva, igual que ya se
  había corregido `check_el_azul.py` en la entrega anterior.
- Envío cubierto: 1×1 y masivo por estudio mandan los 3 parámetros con la hora del registro
  ("5:00 pm") contra Meta simulado; una key 1×1 no conectada al estudio sigue rechazándose con
  403 sin llamar a Meta.
- Verificación: suite `scripts/tests` **32/32 OK** (ver L3); `python -m py_compile
  backend/main.py` y `node --check frontend/call_center.js` OK.
- Pendiente fuera del código: que Meta tenga `shampo_729` (`es`) aprobada con esos
  `parameter_name` y que el superusuario la conecte al estudio en "Plantillas 1×1" y
  "Plantillas".

**L3** (verificación final):

- Suite `scripts/tests` **32/32 OK** (20 `.py` + 12 `.js`) en 68 s, con los dos checks nuevos
  clasificados en el área `templates` de `run_checks.py`.
- `python -m py_compile backend/main.py` y `node --check frontend/call_center.js` OK.
- Cuerpo: 289 chars, byte-idéntico en `WHATSAPP_TEMPLATE_BODIES`, en el catálogo y en el
  respaldo del front; el render conserva `a las 5:00 pm.\n.` (punto suelto incluido).
- Payload 1×1 y masivo por estudio: `entrevistada=Maria`, `encuestador=Ana Check`,
  `hora_agendada=5:00 pm` (tomada de `collection_time`).
- Catálogo: 35 keys, 35 etiquetas, 30 cuerpos, lista 1×1 en 19.
- Hallazgo de regresión: la primera corrida completa dio **31/32** porque
  `check_853_sin_bono.py` fijaba "es la última de la lista 1×1". Se corrigió a presencia + orden
  después de `el_azul` y la suite volvió a **32/32**; el check nuevo nace ya con la aserción
  estable (después de `853_sin_bono`).
