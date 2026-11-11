# Checks de `scripts/tests`

30 scripts standalone (19 `.py` + 11 `.js`), sin pytest ni dependencias: cada uno imprime
`OK`/`FALLA` y sale con código distinto de cero si falla. No hay CI, así que se corren a mano
—o con el runner de abajo, que además los agrupa por área.

## Cómo correr

```bash
python scripts/tests/run_checks.py --list                  # mapa check -> área
python scripts/tests/run_checks.py --scope templates       # cambio de plantillas
python scripts/tests/run_checks.py --scope templates,masivo
python scripts/tests/run_checks.py --solo-fallas --scope llamadas
python scripts/tests/run_checks.py                         # todo (30)
```

Salida `0` = todo pasó. `1` = algo falló **o** hay un `check_*` nuevo sin clasificar en el mapa
del runner (aborta a propósito: un check que nadie corre es peor que ninguno).

También se pueden correr sueltos, desde la raíz del repo:

```bash
python scripts/tests/check_noviembre_9_sibate_templates.py
node   scripts/tests/check_noviembre_9_sibate_preview.js
```

## Política: qué correr según el cambio

| Cambio | Scope | Por qué |
|---|---|---|
| Agregar, renombrar, sacar o corregir una plantilla de WhatsApp | `templates` | toca el catálogo compartido: `WHATSAPP_TEMPLATE_MAP`, `_LABELS`, `_BODIES`, `SINGLE_TEMPLATE_KEYS`, `BULK_DAY_TEMPLATES`, `WA_TEMPLATE_BODIES` |
| Cuerpo o vista previa de una plantilla | `templates` | el backend y `frontend/call_center.js` tienen que quedar byte-idénticos |
| Filtro de estados del envío múltiple / links | `masivo` | UI del masivo que no lee el catálogo |
| Migraciones, columnas del Excel, `POST /upload-calls` | `llamadas` | no toca plantillas |
| Antes de un release o un cambio en código verdaderamente compartido | `todo` | es la única pasada que cubre las tres áreas |

Más sintaxis, siempre y gratis:

```bash
python -m py_compile backend/main.py
node --check frontend/call_center.js
```

## Qué cubre cada familia

| Familia | Qué afirma |
|---|---|
| `check_*_templates.py` | por plantilla: `name` real que viaja a Meta, idioma `es`, parámetros en orden de aparición, cuerpo byte-exacto backend↔front, payload en 1×1 y masivo contra Meta simulado, `400` cuando falta el día, `403` si la key no está conectada al estudio |
| `check_*_preview.js` | las tres vistas previas del front (modal 1×1, "Nuevo chat", masivo por estudio): sustitución de variables, marcador `[día]`, que no quede ningún `{{` |
| `check_single_templates*.py`, `check_template_visibility*.py` | estructura de la lista 1×1 y qué plantillas ve cada estudio |
| `check_template_day_preview.js`, `check_new_chat_bulk_default.js` | campo día y default del select compartido 1×1/masivo — depende de que la key exista en el catálogo |
| `check_calls_migration.py`, `check_column_mapping.py`, `check_upload_calls.py` | columnas nuevas sobre base existente, mapeo de encabezados y carga del `.xlsx` |

## Regla al agregar un check nuevo

Clasificalo en `SCOPES` dentro de `run_checks.py`. Si no, el runner aborta con el nombre del
archivo sin clasificar. Es la única forma de que "correr lo del área" no te deje un check afuera.

## Contexto

El porqué de este runner y el caso que lo motivó (una aserción puntual de otra entrega,
`check_729_sin_bono.py`, que se rompió al sumar una plantilla) están en
`odd/tasks/plantillas-noviembre-9-sibate.md`, entradas L5 y L6.
