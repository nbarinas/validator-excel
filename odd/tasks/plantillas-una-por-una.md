# Plantillas de WhatsApp "una por una" por estudio

**Feature:** agregar la plantilla `in_home_beta_385` (español) al catálogo y crear un
segundo conjunto de plantillas por estudio, las **"una por una"** (envío por registro),
administrable al lado del botón `Plantillas` que hoy conecta las masivas.
**Rama:** `feat/plantillas-una-por-una`

## Specs

**S1.** El catálogo debe incluir la plantilla `in_home_beta_385` con idioma español y este
cuerpo exacto (verbatim del pedido), con variables `{{encuestada}}`, `{{encuestador}}` y
`{{hora_asignada}}`:

```
Az-Marketing
Buenos días, señora {{encuestada}}, ¿cómo está? Mucho gusto.

Mi nombre es {{encuestador}}, trabajo para AZ Marketing Plus.

El motivo de mi mensaje es que usted nos está colaborando en un estudio de tratamiento para el cabello de los que se compran listos. Hace 15 días le entregamos el producto 358  y el día de hoy tiene programada una videollamada a las {{hora_asignada}}.

Quería confirmar si está disponible a esa hora o si podemos realizar la videollamada en este momento.

Quedo atento a su pronta respuesta.
Muchas gracias. ¡Feliz día!
```

`{{hora_asignada}}` se resuelve con la hora de recogida del registro (`collection_time`),
igual que `{{hora}}`; si no hay, `"hoy"`.

**S2.** Hoy el envío "una por una" tiene 3 plantillas, y deben poder conectarse/desconectarse
por estudio: `manana_3` (Buenas tardes (recordatorio)), `shampo_primer` (Shampoo — primer
contacto), `shampo_segundo` (Shampoo — segundo recordatorio).

**S3.** En el modal de bases de datos, al lado del botón `Plantillas` que hoy cambia a
plantillas masivas, debe haber un botón `Plantillas 1×1` para agregar o quitar las plantillas
"una por una" de cada estudio.

**S4.** El backend debe **rechazar siempre** el envío 1×1 de una plantilla que no esté
conectada al estudio (decisión del usuario; sin fallback permisivo).

**S5.** Elegibles para 1×1: `manana_3`, `shampo_primer`, `shampo_segundo`,
`in_home_beta_385`, `r2_729`. El masivo conserva todo el catálogo, incluidas
`in_home_beta_385` y `r2_729`.

**S6.** El modal "Nuevo chat" suma un selector de Estudio y ofrece solo las 1×1 de ese estudio.

**S8.** (Cambio de requerimiento, ver L11) El catálogo suma la plantilla `r2_729` (nombre Meta
`r2_729`, idioma `es`), habilitada para 1×1 y para el masivo. Usa las variables
`{{nombre_entrevistada}}`, `{{encuestador}}` y `{{hora_agendada}}`; esta última se resuelve con
`collection_time`, igual que `{{hora}}`. Cuerpo verbatim:

```
¡Muy buenos días, señora {{nombre_entrevistada}}! 😊

La saluda {{encuestador}}, de AZ Marketing Plus.

Le escribo porque hoy tiene programada la segunda videollamada del estudio de shampoo 729, a las {{hora_agendada}}.

¿Sería posible realizarla en este momento o prefiere que la contactemos más tarde?

Quedo atento a su respuesta. ¡Muchas gracias y feliz día! 🌷
```

**S7.** Al arrancar, si la tabla de 1×1 está totalmente vacía (primer deploy), conectar las 3
históricas a los estudios activos, para no cortar el trabajo el día 1. Es un sembrado único,
no un fallback permanente.

**S9.** (Cambio de requerimiento, ver L13) El catálogo suma `plantilla_sibate_2_302_oct_1_26`
(idioma `es`, plantilla de Meta categoría *Marketing*) e `inicio_de_semana_sibate_1_204_oct_26`
(idioma `es`, categoría *Utilidad*, identificador 13), con las variables `{{encuestada}}`,
`{{mascota}}` y `{{censo}}`, habilitadas para el envío 1×1 y para el masivo, con vista previa en
el front. Cuerpo verbatim del pedido (los dos textos pegados difieren **solo** en una línea: la
302 dice `codigo de resistro censo:` y la 204 dice `codigo de registro censo:`):

```
Hola, {{encuestada}}. ¡Buenos días! Te saluda el equipo de AZ Marketing Plus.

¡Hoy comenzamos la segunda fase del estudio con tu mascota {{mascota}}! 🐾 Muchas gracias por seguir participando y por tu compromiso.

📅 Durante los próximos 7 días, deberás medir el tiempo que tu perrito tarda en comer su concentrado habitual, mezclado con el suplemento que te enviamos.

🍽️ ¿Qué debes hacer cada día?

1. Sirve el alimento mezclado con el suplemento.
2. Mide el tiempo desde que le sirves hasta que termine de comer.
3. Observa si empieza a comer de inmediato o si primero olfatea el alimento.
4. Al finalizar, diligencia la encuesta del día.

⏰ La actividad se realiza una sola vez al día. Puedes elegir el desayuno, almuerzo o cena, procurando mantener el mismo horario durante los 7 días.

codigo de resistro censo: {{censo}}

🔗 Enlace para registrar tu actividad diaria:
https://forms.gle/kFrKRWKXFRkp6dhT9

🎁 Bono de $30.000: Al completar los 7 días, nos comunicaremos contigo por WhatsApp
```

