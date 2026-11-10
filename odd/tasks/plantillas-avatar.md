# Plantillas de WhatsApp del estudio "Avatar" (freidoras de aire)

> **Estado:** las dos plantillas originales (`inicia_avatar`, `recordatorio_avatar`) se
> entregaron en `29ace47` y el usuario las descartó por estar mal (L4), así que se dieron de
> baja en `60ea7da`. En su lugar entró una versión corregida,
> `nuevo_recordatorio_avatar_noviembre` (L5), que es la única viva hoy: el resto de este
> documento queda como registro histórico de las que se dieron de baja.

**Feature:** agregar `inicia_avatar` y `recordatorio_avatar` (idioma `es`) al catálogo de
WhatsApp, al envío **1×1**, al **masivo** y a la **vista previa** del front.
**Rama:** `main` (misma convención que las entregas anteriores de plantillas).

## Specs

**S1.** El catálogo incluye `inicia_avatar` (idioma `es`) con las variables `{{encuestada}}`,
`{{encuestador}}` y `{{censo}}`, en ese orden de aparición, y este cuerpo verbatim:

```
Hola, {{encuestada}}! 😊 ¿Cómo estás?

Te saluda AZ MARKETING PLUS. Mi nombre es {{encuestador}}.

Te contamos que hoy, 9 de noviembre, iniciamos nuestro estudio sobre el uso de las freidoras de aire (Air Fryer). 

📅 ¿Qué debes hacer?

Desde hoy, 9 de noviembre, hasta el 9 de diciembre, debes diligenciar un formulario todos los días.

Es muy sencillo:

✅ Si utilizaste la freidora de aire, cuéntanos qué preparación realizaste y envíanos una fotografía de la preparación.

✅ Si NO la utilizaste, simplemente selecciona la opción NO LA USÉ.

🔢 Tu número de registro es: {{censo}}.

📲 Ingresa diariamente a este enlace para responder el formulario:

https://docs.google.com/forms/d/e/1FAIpQLSesadqYtsGrKwJ-un7GIGH1jTinLG_-HgYcdTjPmEiD7zRbcA/formResponse

⚠️ ¡IMPORTANTE! Recuerda diligenciarlo TODOS LOS DÍAS, incluso si no utilizaste la freidora de aire.
¡Muchas gracias por participar y por confiar en AZ MARKETING
```

**S2.** El catálogo incluye `recordatorio_avatar` (idioma `es`) con las variables
`{{entrevistado}}` y `{{censo}}`, en ese orden, y este cuerpo verbatim:

```
¡Hola, {{entrevistado}}! 😊 ¿Cómo estás?

Te saluda el equipo de AZ MARKETING PLUS.

Hoy continuamos con nuestro estudio sobre el uso de tu freidora de aire (Air Fryer). 🍟

Te recordamos que es muy importante seguir diligenciando el formulario TODOS LOS DÍAS, independientemente de si utilizaste o no tu freidora de aire.

✅ Si la usaste, cuéntanos qué preparación realizaste y adjunta una fotografía del plato o alimento preparado.

✅ Si no la usaste, simplemente selecciona la opción NO LA USÉ.

🔢 Recuerda que tu número de registro es: {{censo}}.

📲 Ingresa aquí para diligenciar la encuesta:

https://docs.google.com/forms/d/e/1FAIpQLSesadqYtsGrKwJ-un7GIGH1jTinLG_-HgYcdTjPmEiD7zRbcA/viewform

Si tienes alguna duda o inquietud, con mucho gusto estamos disponibles para ayudarte.
¡Gracias por tu compromiso y por continuar participando con
```

Los cuerpos quedan **cortados tal cual** vinieron en el pedido (S4).

**S3.** Las dos quedan habilitadas para el envío **1×1** y para el **masivo**, con **vista
previa** en el front byte-idéntica a la del backend.

**S4.** Nada que no sea cuerpo de la plantilla entra: los horarios del chat ("10:25 pm"),
"Listo, ya la llene" y "Mas tarde la lleno" quedan afuera. En cambio, los cortes del final del
texto ("…por confiar en AZ MARKETING" y "…por continuar participando con") **son parte** del
cuerpo aprobado: el usuario decidió copiarlos tal cual.

**S5.** Ninguna de las dos usa `{{dia}}`: no muestran el campo Día en el modal 1×1, en "Nuevo
chat" ni en el masivo, y el envío no lo exige ni lo manda.

## Tasks

