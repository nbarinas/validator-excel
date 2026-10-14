#!/usr/bin/env python3
"""S3/S4: en una base YA EXISTENTE, el arranque de la app debe crear las columnas nuevas.

La trampa que cubre esta prueba: `Base.metadata.create_all` NO altera tablas que ya existen, y la
lista `new_call_cols_2` de `backend/main.py` esta dentro de una funcion con un `return`
incondicional antes (codigo inalcanzable). O sea: una prueba sobre base nueva pasa sin migrar nada.
Aca se corre el MISMO hook que uvicorn (`on_startup`) sobre una copia de la base real, que es el
caso de produccion.

Uso:    python scripts/tests/check_calls_migration.py
Salida: 0 = el arranque crea las columnas en una base existente; 1 = quedan sin crear; 2 = no hay
        fixture disponible.
"""
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

NUEVAS = ["hair_dye", "hair_keratin", "hair_straightening", "hair_other_treatment"]
BASE_REAL = RAIZ / "az_marketing.db"


def base_sintetica(ruta):
    """Fallback cuando no hay una base real: `calls` incompleta a proposito."""
    con = sqlite3.connect(ruta)
    con.execute("CREATE TABLE calls (id INTEGER PRIMARY KEY, phone_number VARCHAR(20), hair_type VARCHAR(50))")
    con.execute("INSERT INTO calls (phone_number, hair_type) VALUES ('3001234567', 'MIXTO')")
    con.commit()
    con.close()


def columnas(ruta, tabla):
    con = sqlite3.connect(ruta)
    try:
        return [r[1] for r in con.execute(f"PRAGMA table_info({tabla})")]
    finally:
        con.close()


def correr():
    carpeta = tempfile.mkdtemp(prefix="migracion_")
    ruta = os.path.join(carpeta, "existente.db")

    if BASE_REAL.exists():
        shutil.copyfile(BASE_REAL, ruta)
        origen, completa = f"copia de {BASE_REAL.name}", True
    else:
        base_sintetica(ruta)
        origen, completa = "base sintetica (no hay az_marketing.db)", False

    antes = columnas(ruta, "calls")
    print(f"fixture: {origen} | calls tiene {len(antes)} columnas | ya tiene las nuevas: "
          f"{[c for c in NUEVAS if c in antes] or 'ninguna'}")

    os.environ["DATABASE_URL"] = f"sqlite:///{ruta}"

    import backend.main as main  # se importa despues de fijar la base

    try:
        main.on_startup()  # el mismo hook que corre uvicorn al arrancar
        error = None
    except Exception as e:  # el arranque nunca deberia romper por esto
        error = f"{type(e).__name__}: {e}"

    faltan = [c for c in NUEVAS if c not in columnas(ruta, "calls")]

    consulta = "no probada (base sintetica)"
    if completa:
        try:
            db = main.database.SessionLocal()
            db.query(main.models.Call).first()
            db.close()
            consulta = "ok"
        except Exception as e:
            consulta = f"{type(e).__name__}: {str(e)[:110]}"

    print(f"on_startup(): {'sin excepcion' if error is None else error}")
    print(f"columnas nuevas faltantes: {faltan or 'ninguna'}")
    print(f"consulta ORM de Call: {consulta}")

    fallas = []
    if faltan:
        fallas.append(f"el arranque no crea {faltan} en una base existente")
    if consulta not in ("ok", "no probada (base sintetica)"):
        fallas.append(f"la app no puede consultar Call: {consulta}")

    if fallas:
        print(f"\nFALLA: {'; '.join(fallas)}")
        return 1
    print("\nOK: el arranque crea las columnas nuevas en una base existente y la app consulta Call")
    return 0


if __name__ == "__main__":
    sys.exit(correr())