Ese es el cuerpo de `plantilla_sibate_2_302_oct_1_26`. El de
`inicio_de_semana_sibate_1_204_oct_26` es idéntico salvo esa línea, que en el pedido dice:

```
codigo de registro censo: {{censo}}
```

En la misma entrega se **retiran** `sibate_encuesta_final`, `recordatorio_diario_semana_19_de_octubre_`
e `inicio_semana_19_de_octu`: no se ven más en ningún selector, no quedan como respaldo de vista
previa, salen de `BULK_DAY_TEMPLATES` y se rechazan en 1×1 y en masivo.

**S10.** (Cambio de requerimiento, ver L15) `GET /whatsapp/templates` deja de devolver el
catálogo completo a cualquier usuario autenticado:

| Rol | Qué ve en `/whatsapp/templates` |
|---|---|
| `superuser` | catálogo completo (`WHATSAPP_TEMPLATE_MAP`), sin cambios: lo necesita para conectar plantillas a los estudios |
| `coordinator` | solo las keys conectadas (masivas + 1×1) a los estudios que ve: todos, activos e inactivos |
| `agent` | solo las keys conectadas a estudios **activos** |
| `auxiliar` | solo las keys conectadas a **sus** estudios asignados |
| cualquier rol sin estudios / sin plantillas conectadas | lista vacía |

*"Sólo los estudios que ese usuario puede ver"* (pedido del usuario, L15). La visibilidad se
comparte con `GET /studies` vía `_visible_studies_query(db, user)`, una **extracción pura** de esa
lógica (superuser/coordinator/auxiliar sin filtro, resto solo `is_active`, auxiliar además `join`
con `study_assignments`). `GET /studies` no cambia de comportamiento: ni el orden, ni el shape, ni
el `include_inactive` que hoy se ignora. El shape de cada item del catálogo tampoco cambia
(`key`, `name`, `language`, `label`, `params`, `body`, `single_eligible`), y el catálogo filtrado
usa como máximo 3 consultas (estudios + masivas + 1×1), sin N+1.

**Consecuencia deliberada sobre `auxiliar`:** deja de ver las plantillas de los estudios que no
tiene asignados, y por lo tanto deja de poder mandarlas por 1×1 desde un chat de ese estudio.
Un `auxiliar` sin asignaciones no ve ninguna plantilla.

**El front sí cambia (T20).** `waLoadTemplateCatalog()` cacheaba el catálogo para toda la vida de
la página (`if (waTemplateCatalog) return waTemplateCatalog;`). Con el catálogo estático eso era
inocuo; con el filtro por estudio es un bug: si el superusuario conecta una plantilla mientras el
agente tiene la página abierta, el catálogo cacheado no tiene la key nueva, el selector la tira por
`waTemplateCatalogMap[key]` ausente (`waRenderTemplateOptions`, `waPopulateNewChatTemplates` y
`bulkLinkPopulateTemplates` filtran con `.filter(k => waTemplateCatalogMap[k])`) y al agente le
queda "(sin plantillas conectadas)" o la plantilla desaparece, sin error visible, hasta un F5.
Ahora la función vuelve a pedir `/whatsapp/templates` en **cada** llamada y refresca
`waTemplateCatalog`/`waTemplateCatalogMap`; los 6 call sites son aperturas de modal (no polling).

**S11.** (Cambio de requerimiento, ver L16) El catálogo suma `recordatorio_sibate_1_204` y
`recordatorio_sibate_2_302` (idioma `es`), habilitadas para el envío 1×1 **y** para el masivo, con
vista previa en el front. Parámetros en orden de aparición: `dia`, `entrevistada`, `mascota`,
`censo` para la 204; `dia`, `encuestada`, `mascota`, `censo` para la 302. Cuerpos verbatim del
pedido:

```
🐶 REGISTRO DIARIO – DÍA {{dia}}/7

¡Hola, {{entrevistada}}! 👋 Te saluda el equipo de AZ Marketing Plus.

🐾 Hoy debes registrar el consumo de tu mascota, {{mascota}}, del concentrado mas  el producto entregado (código 204).

🍽️ Registra una sola comida al día, manteniendo el mismo horario.

⏱️ Mide el tiempo que tarda en comer y registra su comportamiento en la encuesta.

🔢 Código de registro: {{censo}}

🔗 Diligencia aquí la encuesta:
https://forms.gle/pP9Fd9v5ZSTGjemX8

¡Gracias por tu compromiso! 💚 Recuerda completar el registro durante los 7 días del estudio.
```

```
🐶 REGISTRO DIARIO – DÍA {{dia}}/7

¡Hola, {{encuestada}}! 👋 Te saluda el equipo de AZ Marketing Plus.

🐾 Hoy debes registrar el consumo de tu mascota, {{mascota}}, del concentrado mas  el producto entregado (código 302).

🍽️ Registra una sola comida al día, manteniendo el mismo horario.

⏱️ Mide el tiempo que tarda en comer y registra su comportamiento en la encuesta.

🔢 Código de registro: {{censo}}

🔗 Diligencia aquí la encuesta:
https://forms.gle/pP9Fd9v5ZSTGjemX8

¡Gracias por tu compromiso! 💚 Recuerda completar el registro durante los 7 días del estudio.
```

