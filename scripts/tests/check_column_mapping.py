#!/usr/bin/env python3
"""Verifica el contrato de mapeo de columnas de `POST /upload-calls`.

Lee la tabla de alias REAL desde `backend/main.py` (no la duplica) y comprueba que
cada encabezado de un Excel de estudio de cabello llegue al campo esperado de `calls`.

Uso:    python scripts/tests/check_column_mapping.py
Salida: 0 = el contrato se cumple; 1 = hay encabezados sin destino o mal ruteados.
Solo stdlib: no requiere pytest ni instalar nada.
"""
import ast
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MAIN = RAIZ / "backend" / "main.py"
MODELS = RAIZ / "backend" / "models.py"
FRONTEND_JS = RAIZ / "frontend" / "call_center.js"
FRONTEND_HTML = RAIZ / "frontend" / "call_center.html"

# Encabezados reales de "In Home 15 + 15 Beta (358 vs 358.).xlsx" (hoja "Hoja 1", fila 1).
# '\xa0' es el espacio duro que trae el encabezado "Segundo Código\xa0" del Excel.
ENCABEZADOS = [
    "CIUDAD", "CENSO", "NSE", "CODIGO", "Segundo Código\xa0", "Nombre", "EDAD",
    "CELULAR", "WHASSAPP", "BARRIO", "DIRECCION", "DESCRIPCION VIVIENDA",
    "Marca tratamiento", "Tratamiento Variedad", "tratamient presentacion",
    "marca y variedad shampoo", "marca y variedad acondicionador",
    "Tipo de cabello", "Forma de cabello", "Largo de cabello",
    "12. ¿Tiene tintura en el cabello?",
    "13. ¿Tiene queratina en el cabello?",
    "14. ¿Tiene alisados químicos, permanentes en el cabello?",
    "15. ¿Tiene otro tipo de tratamiento en el cabello?",
    "ENCUESTADOR", "SUPERVISOR", "Fecha Implantación", "FECHA DE RECOGIDA",
    "HORA DE RECOGIDA", "CEDULA",
]

# Encabezado -> campo de `calls` donde tiene que caer.
ESPERADO = {
    "CIUDAD": "city",
    "CENSO": "census",
    "NSE": "nse",
    "CODIGO": "code",
    "Segundo Código\xa0": "segundo_codigo",
    "Nombre": "person_name",
    "EDAD": "age",
    "CELULAR": "phone_number",
    "WHASSAPP": "whatsapp",
    "BARRIO": "neighborhood",
    "DIRECCION": "address",
    "DESCRIPCION VIVIENDA": "housing_description",
    "Marca tratamiento": "treatment_brand",
    "Tratamiento Variedad": "treatment_variety",
    "tratamient presentacion": "shampoo_quantity",
    "marca y variedad shampoo": "shampoo_brand",
    "marca y variedad acondicionador": "conditioner_brand",
    "Tipo de cabello": "hair_type",
    "Forma de cabello": "hair_shape",
    "Largo de cabello": "hair_length",
    "12. ¿Tiene tintura en el cabello?": "hair_dye",
    "13. ¿Tiene queratina en el cabello?": "hair_keratin",
    "14. ¿Tiene alisados químicos, permanentes en el cabello?": "hair_straightening",
    "15. ¿Tiene otro tipo de tratamiento en el cabello?": "hair_other_treatment",
    "ENCUESTADOR": "implantation_pollster",
    "SUPERVISOR": "supervisor",
    "Fecha Implantación": "implantation_date",
    "FECHA DE RECOGIDA": "collection_date",
    "HORA DE RECOGIDA": "collection_time",
    "CEDULA": "person_cc",
}

# Campos que el constructor del Call ya lee pero que no se podian mapear (siempre NULL).
CAMPOS_SIN_ALIAS_HISTORICO = ["second_collection_date", "second_collection_time", "shampoo_quantity"]

# Columnas creadas para las preguntas 12-15: ademas de mapearse, tienen que existir en el modelo
# y estar en el migrador idempotente, o el INSERT/UPDATE falla en runtime.
CAMPOS_NUEVOS_PREGUNTAS = ["hair_dye", "hair_keratin", "hair_straightening", "hair_other_treatment"]

