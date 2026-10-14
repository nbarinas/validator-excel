# Carga completa de estudios de cabello (Excel -> CRM)

**Feature:** que `POST /upload-calls` guarde **todas** las columnas utiles de un Excel de
cabello, y que **avise** cuando alguna columna no tenga destino (hoy las descarta en silencio).
**Origen del analisis:** carga real del estudio `study_id = 185`
("In Home 15 + 15 Beta (358 vs 358.).xlsx"), hecha por SQL fuera de la app.

## Specs

**S1.** El encabezado `Tratamiento Variedad` debe guardarse en `calls.treatment_variety`.

**S2.** Los encabezados compuestos deben guardarse en el campo de marca correspondiente:
- `marca y variedad shampoo` -> `calls.shampoo_brand`
- `marca y variedad acondicionador` -> `calls.conditioner_brand`
- `tratamient presentacion` -> `calls.shampoo_quantity`

**S3.** `second_collection_date`, `second_collection_time` y `shampoo_quantity` deben poder
mapearse desde Excel. Antes se leian en el constructor del `Call` pero **no existian como claves
en `cols_mapping`**: `cols_mapping.get(key, [])` devolvia `[]` y el valor era siempre `None`.

**S4.** Las cuatro preguntas deben guardarse en columnas nuevas y verse en el CRM:
- `12. ¿Tiene tintura en el cabello?` -> `hair_dye`
- `13. ¿Tiene queratina en el cabello?` -> `hair_keratin`
- `14. ¿Tiene alisados químicos, permanentes en el cabello?` -> `hair_straightening`
- `15. ¿Tiene otro tipo de tratamiento en el cabello?` -> `hair_other_treatment`

Valores reales en el Excel de origen (por eso `VARCHAR(100)` y no `SI/NO`):
`'MARLIU'`, `'PALET'`, `'PANTENE'`, `'NO'`, `'NO SABE'`, `'SI-NO RECUERDA'`.

**S5.** `POST /upload-calls` debe devolver en su JSON la lista de columnas del Excel que se
ignoraron, y el CRM debe mostrarla al terminar la carga.
Ejemplo: `{"status":"ok","count":90,"study_id":185,"study_name":"...","ignoradas":["Tratamiento Variedad"]}`

**S6.** Todo id que el selector del CRM ofrece (`STANDARD_FIELDS`) y todo campo canonico de
`QUESTION_HEADER_MAP` tiene que ser aceptado por el backend. Si no, el usuario mapea a mano y la
columna se pierde igual. El check la detecta: encontro `code`, `dog_name`, `stool_texture` y
`health_status` sin alias en `cols_mapping` (mismo bug que S1-S2, en estudios de mascotas).

## Tasks

| ID | Spec | Ruta | Evidencia |
|---|---|---|---|
| T1 | S1-S3 | `backend/main.py` (`cols_mapping`) | RED 11 fallas -> GREEN 30/30 |
| T2 | S4 | migrador (781-810), `backend/models.py`, constructor, `c_dict` | modelo 68 cols, migrador 32 cols, todo destino existe como columna |
| T3 | S1-S4 | `frontend/call_center.js`, `frontend/call_center.html` | contrato: 159 alias / 51 ids / 7 canonicos; `node --check` OK en HEAD y en la modificada |
| T4 | S5 | return `ignoradas` + alert del CRM | caso B: `ignoradas=['COLUMNA BASURA']` |
| T5 | S6 | alias de `code`, `dog_name`, `stool_texture`, `health_status` | los detecto el check; corregidos |
| T6 | S1-S5 | `scripts/tests/check_column_mapping.py` | stdlib, sin dependencias, corre en verde |
| T7 | S1-S5 | `scripts/tests/check_upload_calls.py` | end-to-end: `count=1`, `ignoradas=[]`, 30/30 campos correctos |
| T8 | S4 | `on_startup()` en `backend/main.py` (bloque "Calls") | `check_calls_migration.py`: RED `no such column: calls.hair_dye` -> GREEN |
| T9 | S4 | `scripts/tests/check_calls_migration.py` | corre en verde contra una copia de la base real |

Columnas nuevas: aditivas, **en `on_startup()`** (`backend/main.py`, bloque `# Calls`, junto a
`bonus_amount`/`bulk_send_status`), que es la unica migracion que corre de verdad.
`ALTER TABLE calls ADD COLUMN` solo si la columna falta. No borra ni reescribe datos.

> Correccion (L6): la lista `new_call_cols_2` de `backend/main.py:772-813` **no sirve** para migrar:
vive dentro de `update_bulk_link_permission` (arranca en 582) despues de un `return` incondicional
en 597, o sea que es codigo inalcanzable. `Base.metadata.create_all` tampoco altera tablas
existentes. La migracion tiene que estar en `on_startup`. Lo cubre `check_calls_migration.py`.

## Log

**L1** (pedido original, verbatim):
> la carga quedo perfecta, podrias con lo aprendido decirme que tenemos que modificar para que el cargue quede completo a la proxima?? en el codigo tenemos cargar para cabello

**L2** (decision de alcance, verbatim):
> Nivel 1 + aviso + las 4 preguntas con columnas

**L3** (evidencia): el endpoint no lee el `.xlsx` subido por el usuario. El frontend pega texto
TSV, auto-mapea con `KNOWN_BACKEND_COLUMNS` + `isRecognizedColumn` (substring, 603-612), rearma un
`.xlsx` con SheetJS y lo manda a `/upload-calls`. El backend resuelve con **igualdad exacta**.
Las listas no coincidian: 4 columnas se descartaban sin aviso. `scripts/tests/check_column_mapping.py`
versiona ese contrato.

**L4** (hallazgo del check, S6): al contrastar `STANDARD_FIELDS` contra `cols_mapping` aparecieron 4
bugs latentes del mismo tipo que el reportado, en estudios de mascotas: el selector ofrece `code`,
`dog_name`, `stool_texture` y `health_status`, y el backend no aceptaba ninguno de esos cuatro
nombres. Mapear a mano con esos ids perdia la columna en silencio. Se agregaron los 4 alias.

**L5** (evidencia end-to-end): `check_upload_calls.py` llama la funcion real del endpoint con una
base SQLite temporal. Caso A: `count=1`, `ignoradas=[]`, los 30 campos con su valor y `status='pending'`.
Caso B (columna sin destino): `ignoradas=['COLUMNA BASURA']`. `node --check` OK en la version de HEAD
y en la modificada. La base local `az_marketing.db` quedo intacta (1 estudio, 34 llamadas).

**L6** (defecto bloqueante encontrado por la verificacion independiente, B1): las 4 columnas nuevas
estaban declaradas en `models.py` pero **ninguna migracion las creaba**. Yo habia citado
`new_call_cols_2` como "migrador idempotente", y esa lista es codigo muerto (`update_bulk_link_permission`
retorna en la linea 597; la lista empieza en 772). Consecuencia en una base existente: cualquier
consulta de `Call` falla con `no such column: calls.hair_dye` -> el CRM entero en 500. Reproducido
sobre una copia de `az_marketing.db` y arreglado agregando las 4 columnas al `ALTER TABLE` de
`on_startup()`, que si corre. `check_upload_calls.py` no lo detectaba porque arma la base con
`metadata.create_all` (base nueva); por eso se agrego `check_calls_migration.py`, que usa una copia
de la base real.

**L7** (commit): d2efe37 en la rama feat/hair-upload-completeness (work unit unico de este cambio).