El `{{dia}}` se digita antes de enviar, tanto en 1×1 como en el masivo: el campo ya existe y se
muestra para toda plantilla que declare `dia`; el backend rechaza el envío sin día con
`400 "Indica el día del registro antes de enviar"`. La vista previa sustituye también
`{{entrevistada}}`.

En la misma entrega se **retiran** `inicio_de_semana_sibate_1_204_oct_26` (etiqueta
"Inicio de semana Sibate 1 — producto 204") y `plantilla_sibate_2_302_oct_1_26_fase2`
(etiqueta "Sibate 2 — producto 302 (segunda fase)"): salen del catálogo, de las etiquetas, de
los cuerpos, de `WHATSAPP_SINGLE_TEMPLATE_KEYS` y de `BULK_DAY_TEMPLATES`; no se ven más en
ningún selector y el backend las rechaza con `400 "Plantilla no válida"` en 1×1 y en masivo.

## Tasks

| ID | Spec | Ruta | Estado |
|---|---|---|---|
| T1 | S1 | `backend/main.py`: MAP/LABELS/BODIES + `hora_asignada` en `param_values` | hecho (fd2c27b) |
| T2 | S2, S5 | `backend/models.py`: tabla `study_single_templates` | hecho (fd2c27b) |
| T3 | S3, S5 | `backend/main.py`: `GET/PUT /studies/{id}/single-templates` + `single_template_keys` en `GET /studies` + `single_eligible` en el catálogo | hecho (fd2c27b) |
| T4 | S7 | `backend/main.py` `on_startup()`: sembrado único | hecho (fd2c27b) |
| T5 | S4 | `backend/main.py` `/whatsapp/send-template`: validación 1×1 | hecho (fd2c27b) |
| T6 | S3 | `frontend/call_center.html`: modal `studySingleTemplatesModal` | hecho (9a25f0d) |
| T7 | S3 | `frontend/call_center.js`: botón + open/render/save 1×1 | hecho (9a25f0d) |
| T8 | S2, S5 | `frontend/call_center.js`/`.html`: selector dinámico en el modal por registro | hecho (9a25f0d) |
| T9 | S6 | `frontend/call_center.js`/`.html`: selector de estudio + optgroup dinámico en "Nuevo chat" | hecho (9a25f0d) |
| T10 | S1 | `frontend/call_center.js`: `{{hora_asignada}}` en vistas previas | hecho (9a25f0d) |
| T11 | S1-S7 | `scripts/tests/check_single_templates.py` | hecho (a618814) |
| T12 | S4 | fix B1: la validación aplica solo al catálogo 1×1 | hecho (b5676a1) |
| T13 | S6 | fix B2: default válido del select compartido | hecho (b5676a1) |
| T14 | S1-S7 | `scripts/tests/check_single_templates_regression.py` + `check_new_chat_bulk_default.js` | hecho (3f82582) |
| T15 | S8 (S5) | `backend/main.py` + `frontend/call_center.js` + `scripts/tests/check_r2_729_preview.js` | hecho (sin commit) |
| T16 | S9 | `backend/main.py` + `frontend/call_center.js`: 2 plantillas nuevas y 3 retiradas | hecho (commit único Oct 26) |
| T17 | S9 | `scripts/tests/check_sibate_oct26_templates.py`; retiro de los tests del 19 oct y día digitado reapuntado | hecho (commit único Oct 26) |
| T18 | S10 | `backend/main.py`: `_visible_studies_query` extraído de `GET /studies` + `GET /whatsapp/templates` filtrado por rol (masivas + 1×1 de los estudios visibles) | hecho (sin commit) |
| T19 | S10 | `scripts/tests/check_template_visibility.py` (RED→GREEN) + diferencial contra `HEAD` | hecho (sin commit) |
| T20 | S10 | fix del blocker: `frontend/call_center.js` `waLoadTemplateCatalog()` sin caché (refresca en cada apertura de modal) + `scripts/tests/check_template_catalog_refresh.js` (RED→GREEN) + `scripts/tests/check_template_visibility_edges.py` (bordes de S10) | hecho (sin commit) |
| T21 | S11 | `backend/main.py`: 2 plantillas nuevas (map/labels/bodies/single keys), `entrevistada` en `param_values`, retiro de las 2 del 26 oct y `dia` en `send-bulk` | hecho (commit de esta entrega) |
| T22 | S11 | `frontend/call_center.js`: cuerpos de respaldo, `{{entrevistada}}` en las 3 vistas previas, `BULK_DAY_TEMPLATES`, retiro de las 2 del 26 oct y dia en el envio masivo por lista | hecho (commit de esta entrega) |
| T23 | S11 | `scripts/tests/check_recordatorio_sibate_204_302.py` + `check_recordatorio_sibate_preview.js`; actualizar `check_template_visibility.py` y dar de baja `check_sibate_oct26_templates.py` | hecho (commit de esta entrega) |
| T24 | S11 | Verificación: suite, `node --check`, `py_compile` y evidencia en este doc | hecho (commit de esta entrega) |

Work units: backend (fd2c27b), frontend (9a25f0d), tests (a618814), fix de la verificación
(b5676a1), regresión (3f82582), r2_729 (sin commit), esta doc y el cambio del 26 de octubre
(commit único: plantillas + tests + doc).

## Log

**L1** (pedido original, verbatim):