# Encabezados que se perdian en silencio antes de este cambio (el frontend los daba por buenos
# y el backend no los conocia). Cada uno tiene que estar reconocido en LOS DOS lados.
ENCABEZADOS_QUE_SE_PERDIAN = [
    "Tratamiento Variedad",
    "tratamient presentacion",
    "marca y variedad shampoo",
    "marca y variedad acondicionador",
    "12. ¿Tiene tintura en el cabello?",
    "13. ¿Tiene queratina en el cabello?",
    "14. ¿Tiene alisados químicos, permanentes en el cabello?",
    "15. ¿Tiene otro tipo de tratamiento en el cabello?",
]

IDS_PANEL_CABELLO = ["hairDye", "hairKeratin", "hairStraightening", "hairOtherTreatment"]


def cargar_cols_mapping(path=MAIN):
    """Devuelve el dict `cols_mapping` tal como lo ve el endpoint, sin ejecutar el modulo."""
    arbol = ast.parse(path.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Assign):
            for destino in nodo.targets:
                if isinstance(destino, ast.Name) and destino.id == "cols_mapping":
                    return ast.literal_eval(nodo.value)
    raise SystemExit(f"ERROR: no encontre la tabla `cols_mapping` en {path}")


def resolver(cols_mapping, encabezado):
    """Misma semantica que get_val(): comparacion exacta, sin acentos normalizados ni substring."""
    clave = str(encabezado).strip().lower()
    for campo, alias in cols_mapping.items():
        for a in alias:
            if str(a).strip().lower() == clave:
                return campo
    return None


def campos_del_modelo(path=MODELS):
    """Nombres asignados a Column(...) dentro de la clase Call de models.py."""
    arbol = ast.parse(path.read_text(encoding="utf-8"))
    campos = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ClassDef) and nodo.name == "Call":
            for sentencia in nodo.body:
                if isinstance(sentencia, ast.Assign) and isinstance(sentencia.value, ast.Call):
                    if getattr(sentencia.value.func, "id", None) == "Column":
                        for destino in sentencia.targets:
                            if isinstance(destino, ast.Name):
                                campos.add(destino.id)
    return campos


def columnas_a_migrar(path=MAIN):
    """Nombres de columna declarados en la lista `new_call_cols_2` (el migrador idempotente)."""
    arbol = ast.parse(path.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Assign):
            for destino in nodo.targets:
                if isinstance(destino, ast.Name) and destino.id == "new_call_cols_2":
                    return [col for col, _ in ast.literal_eval(nodo.value)]
    return []


def normalizar_como_frontend(texto):
    """Equivalente a normalizeHeaderKey() del frontend: sin acentos, minusculas, espacios colapsados."""
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFD", str(texto)) if unicodedata.category(c) != "Mn"
    )
    return " ".join(sin_acentos.lower().split())


def bloque_js(fuente, nombre):
    """Texto entre `const <nombre> = [` y el primer `];`."""
    inicio = fuente.index(f"const {nombre} = [")
    return fuente[inicio:fuente.index("];", inicio)]


def literales_js(fragmento):
    """Strings entre comillas simples o dobles de un fragmento de JS."""
    return re.findall(r"'([^']*)'", fragmento) + re.findall(r'"([^"]*)"', fragmento)


