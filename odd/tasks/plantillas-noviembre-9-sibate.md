# Plantillas de WhatsApp del 9 de noviembre (Sibate)

**Feature:** agregar `plantilla_inicio_semana_9_de_noviembre_sibate` y
`registro_noviembre_9_2026` (idioma `es`) al catálogo de WhatsApp, al envío **1×1**, al
**masivo** y a la **vista previa** del front.
**Rama:** `main` (misma convención que las entregas anteriores de plantillas).

## Specs

**S1.** El catálogo incluye `plantilla_inicio_semana_9_de_noviembre_sibate` (nombre de Meta
idéntico, idioma `es`, con el prefijo `plantilla_`) con las variables `{{entrevistada}}`,
`{{mascota}}` y `{{censo}}`, en ese orden de aparición, y este cuerpo verbatim:

```
ENCUESTA DIARIA – 7 DÍAS
¡Hola, {{entrevistada}}👋
Te saluda el equipo de AZ Marketing Plus.

Hoy iniciamos esta dinámica, que tendrá una duración de 7 semanas.

Durante los próximos 7 días, deberás registrar diariamente el tiempo que tu perrito  {{mascota}}  tarda en consumir el concentrado o alimento que habitualmente le das.

⏱️ ¿Qué debes hacer?

Toma el tiempo desde el momento en que le sirves el alimento hasta que termina de comer.
Observa atentamente su comportamiento al momento de alimentarse.
Registra si comienza a comer inmediatamente o si primero olfatea el alimento antes de consumirlo.

🍽️ Realiza esta actividad en una sola comida al día: desayuno, almuerzo o cena.

📌 Importante: durante estos 7 días, procura mantener el mismo alimento y el mismo horario de alimentación, para garantizar un seguimiento consistente.

📝 Recuerda diligenciar una encuesta cada día durante los 7 días.

Tu código de registro es: {{censo}}

🔗 INGRESA AQUÍ A LA ENCUESTA:
https://forms.gle/cedqXEt1zPQXZcRt6
Muchas gracias
```

**S2.** El catálogo incluye `registro_noviembre_9_2026` (idioma `es`; en Meta figura como
"Spanish (SPA)", que es el locale `es`) con las variables `{{dia}}`, `{{encuestada}}`,
`{{mascotica}}` y `{{censo}}`, en ese orden, y este cuerpo verbatim:

```
REGISTRO DIARIO
DÍA {{dia}}/7

¡Hola, {{encuestada}}! 👋
Te saluda el equipo de AZ Marketing Plus.

Recuerda realizar hoy el registro del consumo de concentrado o purina de tu perro {{mascotica}}.

📌 Recuerda:

🍽️ Realiza el registro en una sola comida al día y procura mantener la misma comida y el mismo horario durante toda la semana.
⏱️ Mide el tiempo desde que sirves el alimento hasta que tu perro termina de comer.
👀 Observa atentamente su comportamiento durante la alimentación y registra tus observaciones en la encuesta.
📝 Recuerda realizar un registro diario durante los 7 días.

Tu código de registro es: {{censo}}

🔗 INGRESA AQUÍ A LA ENCUESTA:
https://forms.gle/HAtyTHjKxLYmtinz5
```

`{{mascotica}}` es literal, con t: es el nombre del parámetro que quedó aprobado en Meta, no un
typo nuestro (L4), y el backend lo resuelve con el nombre del perro del registro. El primer
nombre propuesto para esta plantilla, `recordatorio_semana_9_de_noviembre_sibate`, **no** queda
en el catálogo: Meta lo rechazó (L4).

**S3.** Las dos quedan habilitadas para el envío **1×1** (botón "Plantillas 1×1") y para el
**masivo** (el masivo sigue ofreciendo todo el catálogo), con **vista previa** en el front
byte-idéntica a la del backend.

**S4.** El `{{dia}}` de la de registro se digita antes de enviar: el campo aparece en el
modal 1×1, en "Nuevo chat" y en el masivo por estudio, y el backend rechaza el envío sin día con
`400 "Indica el día del registro antes de enviar"`, sin llamar a Meta ni guardar el mensaje. La
de inicio no usa `dia` y no muestra ese campo.