| ID | Spec | Ruta | Evidencia |
|---|---|---|---|
| T1 | S1, S2, S3 | `backend/main.py`: `WHATSAPP_TEMPLATE_MAP`, `WHATSAPP_TEMPLATE_LABELS`, `WHATSAPP_TEMPLATE_BODIES`, `WHATSAPP_SINGLE_TEMPLATE_KEYS` | ver L3 |
| T2 | S1, S2 | `backend/main.py`: alias `entrevistado` en `param_values` de `whatsapp_send_template` y `whatsapp_send_bulk` | ver L3 |
| T3 | S1, S2, S3 | `frontend/call_center.js`: `WA_TEMPLATE_BODIES`, `BULK_TEMPLATE_VARS` y sustitución de `{{entrevistado}}` en las tres vistas previas | ver L3 |
| T4 | S3, S5 | `frontend/call_center.js`: `needsName` de "Nuevo chat" reconoce `entrevistado` | ver L3 |
| T5 | S1-S5 | `scripts/tests/check_avatar_templates.py` | ver L3 |
| T6 | S1-S5 | `scripts/tests/check_avatar_preview.js` | ver L3 |

## Log

**L1** (pedido del usuario, verbatim):

> ahora quiero cargar esta plantillas inicia_avatar · Spanish que dice Hola, {{encuestada}}! 😊 ¿Cómo estás?
>
> Te saluda AZ MARKETING PLUS. Mi nombre es {{encuestador}}.
>
> Te contamos que hoy, 9 de noviembre, iniciamos nuestro estudio sobre el uso de las freidoras de aire (Air Fryer). 
>
> 📅 ¿Qué debes hacer?
>
> Desde hoy, 9 de noviembre, hasta el 9 de diciembre, debes diligenciar un formulario todos los días.
>
> Es muy sencillo:
>
> ✅ Si utilizaste la freidora de aire, cuéntanos qué preparación realizaste y envíanos una fotografía de la preparación.
>
> ✅ Si NO la utilizaste, simplemente selecciona la opción NO LA USÉ.
>
> 🔢 Tu número de registro es: {{censo}}.
>
> 📲 Ingresa diariamente a este enlace para responder el formulario:
>
> https://docs.google.com/forms/d/e/1FAIpQLSesadqYtsGrKwJ-un7GIGH1jTinLG_-HgYcdTjPmEiD7zRbcA/formResponse
>
> ⚠️ ¡IMPORTANTE! Recuerda diligenciarlo TODOS LOS DÍAS, incluso si no utilizaste la freidora de aire.
> ¡Muchas gracias por participar y por confiar en AZ MARKETING
> 10:25 pm
> Listo, ya la llene
> Mas tarde la lleno y esta recordatorio_avatar · Spanish que dice ¡Hola, {{entrevistado}}! 😊 ¿Cómo estás?
>
> Te saluda el equipo de AZ MARKETING PLUS.
>
> Hoy continuamos con nuestro estudio sobre el uso de tu freidora de aire (Air Fryer). 🍟
>
> Te recordamos que es muy importante seguir diligenciando el formulario TODOS LOS DÍAS, independientemente de si utilizaste o no tu freidora de aire.
>
> ✅ Si la usaste, cuéntanos qué preparación realizaste y adjunta una fotografía del plato o alimento preparado.
>
> ✅ Si no la usaste, simplemente selecciona la opción NO LA USÉ.
>
> 🔢 Recuerda que tu número de registro es: {{censo}}.
>
> 📲 Ingresa aquí para diligenciar la encuesta:
>
> https://docs.google.com/forms/d/e/1FAIpQLSesadqYtsGrKwJ-un7GIGH1jTinLG_-HgYcdTjPmEiD7zRbcA/viewform
>
> Si tienes alguna duda o inquietud, con mucho gusto estamos disponibles para ayudarte.
> ¡Gracias por tu compromiso y por continuar participando con
> 10:25 pm
> Listo, ya lo llene
> Mas tarde lo lleno y su respectivo commit en local, sin al final usar ese agente que tengo instalado

**L2** (decisiones del usuario):