def verificar_frontend(cols_mapping, fallas):
    """El contrato real: el frontend manda nombres de columna y el backend los resuelve por alias
    EXACTO. Si las dos listas no coinciden, la columna se pierde en silencio (el bug original)."""
    fuente_js = FRONTEND_JS.read_text(encoding="utf-8")
    fuente_html = FRONTEND_HTML.read_text(encoding="utf-8")

    conocidos = [normalizar_como_frontend(c) for c in literales_js(bloque_js(fuente_js, "KNOWN_BACKEND_COLUMNS"))]
    bloque_std = bloque_js(fuente_js, "STANDARD_FIELDS")
    ids_estandar = re.findall(r"id:\s*'([^']+)'", bloque_std)
    bloque_preg = bloque_js(fuente_js, "QUESTION_HEADER_MAP")
    campos_canonicos = re.findall(r"field:\s*'([^']+)'", bloque_preg)
    tests_pregunta = [normalizar_como_frontend(t) for t in literales_js(bloque_preg)]

    # 1) Los encabezados que se perdian tienen que estar reconocidos en los dos lados.
    for encabezado in ENCABEZADOS_QUE_SE_PERDIAN:
        clave = normalizar_como_frontend(encabezado)
        if resolver(cols_mapping, encabezado) is None:
            fallas.append(f"  [X] el backend no reconoce {encabezado!r}")
        en_lista = clave in conocidos
        por_pregunta = any(t and t in clave for t in tests_pregunta)
        if not (en_lista or por_pregunta):
            fallas.append(f"  [X] el frontend no reconoce {encabezado!r} (no esta en KNOWN_BACKEND_COLUMNS ni en QUESTION_HEADER_MAP)")

    # 2) Lo que el frontend manda tiene que ser un alias que el backend acepta.
    for campo in campos_canonicos:
        if resolver(cols_mapping, campo) is None:
            fallas.append(f"  [X] QUESTION_HEADER_MAP manda {campo!r} y el backend no lo reconoce")
    for identificador in ids_estandar:
        if identificador == "ignorar":
            continue
        if resolver(cols_mapping, identificador) is None:
            fallas.append(f"  [X] STANDARD_FIELDS ofrece {identificador!r} y el backend no lo reconoce")

    # 3) Ya no hay preguntas 'sin columna en la BD'.
    if "isUnsupportedQuestion" in fuente_js:
        fallas.append("  [X] quedo una referencia a isUnsupportedQuestion en el frontend")

    # 4) El panel de cabello tiene que tener donde mostrar las 4 columnas nuevas.
    for identificador in IDS_PANEL_CABELLO:
        if f'id="{identificador}"' not in fuente_html:
            fallas.append(f"  [X] falta el span id={identificador!r} en call_center.html")

    print(f"frontend: {len(conocidos)} alias conocidos | {len(ids_estandar)} campos en el selector | {len(campos_canonicos)} campos canonicos")


def main():
    cols_mapping = cargar_cols_mapping()
    print(f"cols_mapping: {len(cols_mapping)} campos | encabezados del Excel: {len(ENCABEZADOS)}")

    fallas = []
    for encabezado in ENCABEZADOS:
        esperado = ESPERADO[encabezado]
        obtenido = resolver(cols_mapping, encabezado)
        if obtenido != esperado:
            fallas.append(f"  [X] {encabezado!r} -> {obtenido!r}, esperado {esperado!r}")
        else:
            print(f"  [ok] {encabezado!r} -> {obtenido}")

    for campo in CAMPOS_SIN_ALIAS_HISTORICO:
        if campo not in cols_mapping:
            fallas.append(f"  [X] la clave {campo!r} no existe en cols_mapping (su valor es siempre NULL)")

    # Todo destino del mapeo tiene que ser una columna real del modelo: si no, el upload explota con 500.
    campos_modelo = campos_del_modelo()
    destinos = set(ESPERADO.values()) | set(CAMPOS_SIN_ALIAS_HISTORICO)
    for campo in sorted(destinos):
        if campo not in campos_modelo:
            fallas.append(f"  [X] {campo!r} se mapea pero no existe como Column en models.Call")

    # Las columnas nuevas tienen que estar en el migrador o nunca se crean en la base.
    a_migrar = columnas_a_migrar()
    for campo in CAMPOS_NUEVOS_PREGUNTAS:
        if campo not in a_migrar:
            fallas.append(f"  [X] {campo!r} no esta en new_call_cols_2: la columna nunca se crearia")

    print(f"modelos.Call: {len(campos_modelo)} columnas | migrador new_call_cols_2: {len(a_migrar)} columnas")

    verificar_frontend(cols_mapping, fallas)

    if fallas:
        print(f"\nFALLA: {len(fallas)} problema(s) de mapeo")
        print("\n".join(fallas))
        return 1

    print(f"\nOK: los {len(ENCABEZADOS)} encabezados caen en su campo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