**S5.** Todo lo que no es cuerpo de la plantilla en el pedido queda afuera: los horarios del
chat ("6:17 pm", "6:18 pm"), "Listo, ya lo llene", "Ahora lo lleno" y la nota "Mas tarde la lleni
este el dia se digita antes de enviar" (esta última es la regla de S4, no texto del cuerpo).

## Tasks

| ID | Spec | Ruta | Evidencia |
|---|---|---|---|
| T1 | S1, S2, S3 | `backend/main.py`: `WHATSAPP_TEMPLATE_MAP`, `WHATSAPP_TEMPLATE_LABELS`, `WHATSAPP_TEMPLATE_BODIES`, `WHATSAPP_SINGLE_TEMPLATE_KEYS` | ver L3 |
| T2 | S1, S2, S3 | `frontend/call_center.js`: `WA_TEMPLATE_BODIES` (vista previa) | ver L3 |
| T3 | S4 | `frontend/call_center.js`: `BULK_DAY_TEMPLATES` (campo día en el masivo) y `BULK_TEMPLATE_VARS` | ver L3 |
| T4 | S1-S5 | `scripts/tests/check_noviembre_9_sibate_templates.py` | ver L3 |
| T5 | S1-S5 | `scripts/tests/check_noviembre_9_sibate_preview.js` | ver L3 |

No hizo falta tocar el mapeo de variables: `entrevistada`, `mascota`, `censo` y `dia` ya se
resuelven en `whatsapp_send_template` y en `whatsapp_send_bulk`, y las tres vistas previas del
front ya sustituyen `{{entrevistada}}`, `{{mascota}}`, `{{censo}}` y `{{dia}}`.

## Log

**L1** (pedido del usuario, verbatim):

> quiero agregar las plantillas de 1x1, masivo y en previu plantilla_inicio_semana_9_de_noviembre_sibate · Spanish que dice ENCUESTA DIARIA – 7 DÍAS
> ¡Hola, {{entrevistada}}👋
> Te saluda el equipo de AZ Marketing Plus.
>
> Hoy iniciamos esta dinámica, que tendrá una duración de 7 semanas.
>
> Durante los próximos 7 días, deberás registrar diariamente el tiempo que tu perrito  {{mascota}}  tarda en consumir el concentrado o alimento que habitualmente le das.
>
> ⏱️ ¿Qué debes hacer?
>
> Toma el tiempo desde el momento en que le sirves el alimento hasta que termina de comer.
> Observa atentamente su comportamiento al momento de alimentarse.
> Registra si comienza a comer inmediatamente o si primero olfatea el alimento antes de consumirlo.
>
> 🍽️ Realiza esta actividad en una sola comida al día: desayuno, almuerzo o cena.
>
> 📌 Importante: durante estos 7 días, procura mantener el mismo alimento y el mismo horario de alimentación, para garantizar un seguimiento consistente.
>
> 📝 Recuerda diligenciar una encuesta cada día durante los 7 días.
>
> Tu código de registro es: {{censo}}
>
> 🔗 INGRESA AQUÍ A LA ENCUESTA:
> https://forms.gle/cedqXEt1zPQXZcRt6
> Muchas gracias
> 6:17 pm
> Listo, ya lo llene
> Ahora lo lleno recordatorio_semana_9_de_noviembre_sibate · Spanish que dice 🐶 REGISTRO DIARIO – DÍA {{dia}}/7
>
> ¡Hola, nombre entrevistada! 👋
> Te saluda el equipo de AZ Marketing Plus.
>
> Recuerda realizar hoy el registro del consumo de concentrado o purina de tu perro {{mascota}} .
>
> 📌 Recuerda:
>
> 🍽️ Realiza el registro en una sola comida al día y procura mantener la misma comida y el mismo horario durante toda la semana.
> ⏱️ Mide el tiempo desde que sirves el alimento hasta que tu perro termina de comer.
> 👀 Observa atentamente su comportamiento durante la alimentación y registra tus observaciones en la encuesta.
> 📝 Recuerda realizar un registro diario durante los 7 días.
>
> Tu código de registro es: {{censo}}
>
> 🔗 INGRESA AQUÍ A LA ENCUESTA:
> https://forms.gle/HAtyTHjKxLYmtinz5
> 6:18 pm
> Listo, ya la llene
> Mas tarde la lleni este el dia se digita antes de enviar