- **Cortes del texto:** los dos cuerpos terminan a mitad de frase ("…por confiar en AZ
  MARKETING" y "…por continuar participando con"). Se preguntó antes de escribir código y el
  usuario eligió **copiarlos tal cual**, asumiendo que así están aprobados en Meta.
- **Sin agente de verificación:** el usuario pidió expresamente no usar el subagente de
  verificación en esta entrega; la verificación se hizo inline (suite + compilación + doble
  tipeo comparado de los cuerpos).
- **Commit local**, sin push.

**L3** (implementación y verificación):

- Catálogo: `inicia_avatar` (params `encuestada`, `encuestador`, `censo`; label "Avatar — inicio
  del estudio (Air Fryer)") y `recordatorio_avatar` (params `entrevistado`, `censo`; label
  "Avatar — recordatorio diario (Air Fryer)"), ambas al final de `WHATSAPP_SINGLE_TEMPLATE_KEYS`.
- `{{entrevistado}}` no existía en el mapeo de variables: se agregó el alias al `person_name` en
  `whatsapp_send_template` y en `whatsapp_send_bulk`, y su sustitución en las tres vistas previas
  del front (`waRenderInlineTemplatePreview`, `showWhatsAppTemplatePreview`,
  `waRenderNewChatPreview`).
- `needsName` de "Nuevo chat" (`waToggleNewChatLink` y `waNewChatTemplateParams`) reconoce ahora
  `entrevistado`; sin eso, `recordatorio_avatar` no mostraba el campo Nombre.
- Detalle de whitespace: el cuerpo de `inicia_avatar` conserva el espacio final de la línea
  "…(Air Fryer). " tal como vino en L1; no cambia nada visible, pero está para que el literal sea
  el mismo que el del pedido.
- Test-first: los dos checks nuevos fallan contra `HEAD` (la plantilla y el alias no existen:
  `git show HEAD:backend/main.py | grep -c inicia_avatar` → 0, y
  `node check_avatar_preview.js <base>` → exit 1) y quedan **GREEN** con el cambio.
- Regresión cubierta: el catálogo es exactamente las 32 keys previas + las 2 nuevas, en el mismo
  orden; la lista 1×1 es la de 16 previas + las 2 nuevas al final; las dos plantillas de la
  entrega anterior conservan el largo exacto de su cuerpo; `registro_noviembre_9_2026` sigue
  exigiendo el día e `in_home_beta_385` sigue sin pedirlo.
- Envío cubierto: 1×1, masivo por estudio (`bulk_link`) y masivo por lista (`send-bulk`) mandan
  el payload exacto contra Meta simulado, incluida la sustitución de `entrevistado`; una key 1×1
  no conectada al estudio sigue rechazándose con 403 sin llamar a Meta.
- Verificación: suite `scripts/tests` **28/28 OK** (18 `.py` + 10 `.js`); `python -m py_compile backend/main.py` y
  `node --check frontend/call_center.js` OK. Los dos cuerpos se compararon byte a byte contra el
  texto de L1 (tipeado de nuevo en un script aparte, no leído del código).
- Límite conocido (heredado): en el masivo **por lista** el contacto solo trae nombre y teléfono,
  así que `censo` (y `encuestador`, que se llena con el usuario logueado) viajan según lo que
  aporta ese endpoint — no hay registro del que sacar el censo. Para eso está el masivo **por
  estudio**.
- Pendiente fuera del código: que Meta tenga las dos (`es`) aprobadas con esos `parameter_name` y
  cuerpos, y que el superusuario las conecte al estudio en "Plantillas 1×1" y "Plantillas".

**L4** (cambio de requerimiento: se dan de baja, pedido del usuario verbatim):

> revisa que tenmos dos plantillas que dicen avatar, quiero eliminarlas que estan mal

Implementación de la baja:

- Salen del catálogo: `WHATSAPP_TEMPLATE_MAP`, `WHATSAPP_TEMPLATE_LABELS`,
  `WHATSAPP_TEMPLATE_BODIES` y `WHATSAPP_SINGLE_TEMPLATE_KEYS` en `backend/main.py`, y
  `WA_TEMPLATE_BODIES` y `BULK_TEMPLATE_VARS` en `frontend/call_center.js`. El catálogo vuelve a
  **32 keys** y la lista 1×1 a **16**, exactamente como quedaron después de `5d65757`.
- Se dan de baja `scripts/tests/check_avatar_templates.py` y
  `scripts/tests/check_avatar_preview.js`: su objeto ya no existe y fallarían por diseño.
- El backend las rechaza ahora como cualquier key desconocida: `400 "Plantilla no válida"` en
  1×1 y en masivo, sin llamar a Meta.
- **Se conserva** el alias `entrevistado -> nombre de la persona` (en `whatsapp_send_template`,
  `whatsapp_send_bulk` y las tres vistas previas, más `needsName` en "Nuevo chat"): es una
  variable genérica, no una plantilla, no cambia el comportamiento de ninguna otra key y evita
  que una plantilla futura con `{{entrevistado}}` mande el campo vacío. Si se quiere afuera
  también, es una baja aparte.
- Verificación: suite `scripts/tests` **26/26 OK** (17 `.py` + 9 `.js`); `python -m py_compile backend/main.py` y
  `node --check frontend/call_center.js` OK.

**L5** (cambio de requerimiento: versión corregida del recordatorio, pedido del usuario verbatim):

> ahora agregar es nuevo_recordatorio_avatar_noviembre · Spanish que dice ¡Hola, {{encuestada}}! 😊 ¿Cómo estás?
>
> Te saluda el equipo de AZ MARKETING PLUS.
>
> Hoy continuamos con nuestro estudio sobre el uso de tu freidora de aire (Air Fryer). 🍟
>
> Te recordamos que es muy importante seguir diligenciando el formulario TODOS LOS DÍAS, independientemente de si utilizaste o no tu freidora de aire.
>
> ✅ Si la usaste, cuéntanos qué preparación realizaste y adjunta una fotografía del plato o alimento preparado.
>
> ✅ Si no la usaste, simplemente selecciona la opción NO LA USÉ.
>
> 🔢 Recuerda que tu número de registro es: {{censo}}.
>
> 📲 Ingresa aquí para diligenciar la encuesta:
> https://forms.gle/jhwUsEbh1Bf6rMG79
>
> Si tienes alguna duda o inquietud, con mucho gusto estamos disponibles para ayudarte.
>
> ¡Gracias por tu compromiso y por continuar participando con AZ Marketing Plus!
> 4:58 pm
> Listo, ya la llene
> Mas tarde la lleno

Diferencias con la plantilla que se dio de baja (L4), todas a favor de este texto:

- Nombre nuevo: `nuevo_recordatorio_avatar_noviembre`.
- Saluda con `{{encuestada}}` (la dada de baja usaba `{{entrevistado}}`), y solo lleva `censo`
  como segundo parámetro.
- Link nuevo y corto: `https://forms.gle/jhwUsEbh1Bf6rMG79`, en la línea siguiente a
  "…diligenciar la encuesta:" (sin línea en blanco en medio).
- El texto viene **completo**: cierra en "…participando con AZ Marketing Plus!", sin el corte
  que tenía la versión anterior. El ruido del chat ("4:58 pm", "Listo, ya la llene", "Mas tarde
  la lleno") queda afuera.

Implementación:

- Entra en `WHATSAPP_TEMPLATE_MAP` (name = key, `es`, params `encuestada` y `censo`), en
  `WHATSAPP_TEMPLATE_LABELS` ("Recordatorio Avatar — noviembre (Air Fryer)"), en
  `WHATSAPP_TEMPLATE_BODIES` y en `WHATSAPP_SINGLE_TEMPLATE_KEYS` (al final), más
  `WA_TEMPLATE_BODIES` y `BULK_TEMPLATE_VARS` en el front. Vista previa byte-idéntica al backend
  (795 chars).
- No usa `{{dia}}`: no está en `BULK_DAY_TEMPLATES` y el envío no lo exige ni lo manda. No hizo
  falta tocar el mapeo de variables: `encuestada` y `censo` ya se resuelven en
  `whatsapp_send_template` y en `whatsapp_send_bulk`.
- Test-first: `check_recordatorio_avatar_noviembre.py` y
  `check_recordatorio_avatar_noviembre_preview.js` fallan contra `HEAD` (la key no existe:
  `git show HEAD:backend/main.py | grep -c nuevo_recordatorio_avatar_noviembre` → 0, y el js
  contra el `call_center.js` de `HEAD` → exit 1) y quedan **GREEN** con el cambio.
- Regresión cubierta: el catálogo es las 32 keys previas + esta al final; la lista 1×1 es su
  prefijo de 16 + esta; `plantilla_inicio_semana_9_de_noviembre_sibate` (1021) y
  `registro_noviembre_9_2026` (692) conservan el largo exacto de su cuerpo;
  `registro_noviembre_9_2026` sigue exigiendo el día y `in_home_beta_385` sigue sin pedirlo.
- Envío cubierto: 1×1, masivo por estudio (`bulk_link`) y masivo por lista (`send-bulk`) con el
  payload exacto contra Meta simulado; una key 1×1 no conectada al estudio sigue rechazándose
  con 403 sin llamar a Meta.
- Verificación: suite `scripts/tests` **28/28 OK** (18 `.py` + 10 `.js`); `python -m py_compile backend/main.py` y
  `node --check frontend/call_center.js` OK. El cuerpo se comparó byte a byte contra el texto de
  L5 (tipeado de nuevo en un script aparte, no leído del código).
- Pendiente fuera del código: que Meta tenga la plantilla (`es`) aprobada con esos
  `parameter_name` y que el superusuario la conecte al estudio en "Plantillas 1×1" y
  "Plantillas".

**L6** (cambio de requerimiento: sale la que quedó en revisión, entra `el_azul`; pedido del usuario verbatim):

> tuve que crear otra plantilla porque esta que acabamos de crear quedo en revision elimina esa y agrega esta el_azul · SpanishSaludos
> ¡Hola, {{encuestada}}! 😊 ¿Cómo estás?
>
> Te saluda el equipo de AZ MARKETING PLUS.
>
> Hoy continuamos con nuestro estudio sobre el uso de tu freidora de aire (Air Fryer). 🍟
>
> Te recordamos que es muy importante seguir diligenciando el formulario TODOS LOS DÍAS, independientemente de si utilizaste o no tu freidora de aire.
>
> ✅ Si la usaste, cuéntanos qué preparación realizaste y adjunta una fotografía del plato o alimento preparado.
>
> ✅ Si no la usaste, simplemente selecciona la opción NO LA USÉ.
>
> 🔢 Recuerda que tu número de registro es: {{censo}}.
>
> 📲 Ingresa aquí para diligenciar la encuesta:
> https://forms.gle/jhwUsEbh1Bf6rMG79
>
> Si tienes alguna duda o inquietud, con mucho gusto estamos disponibles para ayudarte.
> ¡Gracias por tu compromiso y por continuar participando con
> 7:02 pm
> Listo, ya lo llene
> Mas tarde lo lleno y has el commit

Decisiones del usuario sobre este pegado (se preguntaron antes de escribir código):

- **"Saludos" es la primera línea del cuerpo**, seguida de "¡Hola, {{encuestada}}! 😊 ¿Cómo estás?"
  en la línea siguiente y sin línea en blanco entre las dos.
- **El cierre va tal cual**, cortado en "…por continuar participando con", igual que se eligió
  para las plantillas avatar que se dieron de baja (L2). Ojo: esta vez tampoco hay línea en
  blanco entre "…ayudarte." y "¡Gracias…".

Implementación:

- `nuevo_recordatorio_avatar_noviembre` **sale** del catálogo (quedó en revisión en Meta: ofrecerla
  solo generaría envíos con 132001) y `el_azul` entra en su lugar, en los mismos seis puntos:
  `WHATSAPP_TEMPLATE_MAP`, `WHATSAPP_TEMPLATE_LABELS` ("Air Fryer — recordatorio diario (azul)"),
  `WHATSAPP_TEMPLATE_BODIES` y `WHATSAPP_SINGLE_TEMPLATE_KEYS` del backend, más
  `WA_TEMPLATE_BODIES` y `BULK_TEMPLATE_VARS` del front. Catálogo: 33 keys; lista 1×1: 17.
- Mismos parámetros que la anterior: `encuestada` y `censo` (sin `dia`), así que no hizo falta
  tocar el mapeo de variables.
- Los dos checks se renombran y se reapuntan: `check_el_azul.py` y `check_el_azul_preview.js`
  (antes `check_recordatorio_avatar_noviembre*`, cuyo objeto ya no existe).
- Incidencia durante la implementación: el primer intento de escribir el cuerpo pasó el texto por
  un heredoc del shell y perdió un nivel de escapes, dejando saltos de línea reales dentro de la
  cadena; el script de arreglo además ubicó la primera entrada `el_azul` (la de `LABELS`) y borró
  el tramo intermedio (`SINGLE_KEYS`, `WHATSAPP_WINDOW_HOURS` y la cabecera de
  `WHATSAPP_TEMPLATE_BODIES`). Se restauraron los dos archivos desde `1525233`
  (`git checkout HEAD -- backend/main.py frontend/call_center.js`) y se rehizo con ediciones
  exactas. `py_compile` y `node --check` lo detectaron y hoy los dos pasan.
- Test-first: los dos checks fallan contra `HEAD` (la key no existe:
  `git show HEAD:backend/main.py | grep -c '"el_azul": {'` → 0, y el js contra el `call_center.js`
  de `HEAD` → exit 1) y quedan **GREEN** con el cambio.
- Verificación: suite `scripts/tests` **28/28 OK** (18 `.py` + 10 `.js`); `python -m py_compile backend/main.py` y
  `node --check frontend/call_center.js` OK. El cuerpo se comparó byte a byte contra el pedido de
  L6 (20 líneas, 783 chars, primera "Saludos", última "…participando con").
- Pendiente fuera del código: que Meta apruebe `el_azul` (`es`) con esos `parameter_name` y que el
  superusuario la conecte al estudio en "Plantillas 1×1" y "Plantillas".
