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

**S5.** Elegibles para 1×1: `manana_3`, `shampo_primer`, `shampo_segundo`, `in_home_beta_385`.
El masivo conserva todo el catálogo, incluida `in_home_beta_385`.

**S6.** El modal "Nuevo chat" suma un selector de Estudio y ofrece solo las 1×1 de ese estudio.

**S7.** Al arrancar, si la tabla de 1×1 está totalmente vacía (primer deploy), conectar las 3
históricas a los estudios activos, para no cortar el trabajo el día 1. Es un sembrado único,
no un fallback permanente.

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

Work units: backend (fd2c27b), frontend (9a25f0d), tests (a618814), fix de la verificación
(b5676a1), regresión (3f82582) y esta doc.

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