> quiero agregar para plantillas adentro del crm la plantilla in_home_beta_385 · Spanish que dice Az-Marketing
> Buenos días, señora {{encuestada}}, ¿cómo está? Mucho gusto.
>
> Mi nombre es {{encuestador}}, trabajo para AZ Marketing Plus.
>
> El motivo de mi mensaje es que usted nos está colaborando en un estudio de tratamiento para el cabello de los que se compran listos. Hace 15 días le entregamos el producto 358  y el día de hoy tiene programada una videollamada a las {{hora_asignada}}.
>
> Quería confirmar si está disponible a esa hora o si podemos realizar la videollamada en este momento.
>
> Quedo atento a su pronta respuesta.
> Muchas gracias. ¡Feliz día!
> 12:55 pm
> Si, de una vez
> Mas tarde, porfa, en ese lugar estan 3 plantillas ahora y son : 
> Buenas tardes (recordatorio)
> manana_3
>
> Shampoo — primer contacto
> shampo_primer
>
> Shampoo — segundo recordatorio
> shampo_segundo, ademas de agregarlas quiero que para cada estudio queden en donde esta las bases de datos que tienen una ya que dice plantillas (esa que cambia a plantillas masivas el front) una al lado que diga plantillas una por una y que se puedan agregar o quitar a cada estudio activo, revisa y me dices el plan

**L2** (decisiones, verbatim de las respuestas del usuario):
- Validación 1×1: *"Que bloquee siempre"*.
- "Nuevo chat": *"Agregar selector de estudio en ese modal"*.
- `in_home_beta_385` en masivo: *"1×1 y masivo"*.
- Elegibles 1×1: *"Solo las 3 actuales + la nueva"*.

**L3** (pedido de ejecución, verbatim): *"procede en local y has el commit, al terminar me avisas"*.

**L4** (evidencia de exploración): el catálogo vive en `WHATSAPP_TEMPLATE_MAP`/`LABELS`/`BODIES`
(`backend/main.py:1389`, `1417`, `1467`) y se expone en `GET /whatsapp/templates` (`:2439`).
Las masivas por estudio ya usan `study_templates` (`models.py:71`) y el botón `Plantillas`
(`call_center.js:1146`). Las 1×1 NO tenían config por estudio: estaban hardcodeadas en los
radios de `whatsappSendTemplateModal` (`call_center.html:3198`) y en el `<optgroup>` de "Nuevo
chat" (`call_center.html:3027`). `/whatsapp/send-template` sólo validaba conexión cuando
`bulk_link=true` (`main.py:2503`). `create_all` crea tablas nuevas; las columnas nuevas van en
`on_startup()`.

**L5** (decisión de diseño): se usa una tabla nueva `study_single_templates` en vez de una
columna `scope` en `study_templates`, porque el `UniqueConstraint(study_id, template_key)` de
la tabla vieja impediría que una misma key (p.ej. `in_home_beta_385`) sea a la vez masiva y
1×1. Con tabla separada, los dos conjuntos son independientes.

**L6** (alcance de la validación, decisión del padre): cuando no se puede resolver ningún
estudio para un envío 1×1 (número nuevo sin llamada asociada y sin `study_id`), no se bloquea;
la validación aplica siempre que el estudio sea determinable. `bulk_link=true` conserva su
validación actual contra las masivas.

**L7** (verificación independiente, blockers): el primer `gentle-ai-verify` encontró dos
regresiones reales causadas por el cambio:
- **B1**: la validación corría para *todo* envío no masivo, así que `bono_final` y `bono_parcial`
  (que se mandan por `/whatsapp/send-template` con `call_id`, sin `bulk_link`) pasaban a dar 403
  en cualquier llamada con estudio. Baseline: enviaban.
- **B2**: el select `waNewChatKind` lo comparte el pegado de "Envío masivo". Al quedar en
  `'filter'` cuando no había estudio elegido, el paste posteaba `template_key:'filter'` y
  `/whatsapp/send-bulk` respondía 400. Baseline: el default era `shampo_primer` y funcionaba.

**L8** (fix y re-verificación): B1 se corrigió restringiendo la validación a
`request.template_key in WHATSAPP_SINGLE_TEMPLATE_KEYS` (las plantillas fuera del catálogo 1×1,
como los bonos, mantienen su comportamiento previo). B2 se corrigió con
`waNewChatAllSingleKeys()` (unión de las 1×1 de los estudios activos) como default y un guard
en `sendWhatsAppBulk`. El segundo `gentle-ai-verify` confirmó: **B1 resuelto, B2 resuelto, sin
blocker nuevo**, con S1/S4/S6 intactos y el body de `in_home_beta_385` byte-exacto contra el spec.

**L9** (evidencia): `check_single_templates.py` 26/26 OK; `check_single_templates_regression.py`
R1-R6 OK; `check_new_chat_bulk_default.js` OK; `node --check frontend/call_center.js` OK;
`py_compile` de `backend/main.py` y `backend/models.py` OK. Todos contra base SQLite temporal.
Auditoría contra `main` con el verificador: probó además que en un estudio con 1×1
`{manana_3}`, `bono_final`/`bono_parcial` envían y `shampo_primer`/`in_home_beta_385` no
conectadas dan 403; y que con un `<select>` realista `waNewChatKind` queda en `manana_3`.

**L10** (commits): `fd2c27b` backend, `9a25f0d` frontend, `a618814` check, `b5676a1` fix de
B1/B2, `3f82582` tests de regresión. Rama `feat/plantillas-una-por-una`, sin push ni PR.