**L2** (decisiones del usuario, consultadas antes de escribir código):

- **Nombre en Meta de la primera:** `plantilla_inicio_semana_9_de_noviembre_sibate`, con el
  prefijo `plantilla_` tal cual lo pegó (precedente en el catálogo:
  `plantilla_sibate_2_302_oct_1_26`). Se usa ese string como `name` del payload a Meta.
- **Saludo de la de recordatorio:** el pedido decía "¡Hola, nombre entrevistada! 👋" sin llaves;
  el usuario confirmó que es la **variable** `{{entrevistada}}`, así que la plantilla lleva 4
  parámetros (`dia`, `entrevistada`, `mascota`, `censo`) y no 3.

**L3** (primer intento de implementación; la plantilla de registro fue rechazada por Meta, ver
L4):

- Catálogo: las 2 keys entran en `WHATSAPP_TEMPLATE_MAP` (name = key, `language` `es`, params en
  orden de aparición), en `WHATSAPP_TEMPLATE_LABELS`
  ("Inicio semana 9 de noviembre (Sibate) — encuesta diaria" y
  "Registro diario 9 de noviembre (Sibate)"), en `WHATSAPP_TEMPLATE_BODIES` y en
  `WHATSAPP_SINGLE_TEMPLATE_KEYS` (al final, sin reordenar las previas).
- Cuerpos byte-exactos: se conservan el doble espacio de "perrito  {{mascota}}  tarda", el
  espacio antes del punto en "{{mascota}} ." y la ausencia de línea en blanco entre
  "ENCUESTA DIARIA – 7 DÍAS" y el saludo de la primera plantilla, tal como vinieron en L1.
  El front (`WA_TEMPLATE_BODIES`) guarda el mismo literal, verificado por el check.
- Vista previa y día: `registro_noviembre_9_2026` entra en `BULK_DAY_TEMPLATES`
  (el campo día ya se muestra para toda plantilla con el parámetro `dia` en el modal 1×1 y en
  "Nuevo chat"); `plantilla_inicio_semana_9_de_noviembre_sibate` **no** entra, porque no usa
  `dia`. Las 2 keys se documentan también en `BULK_TEMPLATE_VARS` para la ayuda del masivo.
- Variable `{{mascotica}}`: el backend suma el alias `mascotica -> nombre del perro` en
  `whatsapp_send_template` y las tres vistas previas del front la sustituyen, para que el
  `parameter_name` aprobado en Meta viaje con el valor correcto.
