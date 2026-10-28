#!/usr/bin/env python3
"""Bordes de S10: visibilidad de GET /whatsapp/templates (guardas del catalogo filtrado).

Complementa a `check_template_visibility.py` con los casos borde que la verificacion
independiente pidio dejar versionados (ver T20 y L15 del doc
`odd/tasks/plantillas-una-por-una.md`).

Reglas que se comprueban contra el codigo real:
  1. El rol se compara sin distinguir mayusculas: `SuperUser` ve el catalogo completo.
  2. `coordinator` ve lo conectado a estudios activos e inactivos.
  3. `agent` ve solo lo conectado a estudios ACTIVOS.
  4. `auxiliar` asignado ve solo lo suyo; sin asignaciones ve `[]`.
  5. Filas huerfanas (study_id que no existe) no habilitan nada.
  6. Una key retirada con fila vieja conectada no reaparece.
  7. Pedir el catalogo no modifica la base (hash del archivo sqlite antes/despues).
  8. GET /studies por rol, incluido `Auxiliar` con mayusculas (hoy NO recibe el join de
     asignaciones: comportamiento pre-existente, el catalogo lo refleja igual) e
     `include_inactive` ignorado.

Uso:    python scripts/tests/check_template_visibility_edges.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import hashlib
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

# La base temporal tiene que quedar seteada ANTES de importar la app.
DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_template_visibility_edges.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

FALLAS = []

RETIRADA = "sibate_encuesta_final"
HUERFANA_MASIVA = "in_home_beta_385"
HUERFANA_1X1 = "sigue_interesado"
STUDY_ID_INEXISTENTE = 999999


def check(cond, msg):
    if cond:
        print(f"  OK    {msg}")
    else:
        print(f"  FALLA {msg}")
        FALLAS.append(msg)


def _catalogo(db, user):
    return main.whatsapp_templates_catalog(db=db, current_user=user)


def _claves(db, user):
    return [t["key"] for t in _catalogo(db, user)]


def _en_orden_del_catalogo(keys):
    """Ordena un conjunto de keys como las devuelve el catalogo (orden del MAP)."""
    buscadas = set(keys)
    return [k for k in main.WHATSAPP_TEMPLATE_MAP if k in buscadas]


def _hash_db():
    h = hashlib.sha256()
    with open(DB_TEMP, "rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def _crear_usuario(db, username, rol):
    user = models.User(
        username=username,
        hashed_password=auth.get_password_hash("x"),
        role=rol,
        full_name=username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _crear_estudio(db, code, activo):
    study = models.Study(code=code, name=code, is_active=activo)
    db.add(study)
    db.commit()
    db.refresh(study)
    return study


def _asignar(db, user, study):
    db.execute(models.study_assignments.insert().values(user_id=user.id, study_id=study.id))
    db.commit()


def _estudios(db, user, include_inactive=False):
    return main.get_studies(include_inactive=include_inactive, db=db, current_user=user)


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        # El setup escribe con un superusuario en minusculas (es el rol que acepta
        # `set_study_templates`); la lectura con mayusculas se prueba aparte.
        admin = _crear_usuario(db, "chk_edge_admin", "superuser")
        admin_uc = _crear_usuario(db, "chk_edge_super_uc", "SuperUser")
        coord = _crear_usuario(db, "chk_edge_coord", "coordinator")
        agent = _crear_usuario(db, "chk_edge_agent", "agent")
        aux = _crear_usuario(db, "chk_edge_aux", "auxiliar")
        aux_libre = _crear_usuario(db, "chk_edge_aux_libre", "auxiliar")
        aux_uc = _crear_usuario(db, "chk_edge_aux_uc", "Auxiliar")

        activo = _crear_estudio(db, "EDGE_ACT", True)
        inactivo = _crear_estudio(db, "EDGE_INACT", False)
        otro_activo = _crear_estudio(db, "EDGE_ACT2", True)
        _asignar(db, aux, activo)

        # Conexiones: una masiva y una 1x1 por estudio.
        main.set_study_templates(
            activo.id, main.StudyTemplatesUpdate(template_keys=["manana_3"]),
            db=db, current_user=admin)
        main.set_study_single_templates(
            activo.id, main.StudySingleTemplatesUpdate(template_keys=["fatiga_729_r3"]),
            db=db, current_user=admin)
        main.set_study_templates(
            inactivo.id, main.StudyTemplatesUpdate(template_keys=["shampo_primer"]),
            db=db, current_user=admin)
        main.set_study_single_templates(
            inactivo.id, main.StudySingleTemplatesUpdate(template_keys=["shampo_segundo"]),
            db=db, current_user=admin)
        main.set_study_templates(
            otro_activo.id, main.StudyTemplatesUpdate(template_keys=["bono_final"]),
            db=db, current_user=admin)

        conectadas_todas = ["manana_3", "shampo_primer", "shampo_segundo", "fatiga_729_r3", "bono_final"]
        esperado_coord = _en_orden_del_catalogo(conectadas_todas)
        esperado_agent = _en_orden_del_catalogo(["manana_3", "fatiga_729_r3", "bono_final"])
        esperado_aux = _en_orden_del_catalogo(["manana_3", "fatiga_729_r3"])

        # ------------------------------------------------------------------
        print("[1] El rol se compara sin distinguir mayusculas: `SuperUser` ve todo")
        claves_uc = _claves(db, admin_uc)
        check(claves_uc == list(main.WHATSAPP_TEMPLATE_MAP),
              f"`SuperUser` ve las {len(main.WHATSAPP_TEMPLATE_MAP)} keys del catalogo "
              f"(vio {len(claves_uc)})")
        check(claves_uc == _claves(db, admin),
              "`SuperUser` y `superuser` devuelven exactamente lo mismo")
        check(HUERFANA_MASIVA in claves_uc and HUERFANA_1X1 in claves_uc,
              "`SuperUser` ve las keys que no estan conectadas a ningun estudio")

        # ------------------------------------------------------------------
        print("[2] Coordinator: activos e inactivos")
        check(_claves(db, coord) == esperado_coord,
              f"coordinator ve lo conectado a los 3 estudios (activo, inactivo, activo) -> "
              f"{_claves(db, coord)}")
        check("shampo_primer" in _claves(db, coord) and "shampo_segundo" in _claves(db, coord),
              "coordinator ve lo conectado al estudio INACTIVO")

        # ------------------------------------------------------------------
        print("[3] Agent: solo estudios activos")
        check(_claves(db, agent) == esperado_agent,
              f"agent ve solo lo de los estudios activos -> {_claves(db, agent)}")
        check("shampo_primer" not in _claves(db, agent),
              "agent NO ve shampo_primer (estudio inactivo)")
        check("shampo_segundo" not in _claves(db, agent),
              "agent NO ve shampo_segundo (1x1 de un estudio inactivo)")
        check("bono_final" in _claves(db, agent),
              "agent ve bono_final (estudio activo donde no esta asignado, pero es activo)")

        # ------------------------------------------------------------------
        print("[4] Auxiliar asignado: solo lo suyo")
        check(_claves(db, aux) == esperado_aux,
              f"auxiliar asignado al estudio activo ve solo lo suyo -> {_claves(db, aux)}")
        check("bono_final" not in _claves(db, aux),
              "auxiliar NO ve bono_final (estudio activo pero no asignado)")
        check("shampo_primer" not in _claves(db, aux),
              "auxiliar NO ve shampo_primer (estudio inactivo y no asignado)")

        # ------------------------------------------------------------------
        print("[5] Auxiliar sin asignaciones: lista vacia")
        check(_claves(db, aux_libre) == [],
              f"auxiliar sin asignaciones ve [] -> {_claves(db, aux_libre)}")

        # ------------------------------------------------------------------
        print("[6] Filas huerfanas (study_id inexistente) no habilitan nada")
        db.add(models.StudyTemplate(study_id=STUDY_ID_INEXISTENTE, template_key=HUERFANA_MASIVA))
        db.add(models.StudySingleTemplate(study_id=STUDY_ID_INEXISTENTE, template_key=HUERFANA_1X1))
        db.commit()
        check(db.query(models.StudyTemplate).filter(
                  models.StudyTemplate.study_id == STUDY_ID_INEXISTENTE).count() == 1,
              "la fila huerfana masiva quedo en la base")
        for nombre, user in (("coordinator", coord), ("agent", agent),
                             ("auxiliar", aux), ("Auxiliar", aux_uc)):
            claves = _claves(db, user)
            check(HUERFANA_MASIVA not in claves,
                  f"{nombre} NO ve la masiva huerfana ({HUERFANA_MASIVA})")
            check(HUERFANA_1X1 not in claves,
                  f"{nombre} NO ve la 1x1 huerfana ({HUERFANA_1X1})")
        check(_claves(db, aux_libre) == [],
              "auxiliar sin asignaciones sigue en [] pese a las filas huerfanas")

        # ------------------------------------------------------------------
        print("[7] Una key retirada con fila vieja no reaparece")
        db.add(models.StudyTemplate(study_id=activo.id, template_key=RETIRADA))
        db.add(models.StudySingleTemplate(study_id=activo.id, template_key=RETIRADA))
        db.commit()
        check(RETIRADA not in main.WHATSAPP_TEMPLATE_MAP,
              f"{RETIRADA} ya no esta en WHATSAPP_TEMPLATE_MAP (retirada)")
        for nombre, user in (("superuser", admin), ("SuperUser", admin_uc),
                             ("coordinator", coord), ("agent", agent),
                             ("auxiliar", aux), ("Auxiliar", aux_uc)):
            check(RETIRADA not in _claves(db, user),
                  f"{nombre} no ve {RETIRADA} aunque tenga filas viejas conectadas")
        check(len(_claves(db, admin)) == len(main.WHATSAPP_TEMPLATE_MAP),
              "el catalogo del superusuario no crece con la key retirada")

        # ------------------------------------------------------------------
        print("[8] Pedir el catalogo no modifica la base (hash de la sqlite)")
        db.commit()
        hash_antes = _hash_db()
        filas_antes = (db.query(models.StudyTemplate).count(),
                       db.query(models.StudySingleTemplate).count(),
                       db.query(models.Study).count())
        pedidos = []
        for user in (admin, admin_uc, coord, agent, aux, aux_libre, aux_uc):
            pedidos.append(_claves(db, user))
        _estudios(db, admin)
        _estudios(db, agent)
        hash_despues = _hash_db()
        filas_despues = (db.query(models.StudyTemplate).count(),
                         db.query(models.StudySingleTemplate).count(),
                         db.query(models.Study).count())
        check(hash_antes == hash_despues,
              f"el archivo sqlite queda identico ({hash_antes[:12]}... antes y despues)")
        check(filas_antes == filas_despues,
              f"no cambian las filas: {filas_antes} -> {filas_despues}")
        check(pedidos[2] == esperado_coord and pedidos[3] == esperado_agent,
              "los catalogos devueltos durante la medicion son los esperados")

        # ------------------------------------------------------------------
        print("[9] GET /studies por rol (incluido `Auxiliar` con mayusculas)")
        esperado_studies = {
            "superuser": [activo.id, inactivo.id, otro_activo.id],
            "SuperUser": [activo.id, inactivo.id, otro_activo.id],
            "coordinator": [activo.id, inactivo.id, otro_activo.id],
            "agent": [activo.id, otro_activo.id],
            "auxiliar": [activo.id],
            "auxiliar sin asignaciones": [],
            # Comportamiento PRE-EXISTENTE que este test solo documenta: el join con
            # `study_assignments` depende de `user.role == "auxiliar"` (sensible a
            # mayusculas), asi que un `Auxiliar` con mayusculas no recibe el filtro y ve
            # todos los estudios. El catalogo lo refleja igual (ve lo conectado a todos).
            "Auxiliar": [activo.id, inactivo.id, otro_activo.id],
        }
        usuarios = {
            "superuser": admin,
            "SuperUser": admin_uc,
            "coordinator": coord,
            "agent": agent,
            "auxiliar": aux,
            "auxiliar sin asignaciones": aux_libre,
            "Auxiliar": aux_uc,
        }
        for nombre, user in usuarios.items():
            ids = [s["id"] for s in _estudios(db, user)]
            check(ids == esperado_studies[nombre],
                  f"{nombre}: GET /studies -> {ids} (esperado {esperado_studies[nombre]})")
            ids_inactivo = [s["id"] for s in _estudios(db, user, include_inactive=True)]
            check(ids_inactivo == ids,
                  f"{nombre}: include_inactive sigue ignorado (mismo resultado)")
        claves_uc = _claves(db, aux_uc)
        check(claves_uc == esperado_coord,
              f"`Auxiliar` con mayusculas ve en el catalogo lo mismo que sus /studies "
              f"(todos) -> {claves_uc}")
        # GET /studies devuelve las keys conectadas tal cual (no filtra por catalogo, es
        # previo): por eso el estudio con la fila vieja lista la key retirada.
        detalle_activo = next(s for s in _estudios(db, admin) if s["id"] == activo.id)
        check(detalle_activo["template_keys"] == ["manana_3", RETIRADA],
              f"GET /studies sigue listando las keys conectadas sin filtrar el catalogo -> "
              f"{detalle_activo['template_keys']}")
        detalle = next(s for s in _estudios(db, admin) if s["id"] == otro_activo.id)
        check(detalle["template_keys"] == ["bono_final"],
              f"GET /studies sigue devolviendo las keys conectadas -> {detalle['template_keys']}")
        check(detalle["single_template_keys"] == [],
              f"GET /studies devuelve las 1x1 conectadas por estudio -> "
              f"{detalle['single_template_keys']}")
        detalle_1x1 = next(s for s in _estudios(db, admin) if s["id"] == inactivo.id)
        check(detalle_1x1["single_template_keys"] == ["shampo_segundo"],
              f"GET /studies devuelve la 1x1 del estudio inactivo -> "
              f"{detalle_1x1['single_template_keys']}")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} fallas.")
        sys.exit(1)
    print("\nTodo OK.")