**L11** (cambio de requerimiento, pedido del usuario verbatim):

> quiero agregar la plantilla de meta r2_729 · Spanish que dice ¡Muy buenos días, señora {{nombre_entrevistada}}! 😊
>
> La saluda {{encuestador}}, de AZ Marketing Plus.
>
> Le escribo porque hoy tiene programada la segunda videollamada del estudio de shampoo 729, a las {{hora_agendada}}.
>
> ¿Sería posible realizarla en este momento o prefiere que la contactemos más tarde?
>
> Quedo atento a su respuesta. ¡Muchas gracias y feliz día! 🌷
> 2:26 pm
> Si porfa, de una vez
> Mas tarde, porfa, para que el superusuario la agregue en 1x1 y plantillas (tambien en la previsializacion para que se vea en el front) sabes donde puedo hacer eso? revisa y me avisas antes de proceder a modificar el codigo

**L12** (decisión y evidencia): el usuario autorizó proceder con `r2_729` / `es`. Se agregó al
catálogo (`WHATSAPP_TEMPLATE_MAP`/`LABELS`/`BODIES`) y a `WHATSAPP_SINGLE_TEMPLATE_KEYS`, y se
mapearon `nombre_entrevistada` y `hora_agendada` en `param_values` (`backend/main.py`). En el
front (`frontend/call_center.js`): cuerpo de respaldo en `WA_TEMPLATE_BODIES`, reemplazo de las
variables en las tres vistas previas y reconocimiento de los nombres de parámetro en
`waUpdateTemplateForm`/`waToggleNewChatLink`/`waNewChatTemplateParams`. Checks nuevos:
`check_single_templates.py` (RED→GREEN) y `check_r2_729_preview.js`. El cuerpo del backend y el
del front quedan byte-idénticos (SHA-256 `2dec573524e11c67b590f4accaf06b9d29be1b0e589eaa9929adf86cf47fb6ce`).
Suite `scripts/tests` 5/5 OK, `py_compile` y `node --check` OK. Pendiente fuera del código:
que Meta tenga la plantilla `r2_729` (`es`) aprobada con esos `parameter_name`, y que el
superusuario la conecte al estudio (botones `Plantillas 1×1` y `Plantillas`).

**L13** (cambio de requerimiento, pedido del usuario verbatim):

