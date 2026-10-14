#!/usr/bin/env python3
"""Prueba end-to-end del cargador real de `POST /upload-calls`.

Importa la app con una base SQLite temporal, inserta un estudio y llama a la funcion del
endpoint con un `.xlsx` armado al vuelo. Despues lee la fila guardada y comprueba, campo por
campo, que el valor de cada encabezado cayo en la columna correcta de `calls`.
No necesita servidor, ni token, ni la base real.

Uso:    python scripts/tests/check_upload_calls.py
Salida: 0 = la carga guarda todo como se espera; 1 = hay diferencias.
"""
import asyncio
import io
import os
import sys
from pathlib import Path
from types import SimpleNamespace

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts" / "tests"))

# La base temporal tiene que quedar seteada ANTES de importar la app (database.py conecta al importar).
DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_upload_calls.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

import pandas as pd  # noqa: E402
from fastapi import BackgroundTasks  # noqa: E402

import check_column_mapping as contrato  # noqa: E402  (reusa la lista de encabezados reales)
import backend.main as main  # noqa: E402

STUDY_ID = 185
CELULAR = "3001234567"  # el loader deja solo digitos en phone_number


class ArchivoFalso:
    """Lo minimo que el endpoint usa de `UploadFile`."""

    def __init__(self, contenido: bytes):
        self._contenido = contenido

    async def read(self):
        return self._contenido


def excel(columnas, fila):
    buffer = io.BytesIO()
    pd.DataFrame([fila], columns=columnas).to_excel(buffer, index=False)
    return buffer.getvalue()


def cargar(columnas, fila, db, usuario):
    return asyncio.run(
        main.upload_calls(
            background_tasks=BackgroundTasks(),
            file=ArchivoFalso(excel(columnas, fila)),
            study_id=STUDY_ID,
            db=db,
            current_user=usuario,
        )
    )


def valores_sinteticos():
    """Un valor reconocible por columna, con el celular en digitos."""
    valores = {h: f"V{i:02d}" for i, h in enumerate(contrato.ENCABEZADOS)}
    valores["CELULAR"] = CELULAR
    return valores


def esperado_por_campo(valores):
    esperado = {contrato.ESPERADO[h]: valores[h] for h in contrato.ENCABEZADOS}
    esperado["phone_number"] = CELULAR
    return esperado


def correr():
    fallas = []
    main.models.Base.metadata.create_all(bind=main.database.engine)
    db = main.database.SessionLocal()
    db.add(main.models.Study(id=STUDY_ID, code="TEST_MAPEO", name="Test de mapeo", study_type="cabello", stage="R1"))
    db.commit()
    usuario = SimpleNamespace(id=1, role="superuser")

    # --- Caso A: los 30 encabezados del Excel real tienen que guardarse todos ---
    valores = valores_sinteticos()
    fila = [valores[h] for h in contrato.ENCABEZADOS]
    respuesta = cargar(contrato.ENCABEZADOS, fila, db, usuario)
    print(f"A) respuesta: count={respuesta.get('count')} ignoradas={respuesta.get('ignoradas')}")

    if respuesta.get("count") != 1:
        fallas.append(f"  [X] se esperaba 1 registro cargado, se obtuvo {respuesta.get('count')!r}")
    if respuesta.get("ignoradas"):
        fallas.append(f"  [X] columnas ignoradas con el Excel real: {respuesta.get('ignoradas')!r}")

    registro = db.query(main.models.Call).filter(main.models.Call.study_id == STUDY_ID).first()
    if registro is None:
        fallas.append("  [X] no se guardo ninguna fila en calls")
    else:
        for campo, valor in esperado_por_campo(valores).items():
            obtenido = getattr(registro, campo, "<no existe la columna>")
            if obtenido != valor:
                fallas.append(f"  [X] {campo}: se esperaba {valor!r}, quedo {obtenido!r}")
        if registro.status != "pending":
            fallas.append(f"  [X] status: se esperaba 'pending', quedo {registro.status!r}")

    # --- Caso B: una columna sin destino tiene que aparecer en `ignoradas` (S5) ---
    columnas_b = contrato.ENCABEZADOS + ["COLUMNA BASURA"]
    fila_b = [valores[h] for h in contrato.ENCABEZADOS] + ["no tiene destino"]
    respuesta_b = cargar(columnas_b, fila_b, db, usuario)
    print(f"B) respuesta: count={respuesta_b.get('count')} ignoradas={respuesta_b.get('ignoradas')}")
    if respuesta_b.get("ignoradas") != ["COLUMNA BASURA"]:
        fallas.append(f"  [X] ignoradas deberia ser ['COLUMNA BASURA'], fue {respuesta_b.get('ignoradas')!r}")

    db.close()
    main.database.engine.dispose()
    try:
        DB_TEMP.unlink()
    except OSError:
        pass

    if fallas:
        print(f"\nFALLA: {len(fallas)} diferencia(s)")
        print("\n".join(fallas))
        return 1
    print("\nOK: el cargador guarda los encabezados del Excel en su columna y avisa los ignorados")
    return 0


if __name__ == "__main__":
    sys.exit(correr())