- Test-first: `check_noviembre_9_sibate_templates.py` **RED 33 fallas** (catálogo, cuerpos,
  render, payloads) y `check_noviembre_9_sibate_preview.js` **RED** contra `HEAD`
  (`git show HEAD:frontend/call_center.js`: "no encontre el cuerpo de
  plantilla_inicio_semana_9_de_noviembre_sibate"). Después de T1-T3, **GREEN**.
- Regresión cubierta: el catálogo sigue siendo exactamente las 30 keys previas + las 2 nuevas,
  `WHATSAPP_SINGLE_TEMPLATE_KEYS` = las 14 previas + las 2 nuevas, y `sibate_5_de_octubre`,
  `recordatorio_sibate_1_204`, `recordatorio_sibate_2_302` y `729_sin_bono` conservan su cuerpo
  byte-exacto. El front conserva el campo día para `sibate_2`,
  `registro_diario_fatiga_6_semanas`, `sibate_90mas15_dias`, `recordatorio_sibate_1_204` y
  `recordatorio_sibate_2_302`, y lo sigue ocultando para `in_home_beta_385`.
- Envío cubierto: 1×1, masivo por estudio (`bulk_link`) y masivo por lista (`send-bulk`) mandan
  el payload exacto contra Meta simulado, y una key 1×1 no conectada al estudio sigue
  rechazándose con 403 sin llamar a Meta.
- Verificación: suite `scripts/tests` **26/26 OK** (17 `.py` + 9 `.js`); `python -m py_compile backend/main.py` y
  `node --check frontend/call_center.js` OK.
- Límite conocido (heredado, no de esta entrega): en el masivo **por lista** el contacto solo
  trae nombre y teléfono, así que `mascotica` y `censo` viajan vacíos — igual que en
  `recordatorio_sibate_1_204`/`_2_302`. Para mandar esos datos hay que usar el masivo **por
  estudio**, que sí toma la mascota y el censo del registro.

**L4** (cambio de requerimiento: Meta rechazó una de las dos, pedido del usuario verbatim):

> me rechazaron una de las plantillas cambio de nombre y un poco adentro aqui la que me aprobaron registro_noviembre_9_2026 · Spanish (SPA)
>  REGISTRO DIARIO
> DÍA {{dia}}/7
>
> ¡Hola, {{encuestada}}! 👋
> Te saluda el equipo de AZ Marketing Plus.
>
> Recuerda realizar hoy el registro del consumo de concentrado o purina de tu perro {{mascotica}}.
>
> 📌 Recuerda:
>
> 🍽️ Realiza el registro en una sola comida al día y procura mantener la misma comida y el mismo horario durante toda la semana.
> ⏱️ Mide el tiempo desde que sirves el alimento hasta que tu perro termina de comer.
> 👀 Observa atentamente su comportamiento durante la alimentación y registra tus observaciones en la encuesta.
> 📝 Recuerda realizar un registro diario durante los 7 días.
>
> Tu código de registro es: {{censo}}
>
> 🔗 INGRESA AQUÍ A LA ENCUESTA:
> https://forms.gle/HAtyTHjKxLYmtinz5
> 6:39 pm
> Mas tarde lo lleno
> Listo, ya lo llene esta otra si quedo bien plantilla_inicio_semana_9_de_noviembre_sibate · Spanish

Decisiones del usuario en L4:

- `plantilla_inicio_semana_9_de_noviembre_sibate` **quedó bien** y no se toca (lo dijo en el
  mismo mensaje: "esta otra si quedo bien plantilla_inicio_semana_9_de_noviembre_sibate").
- `{{mascotica}}` es **literal** (con t), tal como quedó aprobada en Meta; se consultó antes de
  escribir código porque el `parameter_name` tiene que coincidir o Meta responde 132000.
- El ruido del chat de L4 ("6:39 pm", "Mas tarde lo lleno", "Listo, ya lo llene") queda afuera
  del cuerpo, igual que en L1 (S5).

**L5** (implementación del cambio y evidencia final):

- La key `recordatorio_semana_9_de_noviembre_sibate` **sale** del catálogo (mapa, etiquetas,
  cuerpos, lista 1×1, `BULK_DAY_TEMPLATES`, `BULK_TEMPLATE_VARS` y `WA_TEMPLATE_BODIES`): Meta la
  rechazó, así que ofrecerla solo generaría envíos con 132001. Entra `registro_noviembre_9_2026`
  con label "Registro diario 9 de noviembre (Sibate)" y params
  `dia`, `encuestada`, `mascotica`, `censo`.
- Cuerpo nuevo byte-exacto: encabezado en dos líneas (`REGISTRO DIARIO` / `DÍA {{dia}}/7`) sin el
  🐶 ni el guion, saludo `{{encuestada}}`, y `{{mascotica}}.` sin el espacio previo al punto que
  traía el primer intento.
- El alias `mascotica` se resuelve a `nombre_mascota` en `whatsapp_send_template` y en las tres
  vistas previas del front, así que el valor que viaja es el nombre del perro del registro.
- Test-first: los 2 checks se repitieron en RED antes del cambio (los cuerpos aprobados de L4 no
  existían) y quedaron **GREEN** después. `check_729_sin_bono.py` se actualizó porque su
  aserción de la lista 1×1 era puntual (`SINGLE_PREVIAS + [KEY]`): ahora verifica el prefijo
  histórico, de modo que sumar keys al final no vuelva a romperlo.
- Verificación: suite `scripts/tests` **26/26 OK** (17 `.py` + 9 `.js`); `python -m py_compile backend/main.py` y
  `node --check frontend/call_center.js` OK.
- Pendiente fuera del código: que Meta tenga `plantilla_inicio_semana_9_de_noviembre_sibate` y
  `registro_noviembre_9_2026` aprobadas (`es`) con esos parámetros y cuerpos, y que el
  superusuario las conecte al estudio en "Plantillas 1×1" y "Plantillas".

**L6** (cambio de requerimiento: Meta rechazó la variante `REGISTRO DIARIO` y aprobó otra
redacción cuyo nombre de plantilla quedó `tal_cual`; pedido del usuario verbatim):

> quedo asi tal_cual · SpanishHola como estas?
> Día {{dia}} de 7 del seguimiento.
>
> Hola, {{encuestada}} 👋
> Somos el equipo de AZ Marketing Plus.
>
> Hoy corresponde registrar el consumo de concentrado de {{mascotica}}.
>
> Registro de hoy:
> 1. Sirve el alimento en la misma comida y a la misma hora de siempre.
> 2. Cronometra el tiempo que tarda tu perro en terminarlo.
> 3. Escribe qué observaste de su comportamiento.
> 4. Envía el formulario una vez al día durante los 7 días.
>
> Código de registro: {{censo}}
>
> Enlace del formulario:
> https://forms.gle/HAtyTHjKxLYmtinz5
>
> Cualquier duda, escríbenos por aquí y te respondemos.
> Hecho
> Mas tarde pero en el nombre en el crm dejalo como recordatorio semana 9 de noviembre sibate,
> toca que quitar ese

Decisiones del usuario (consultadas antes de escribir código):

- `tal_cual` es el nombre **literal** de la plantilla en Meta; viaja como `name` en el payload.
- "Hola como estas?" es la **primera línea del cuerpo aprobado**, no un saludo de chat (se
  confirmó explícitamente porque cambia el cuerpo byte-exacto).
- La key interna (la que se ve en el CRM) pasa a `recordatorio_semana_9_de_noviembre_sibate`,
  así que en esta entrada **key != name**. Ya había precedente en el catálogo:
  `sibate_5_de_octubre` viaja a Meta como `sibate5octubre`.
- `registro_noviembre_9_2026` **sale** del catálogo: lo reemplaza esta.

Detalle de la redacción nueva (por qué se ve así):

- Arranca con "Hola como estas?" y el `{{dia}}` deja de estar pegado a una barra (`DÍA {{dia}}/7`
  pasa a `Día {{dia}} de 7 del seguimiento.`).
- Se van el encabezado en mayúsculas, `📌 Recuerda:` y los emojis de viñeta; el CTA en
  mayúsculas `🔗 INGRESA AQUÍ A LA ENCUESTA` pasa a `Enlace del formulario:`.
- Cierra con una frase completa ("Cualquier duda, escríbenos por aquí y te respondemos."), en
  lugar de la variante incompleta que se había pegado ("Si tienes dudas quedamos atentos").
- Los 4 parámetros conservan nombre y orden de aparición (`dia`, `encuestada`, `mascotica`,
  `censo`), así que `whatsapp_send_template` y las tres vistas previas no cambian de lógica.

Cambios de código:

- `backend/main.py`: `WHATSAPP_TEMPLATE_MAP` (key nueva, `name` `tal_cual`),
  `WHATSAPP_TEMPLATE_LABELS` ("Recordatorio semana 9 de noviembre (Sibate)"),
  `WHATSAPP_SINGLE_TEMPLATE_KEYS` y `WHATSAPP_TEMPLATE_BODIES`.
- `frontend/call_center.js`: `WA_TEMPLATE_BODIES` (vista previa byte-idéntica),
  `BULK_TEMPLATE_VARS` y `BULK_DAY_TEMPLATES`.
- Checks: los dos de esta entrega más `check_el_azul.py`, `check_el_azul_preview.js` y
  `check_853_sin_bono_preview.js`, que usaban la key vieja como ancla de regresión del campo
  día. Las aserciones de `name` ahora comparan contra el nombre de Meta esperado y no contra
  la key (en esta plantilla ya no coinciden).
- Datos: no hay ninguna referencia a `registro_noviembre_9_2026` en `az_marketing.db`, así que
  ninguna conexión estudio↔plantilla quedó huérfana.