> querio agregar plantilla_sibate_2_302_oct_1_26 · Spanish
> En revisión
> En revisión
> ·
> Marketing
> ·
> y dice Hola, {{encuestada}}. ¡Buenos días! Te saluda el equipo de AZ Marketing Plus.
>
> ¡Hoy comenzamos la segunda fase del estudio con tu mascota {{mascota}}! 🐾 Muchas gracias por seguir participando y por tu compromiso.
>
> 📅 Durante los próximos 7 días, deberás medir el tiempo que tu perrito tarda en comer su concentrado habitual, mezclado con el suplemento que te enviamos.
>
> 🍽️ ¿Qué debes hacer cada día?
>
> 1. Sirve el alimento mezclado con el suplemento.
> 2. Mide el tiempo desde que le sirves hasta que termine de comer.
> 3. Observa si empieza a comer de inmediato o si primero olfatea el alimento.
> 4. Al finalizar, diligencia la encuesta del día.
>
> ⏰ La actividad se realiza una sola vez al día. Puedes elegir el desayuno, almuerzo o cena, procurando mantener el mismo horario durante los 7 días.
>
> codigo de resistro censo: {{censo}}
>
> 🔗 Enlace para registrar tu actividad diaria:
> https://forms.gle/kFrKRWKXFRkp6dhT9
>
> 🎁 Bono de $30.000: Al completar los 7 días, nos comunicaremos contigo por WhatsApp
> 4:48 pm
> Listo, ya lo llene
> Ahora lo hago, ademas quiero agregar inicio_de_semana_sibate_1_204_oct_26 · Spanish
> En revisión
> En revisión
> ·
> Utilidad
> ·
> Fecha de actualización: 25 oct 2026
> ·
> Identificador: 13 que dice Hola, {{encuestada}}. ¡Buenos días! Te saluda el equipo de AZ Marketing Plus.
>
> ¡Hoy comenzamos la segunda fase del estudio con tu mascota {{mascota}}! 🐾 Muchas gracias por seguir participando y por tu compromiso.
>
> 📅 Durante los próximos 7 días, deberás medir el tiempo que tu perrito tarda en comer su concentrado habitual, mezclado con el suplemento que te enviamos.
>
> 🍽️ ¿Qué debes hacer cada día?
>
> 1. Sirve el alimento mezclado con el suplemento.
> 2. Mide el tiempo desde que le sirves hasta que termine de comer.
> 3. Observa si empieza a comer de inmediato o si primero olfatea el alimento.
> 4. Al finalizar, diligencia la encuesta del día.
>
> ⏰ La actividad se realiza una sola vez al día. Puedes elegir el desayuno, almuerzo o cena, procurando mantener el mismo horario durante los 7 días.
>
> codigo de registro censo: {{censo}}
>
> 🔗 Enlace para registrar tu actividad diaria:
> https://forms.gle/kFrKRWKXFRkp6dhT9
>
> 🎁 Bono de $30.000: Al completar los 7 días, nos comunicaremos contigo por WhatsApp
> 4:49 pm
> Listo, ya la llene
> Ahora la lleno que los agregues para que el superusuario los pueda ver y agregar en 1x1 y envio masivo ademas quiero que en este mismo commit me ayuda a desactivar
> Sibate — encuesta final (videollamada) (si
>
> Recordatorio diario — 19 de octubre
>
> Inicio semana — 19 de octubre que no se vean porque no los voy a usar mas, entiendes?

**L14** (decisiones y evidencia de la implementación del 26 de octubre):
- Las dos plantillas pegadas son **dos plantillas distintas** (una de Marketing y una de
  Utilidad), no un duplicado: sus textos difieren exactamente en la línea del código de
  registro (`resistro` en la 302, `registro` en la 204), así que se guardó cada cuerpo verbatim
  en la suya. **Pendiente del usuario:** el typo `resistro` está hoy en la plantilla de Meta
  302; si lo corrigen allá durante la revisión, el cuerpo de acá se ajusta en una línea.
- "Desactivar" = retirar del catálogo (mismo criterio que el set de concentrado en L1/L4): no
  se ven en ningún selector, no se pueden conectar por estudio y el backend las rechaza con
  `400 Plantilla no válida` en 1×1 y en masivo. Las filas viejas de `study_templates` /
  `study_single_templates` quedan en la base, pero el catálogo y los filtros de los `PUT` las
  ignoran.
- Etiquetas legibles en el estilo del catálogo: "Sibate 2 — producto 302 (segunda fase)" e
  "Inicio de semana Sibate 1 — producto 204".
- `BULK_DAY_TEMPLATES` quedó con las 3 plantillas con día que siguen vivas (`sibate_2`,
  `registro_diario_fatiga_6_semanas`, `sibate_90mas15_dias`).
- Tests: `check_sibate_oct26_templates.py` (RED 57 fallas → GREEN) cubre catálogo, cuerpos
  byte-exactos, render, conexión 1×1/masivo en un estudio, payloads a Meta, el rechazo de las 3
  retiradas y la regresión del día digitado. Se dio de baja
  `check_sibate_oct19_templates.py` (su objeto ya no existe; lo que seguía vivo pasó al test
  nuevo) y `check_oct19_dia_preview.js` se reapuntó a `sibate_90mas15_dias` como
  `check_template_day_preview.js`.
- Verificación: suite `scripts/tests` 10/10 OK, `py_compile` de `backend/main.py` y
  `node --check frontend/call_center.js` OK. Diferencial contra `HEAD` (árbol de `git archive`
  en `mktemp -d`, nunca commiteado): catálogo, cuerpos renderizados y payloads de 1×1 y masivo
  byte-idénticos en las 24 plantillas que siguen; las únicas diferencias son las 3 retiradas y
  las 2 nuevas.
- **Límite conocido, fuera de alcance:** el envío masivo sólo completa `encuestada`/`encuestado`
  con el nombre del contacto (`WhatsAppBulkContact` sólo lleva `nombre` y `telefono`), así que
  `{{mascota}}`/`{{censo}}` salen vacíos en el masivo. Le pasa igual a las plantillas que ya
  existían con esos parámetros; no se tocó para no cambiar el comportamiento de las demás.

**L15** (cambio de requerimiento: el catálogo deja de ser global, pedido del usuario verbatim):

> ok si quiero que desaparezca si el superusurio mismo no se lo otorga, se puede?

- **Respuesta de alcance (tal como llegó al implementador):** sí, el catálogo se filtra por la
  visibilidad de estudios. `superuser` conserva el catálogo completo porque es quien conecta las
  plantillas a los estudios; cualquier otro rol ve **sólo los estudios que ese usuario puede ver**
  (keys conectadas en `study_templates` y `study_single_templates` de esos estudios). El shape del
  item tampoco cambia. El front **sí** cambia: el catálogo se cacheaba para toda la sesión, y el
  filtro por estudio convirtió ese cache en un bug (el usuario no veía una plantilla recién
  conectada hasta refrescar la página); ahora se refresca en cada apertura de modal (T20, hallazgo
  más abajo).
- **Decisiones:** (1) la visibilidad se extrae a `_visible_studies_query(db, user)` y la comparten
  `GET /studies` y el catálogo, para que no existan dos definiciones de "qué estudios ve"; la
  extracción es pura y deja `include_inactive` igual de ignorado que antes. (2) El catálogo filtra
  recorriendo `WHATSAPP_TEMPLATE_MAP` (así una key retirada no reaparece aunque queden filas viejas
  conectadas en la base). (3) Sin estudios o sin plantillas conectadas devuelve `[]`.
- **Consecuencia documentada en S10:** un `auxiliar` deja de ver las plantillas de los estudios
  que no tiene asignados y, con eso, deja de poder mandarlas por 1×1 desde un chat de ese
  estudio; un `auxiliar` sin asignaciones no ve ninguna.
- **Test-first:** `scripts/tests/check_template_visibility.py` (nuevo, mismo estilo que
  `check_sibate_oct26_templates.py`: SQLite temporal en `scratch/_ctrl/`, `check()` acumulando
  fallas, 0/1). Casos: catálogo completo del superusuario sin nada conectado, coordinator con una
  sola masiva, agent (activos vs inactivo, masivas + 1×1), auxiliar (asignado / sin
  asignaciones), plantilla retirada con filas viejas conectadas, regresión de `GET /studies`
  (ids y orden por rol, shape e `include_inactive`) y conteo de consultas (3, sin N+1, 0 para el
  superusuario).
- **RED:** contra el código sin cambiar, **16 fallas**: coordinator, agent y auxiliar veían las
  **26 keys** (con `plantilla_sibate_2_302_oct_1_26`, `inicio_de_semana_sibate_1_204_oct_26` y
  `bono_final` incluidas) y el conteo de consultas daba 0 para el rol filtrado (el catálogo no
  consultaba la base).
- **GREEN:** **48 OK / 0 fallas**, con el `/studies` de los 4 roles intacto.
- **Suite:** `scripts/tests` 11/11 OK (8 `.py` + 3 `.js`; los 10 previos verdes más el nuevo),
  `py_compile` de `backend/main.py` OK y `node --check frontend/call_center.js` OK.
- **Diferencial contra `HEAD`** (árbol de `git archive HEAD` en `mktemp -d`, sonda y JSON en
  `scratch/_ctrl/`, nunca commiteados): `/studies` **byte-idéntico** en los 5 roles probados
  (superuser, coordinator, agent, auxiliar, auxiliar sin asignaciones). `/whatsapp/templates`
  idéntico para `superuser` (26 keys, item por item); para los demás cambia **sólo por filtrado**
  (mismos items, mismo orden del catálogo): coordinator 26 → 4 (`manana_3`, `shampo_primer`,
  `shampo_segundo`, `r2_729`), agent 26 → 2 (`manana_3`, `r2_729`), auxiliar 26 → 2 (`manana_3`,
  `r2_729`), auxiliar sin asignaciones 26 → 0.
- **Hallazgo de la verificación independiente (blocker, corregido en T20):** el filtro por estudio
  es correcto, pero el front cacheaba el catálogo para toda la vida de la página, así que el
  cambio no se veía sin F5. **Reproducción:** el agente carga la página (catálogo cacheado), el
  superusuario conecta una plantilla al estudio del agente mientras la página sigue abierta, el
  agente reabre el modal 1×1 → `waLoadTemplateCatalog()` devuelve el cache, la key nueva no está en
  `waTemplateCatalogMap` y el selector la descarta sin error visible. Con el catálogo estático
  anterior ese cache era inocuo: el filtro es lo que lo vuelve un bug real, y por eso el test
  nuevo también falla contra `HEAD`.
- **Fix:** se quita el short-circuit de `waLoadTemplateCatalog()` (queda el `try/catch` y el filtro
  `HIDDEN_TEMPLATE_KEYS` como estaban) y la función pide `/whatsapp/templates` en cada llamada.
  Los 6 call sites (`openStudyTemplatesModal`, `openStudySingleTemplatesModal`,
  `openWhatsAppTemplateModal`, `openWhatsAppTemplateModalFromChat`, el modal de "Nuevo chat" y el
  de enlace masivo) son aperturas de modal, no polling, así que no hay costo de fondo.
- **Evidencia del fix:** `scripts/tests/check_template_catalog_refresh.js` extrae la función real y
  la corre con un `fetch` falso que primero devuelve `['manana_3']` y después
  `['manana_3', 'r2_729']`. **RED** (contra el árbol de trabajo antes del fix y también contra
  `HEAD`: el front era el mismo): 8 fallas — un solo fetch, el segundo catálogo seguía en
  `['manana_3']`, `waTemplateCatalogMap['r2_729']` quedaba ausente y un fetch fallido servía el
  catálogo viejo. **GREEN** después del fix: 11 OK / 0 fallas.
- **Guardas versionadas:** `scripts/tests/check_template_visibility_edges.py` fija los bordes de
  S10 que no estaban cubiertos: rol `SuperUser` con mayúsculas (ve el catálogo completo),
  coordinator con activos e inactivos, agent sólo activos, auxiliar asignado sólo lo suyo,
  auxiliar sin asignaciones `[]`, filas huérfanas con `study_id` inexistente que no habilitan nada,
  key retirada con fila vieja que no reaparece, hash de la SQLite idéntico antes/después de pedir
  el catálogo, y `GET /studies` por rol con `include_inactive` ignorado (53 OK / 0 fallas: es una
  guarda, no un RED). Ahí queda documentado un
  **comportamiento pre-existente** que no se toca: el join con `study_assignments` depende de
  `user.role == "auxiliar"` (sensible a mayúsculas), así que un `Auxiliar` con mayúsculas no recibe
  ese filtro y ve todos los estudios; el catálogo lo refleja fielmente (ve lo conectado a todos).
  Verificación de esta ronda: suite `scripts/tests` verde con los 13 archivos previstos (9 `.py` + 4
  `.js`: los 11 que ya estaban más los 2 nuevos), `py_compile` de `backend/main.py` y
  `node --check frontend/call_center.js` OK.
- **Advisory pre-existente, fuera de alcance:** (1) un usuario puede enviar por 1×1 una plantilla
  conectada a un estudio que no ve: el servidor valida contra la conexión del estudio, no contra la
  visibilidad del usuario, así que el filtro del catálogo no es un control de autorización de
  envío; (2) `/whatsapp/send-bulk` no tiene guard por estudio (no valida que las plantillas del
  payload estén conectadas a un estudio visible). Ninguno de los dos se tocó en este cambio.

**L16** (cambio de requerimiento, pedido del usuario verbatim):

> quiero agregar en 1x1 y plantillas masivas la primera es recordatorio_sibate_1_204 · Spanish y 🐶 REGISTRO DIARIO – DÍA {{dia}}/7
>
> ¡Hola, {{entrevistada}}! 👋 Te saluda el equipo de AZ Marketing Plus.
>
> 🐾 Hoy debes registrar el consumo de tu mascota, {{mascota}}, del concentrado mas  el producto entregado (código 204).
>
> 🍽️ Registra una sola comida al día, manteniendo el mismo horario.
>
> ⏱️ Mide el tiempo que tarda en comer y registra su comportamiento en la encuesta.
>
> 🔢 Código de registro: {{censo}}
>
> 🔗 Diligencia aquí la encuesta:
> https://forms.gle/pP9Fd9v5ZSTGjemX8
>
> ¡Gracias por tu compromiso! 💚 Recuerda completar el registro durante los 7 días del estudio.
> 1:41 pm
> Listo, ya lo llene
> Mas tarde lo hago la de dia es para que se antes de enviar la persona coloque (digite el numero)  y la otra es recordatorio_sibate_2_302 · Spanish y 🐶 REGISTRO DIARIO – DÍA {{dia}}/7
>
> ¡Hola, {{encuestada}}! 👋 Te saluda el equipo de AZ Marketing Plus.
>
> 🐾 Hoy debes registrar el consumo de tu mascota, {{mascota}}, del concentrado mas  el producto entregado (código 302).
>
> 🍽️ Registra una sola comida al día, manteniendo el mismo horario.
>
> ⏱️ Mide el tiempo que tarda en comer y registra su comportamiento en la encuesta.
>
> 🔢 Código de registro: {{censo}}
>
> 🔗 Diligencia aquí la encuesta:
> https://forms.gle/pP9Fd9v5ZSTGjemX8
>
> ¡Gracias por tu compromiso! 💚 Recuerda completar el registro durante los 7 días del estudio.
> 1:45 pm
> Listo, ya lo llene
> Ahora lo hago y quiero eliminar para que no aparezca nicio de semana Sibate 1 — producto 204
>
> Sibate 2 — producto 302 (segunda fase) que no los vamos a usar

**L17** (implementación del cambio, evidencia):
- Catálogo: `recordatorio_sibate_1_204` (params `dia`, `entrevistada`, `mascota`, `censo`) y
  `recordatorio_sibate_2_302` (`dia`, `encuestada`, `mascota`, `censo`), etiquetas "Recordatorio
  Sibate 1 — producto 204" y "Recordatorio Sibate 2 — producto 302". Cuerpos byte-exactos en
  `WHATSAPP_TEMPLATE_BODIES` y en `WA_TEMPLATE_BODIES`; ambos conservan el doble espacio de
  "mas  el" tal como vino en el pedido.
- `entrevistada` se mapea a `person_name` en `whatsapp_send_template` y en
  `whatsapp_send_bulk`; las tres vistas previas del front la sustituyen y
  `waToggleNewChatLink`/`waNewChatTemplateParams` la reconocen como nombre.
- Día digitado: las dos keys entraron en `BULK_DAY_TEMPLATES`; el modal 1×1 y "Nuevo chat"
  muestran el campo; el masivo por estudio (`bulk_link=true` con contactos del estudio) ya lo
  mandaba por contacto, y el "Envío masivo" por lista ahora lee `waNewChatDay`, valida y manda
  `dia` (`WhatsAppSendBulkRequest.dia`). Sin día: `400 "Indica el día del registro antes de
  enviar"` en 1×1, en `send-template` masivo y en `send-bulk`, sin request a Meta ni registro.
- Retiro: `inicio_de_semana_sibate_1_204_oct_26` y
  `plantilla_sibate_2_302_oct_1_26_fase2` salieron de MAP/LABELS/BODIES/SINGLE_KEYS, del
  `WA_TEMPLATE_BODIES` del front y de `BULK_DAY_TEMPLATES`; `grep` no los encuentra en
  `backend/` ni en `frontend/`, y ambos endpoints responden `400 "Plantilla no válida"`.
- Test-first: `check_recordatorio_sibate_204_302.py` **RED 55 fallas** y
  `check_recordatorio_sibate_preview.js` **RED 6 fallas**; después **GREEN**. Se dio de baja
  `check_sibate_oct26_templates.py` (su objeto ya no existe) y `check_template_visibility.py` se
  reapuntó a las keys nuevas.
- Verificación: suite `scripts/tests` **15/15 OK** (9 `.py` + 6 `.js`), `py_compile` de
  `backend/main.py` y `node --check frontend/call_center.js` OK. Diferencial read-only contra
  `HEAD` (árbol de `git archive` en temporal): 24 keys supervivientes byte-idénticas en
  name/language/label/params/body/single_eligible y cuerpo renderizado; 96/96 escenarios de
  envío compartidos con payload y registro idénticos; front con las 24 keys idénticas;
  `BULK_DAY_TEMPLATES` = las 3 vivas + las 2 nuevas; árbol de trabajo sin mutar.
- Límite pre-existente, fuera de alcance: el "Envío masivo" por lista (`/whatsapp/send-bulk`)
  sólo recibe `nombre`/`telefono` por contacto, así que `{{mascota}}` y `{{censo}}` siguen
  saliendo vacíos ahí; el masivo por estudio (`bulk_link=true`) sí manda mascota y censo. No se
  cambió el contrato de la lista.
