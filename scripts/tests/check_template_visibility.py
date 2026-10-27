#!/usr/bin/env python3
"""Verifica que GET /whatsapp/templates solo muestre lo que cada usuario puede ver.

Pedido del usuario (verbatim): *"Solo los estudios que ese usuario puede ver"* (ver L15 del
doc `odd/tasks/plantillas-una-por-una.md`).

Regla:
  - `superuser` -> catalogo completo (lo necesita para conectar plantillas a los estudios).
  - Cualquier otro rol -> solo las keys conectadas (masivas + 1x1) a los estudios que ese
    usuario ve, con la misma visibilidad que usa GET /studies.

Comprueba contra el codigo real:
  1. Superusuario: ve todo WHATSAPP_TEMPLATE_MAP, incluidas las 2 nuevas de recordatorio
     Sibate 204/302, aunque no esten conectadas a ningun estudio. El shape de cada item no cambia.
  2. Coordinator (ve todos los estudios): ve solo la plantilla conectada como masiva.
  3. Agent: ve solo lo conectado a estudios ACTIVOS (masivas y 1x1).
  4. Auxiliar: ve solo lo conectado a SUS estudios asignados; sin asignaciones, nada.
  5. Una plantilla retirada no aparece para ningun rol, aunque tenga filas conectadas.
  6. Regresion de GET /studies: mismos estudios (ids y orden) que antes del cambio.
  7. Sin N+1: el catalogo filtrado usa como maximo 3 consultas.

Uso:    python scripts/tests/check_template_visibility.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

# La base temporal tiene que quedar seteada ANTES de importar la app.
DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_template_visibility.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

from sqlalchemy import event  # noqa: E402

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

FALLAS = []

KEY_302 = "recordatorio_sibate_2_302"
KEY_204 = "recordatorio_sibate_1_204"
RETIRADA = "sibate_encuesta_final"

# Campos exactos de cada item del catalogo (el shape no cambia con este requerimiento).
CAMPOS = ["key", "name", "language", "label", "params", "body", "single_eligible"]


def check(cond, msg):
    if cond:
        print(f"  OK    {msg}")
    else:
        print(f"  FALLA {msg}")
        FALLAS.append(msg)


def _catalogo(db, user):
    """Catalogo real del endpoint.

    Se le pasa la sesion igual que en el request. El respaldo sin `db` permite correr
    este mismo test contra el codigo anterior al cambio (evidencia RED): antes la
    funcion no consultaba la base y devolvia el catalogo completo a todos.
    """
    try:
        return main.whatsapp_templates_catalog(db=db, current_user=user)
    except TypeError:
        return main.whatsapp_templates_catalog(current_user=user)


def _claves(db, user):
    return [t["key"] for t in _catalogo(db, user)]


def _contar_consultas():
    """Escucha las sentencias SQL que ejecuta la app mientras el test las mire."""
    consultas = []

    def _antes(conn, cursor, statement, parameters, context, executemany):
        consultas.append(statement)

    event.listen(database.engine, "before_cursor_execute", _antes)
    return consultas, lambda: event.remove(database.engine, "before_cursor_execute", _antes)


def _contar_consultas_de(db, user):
    """Consulta el catalogo contando solo sus propias sentencias SQL.

    Antes se calienta la sesion: los commit del test expiran las instancias y el primer
    acceso a `user.role` recarga el usuario con un SELECT que no es del catalogo.
    """
    _catalogo(db, user)
    consultas, parar = _contar_consultas()
    try:
        return _claves(db, user), consultas
    finally:
        parar()


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
        admin = _crear_usuario(db, "chk_vis_admin", "superuser")
        coord = _crear_usuario(db, "chk_vis_coord", "coordinator")
        agent = _crear_usuario(db, "chk_vis_agent", "agent")
        aux = _crear_usuario(db, "chk_vis_aux", "auxiliar")
        aux_libre = _crear_usuario(db, "chk_vis_aux_libre", "auxiliar")

        estudio_a = _crear_estudio(db, "VIS_A", True)
        estudio_b = _crear_estudio(db, "VIS_B", False)
        estudio_c = _crear_estudio(db, "VIS_C", True)
        _asignar(db, aux, estudio_a)

        # ------------------------------------------------------------------
        print("[1] Superusuario: catalogo completo, aunque no haya nada conectado")
        catalogo = _catalogo(db, admin)
        claves_admin = [t["key"] for t in catalogo]
        check(len(claves_admin) == len(main.WHATSAPP_TEMPLATE_MAP),
              f"ve las {len(main.WHATSAPP_TEMPLATE_MAP)} plantillas del catalogo (vio {len(claves_admin)})")
        check(claves_admin == list(main.WHATSAPP_TEMPLATE_MAP),
              "respeta el orden del catalogo")
        check(KEY_302 in claves_admin, f"incluye {KEY_302} sin estar conectada")
        check(KEY_204 in claves_admin, f"incluye {KEY_204} sin estar conectada")
        check(db.query(models.StudyTemplate).count() == 0
              and db.query(models.StudySingleTemplate).count() == 0,
              "no hay ninguna plantilla conectada a estudios todavia")
        check(all(list(t.keys()) == CAMPOS for t in catalogo),
              "todos los items conservan el shape key/name/language/label/params/body/single_eligible")
        check(all(t["label"] == main.WHATSAPP_TEMPLATE_LABELS.get(t["key"], t["key"]) for t in catalogo),
              "las etiquetas siguen saliendo de WHATSAPP_TEMPLATE_LABELS")
        check(all(t["params"] == main.WHATSAPP_TEMPLATE_MAP[t["key"]].get("params", []) for t in catalogo),
              "los parametros siguen saliendo de WHATSAPP_TEMPLATE_MAP")
        check(all(t["body"] == main.WHATSAPP_TEMPLATE_BODIES.get(t["key"]) for t in catalogo),
              "los cuerpos siguen saliendo de WHATSAPP_TEMPLATE_BODIES")
        check(all(t["single_eligible"] == (t["key"] in main.WHATSAPP_SINGLE_TEMPLATE_KEYS) for t in catalogo),
              "single_eligible no cambia")

        # ------------------------------------------------------------------
        print("[2] Coordinator: ve todos los estudios, pero solo lo conectado")
        check(_claves(db, coord) == [],
              f"sin plantillas conectadas devuelve lista vacia (vio {_claves(db, coord)})")
        main.set_study_templates(
            estudio_a.id,
            main.StudyTemplatesUpdate(template_keys=["manana_3"]),
            db=db,
            current_user=admin,
        )
        claves_coord = _claves(db, coord)
        check(claves_coord == ["manana_3"],
              f"ve solo la masiva conectada al estudio -> {claves_coord}")
        check(KEY_302 not in claves_coord, f"NO ve {KEY_302} (no esta conectada)")
        check(KEY_204 not in claves_coord, f"NO ve {KEY_204} (no esta conectada)")
        check("bono_final" not in claves_coord, "NO ve otra plantilla no conectada (bono_final)")

        # ------------------------------------------------------------------
        print("[3] Agent: solo lo conectado a estudios ACTIVOS (masivas + 1x1)")
        main.set_study_templates(
            estudio_b.id,
            main.StudyTemplatesUpdate(template_keys=["shampo_primer"]),
            db=db,
            current_user=admin,
        )
        main.set_study_single_templates(
            estudio_a.id,
            main.StudySingleTemplatesUpdate(template_keys=["r2_729"]),
            db=db,
            current_user=admin,
        )
        main.set_study_single_templates(
            estudio_b.id,
            main.StudySingleTemplatesUpdate(template_keys=["shampo_segundo"]),
            db=db,
            current_user=admin,
        )
        claves_agent = _claves(db, agent)
        check(claves_agent == ["manana_3", "r2_729"],
              f"agent ve la masiva y la 1x1 del estudio activo -> {claves_agent}")
        check("shampo_primer" not in claves_agent,
              "agent NO ve shampo_primer (conectada a un estudio inactivo)")
        check("shampo_segundo" not in claves_agent,
              "agent NO ve shampo_segundo (1x1 de un estudio inactivo)")
        claves_admin = _claves(db, admin)
        check(claves_admin == list(main.WHATSAPP_TEMPLATE_MAP),
              "superuser sigue viendo el catalogo completo")
        check("shampo_primer" in claves_admin and "shampo_segundo" in claves_admin,
              "superuser ve lo conectado a estudios activos e inactivos")
        claves_coord = _claves(db, coord)
        check(claves_coord == ["manana_3", "shampo_primer", "shampo_segundo", "r2_729"],
              f"coordinator ve lo conectado a todos los estudios (activos e inactivos) -> {claves_coord}")
        check(all(list(t.keys()) == CAMPOS for t in _catalogo(db, agent)),
              "el shape de los items filtrados es el mismo")

        # ------------------------------------------------------------------
        print("[4] Auxiliar: solo lo conectado a SUS estudios asignados")
        # Consecuencia deliberada de la spec ("Solo los estudios que ese usuario puede ver"):
        # un auxiliar deja de ver las plantillas de los estudios que no tiene asignados, y
        # por lo tanto deja de poder mandarlas por 1x1 desde un chat de ese estudio.
        claves_aux = _claves(db, aux)
        check(claves_aux == ["manana_3", "r2_729"],
              f"auxiliar asignado al estudio A ve solo lo de A -> {claves_aux}")
        check("shampo_primer" not in claves_aux,
              "auxiliar NO ve shampo_primer (estudio B, no asignado)")
        check("shampo_segundo" not in claves_aux,
              "auxiliar NO ve shampo_segundo (estudio B, no asignado)")
        claves_aux_libre = _claves(db, aux_libre)
        check(claves_aux_libre == [],
              f"auxiliar sin asignaciones no ve ninguna plantilla -> {claves_aux_libre}")

        # ------------------------------------------------------------------
        print("[5] Una plantilla retirada no aparece para ningun rol")
        # Filas conectadas a mano: el PUT las filtraria, pero la base puede tener filas viejas.
        db.add(models.StudyTemplate(study_id=estudio_a.id, template_key=RETIRADA))
        db.add(models.StudySingleTemplate(study_id=estudio_a.id, template_key=RETIRADA))
        db.commit()
        for nombre, user in (("superuser", admin), ("coordinator", coord),
                             ("agent", agent), ("auxiliar", aux)):
            claves = _claves(db, user)
            check(RETIRADA not in claves, f"{nombre} no ve {RETIRADA}")
        check(len(_claves(db, admin)) == len(main.WHATSAPP_TEMPLATE_MAP),
              "el catalogo del superuser sigue teniendo el mismo tamano")
        # Se limpian las filas viejas para no ensuciar la regresion de GET /studies
        # (ese endpoint lista las keys conectadas sin filtrar el catalogo; es previo).
        db.query(models.StudyTemplate).filter(
            models.StudyTemplate.template_key == RETIRADA).delete()
        db.query(models.StudySingleTemplate).filter(
            models.StudySingleTemplate.template_key == RETIRADA).delete()
        db.commit()

        # ------------------------------------------------------------------
        print("[6] Regresion de GET /studies (ids y orden) por rol")
        esperado = {
            "superuser": [estudio_a.id, estudio_b.id, estudio_c.id],
            "coordinator": [estudio_a.id, estudio_b.id, estudio_c.id],
            "auxiliar": [estudio_a.id],
            "agent": [estudio_a.id, estudio_c.id],
        }
        for nombre, user in (("superuser", admin), ("coordinator", coord),
                             ("auxiliar", aux), ("agent", agent)):
            ids = [s["id"] for s in _estudios(db, user)]
            check(ids == esperado[nombre], f"{nombre}: /studies -> {ids} (esperado {esperado[nombre]})")
            ids_inactivo = [s["id"] for s in _estudios(db, user, include_inactive=True)]
            check(ids_inactivo == ids,
                  f"{nombre}: include_inactive sigue ignorado (mismo resultado)")
        check([s["id"] for s in _estudios(db, aux_libre)] == [],
              "auxiliar sin asignaciones: /studies vacio")
        detalle_a = next(s for s in _estudios(db, admin) if s["id"] == estudio_a.id)
        check(detalle_a["template_keys"] == ["manana_3"] and detalle_a["single_template_keys"] == ["r2_729"],
              f"GET /studies sigue devolviendo las keys conectadas por estudio -> "
              f"masivas {detalle_a['template_keys']}, 1x1 {detalle_a['single_template_keys']}")
        check(list(detalle_a.keys()) == ["id", "code", "name", "is_active", "status", "study_type",
                                         "stage", "template_keys", "single_template_keys"],
              "el shape de GET /studies no cambia")

        # ------------------------------------------------------------------
        print("[7] Sin N+1: el catalogo filtrado usa como maximo 3 consultas")
        claves_coord, consultas = _contar_consultas_de(db, coord)
        check(len(consultas) == 3,
              f"coordinator (3 estudios) hace 3 consultas (estudios + masivas + 1x1) -> hizo {len(consultas)}")
        check(claves_coord == ["manana_3", "shampo_primer", "shampo_segundo", "r2_729"],
              f"el resultado no cambia al contar consultas -> {claves_coord}")

        estudio_d = _crear_estudio(db, "VIS_D", True)
        main.set_study_templates(
            estudio_d.id,
            main.StudyTemplatesUpdate(template_keys=["bono_final"]),
            db=db,
            current_user=admin,
        )
        claves_coord, consultas = _contar_consultas_de(db, coord)
        check(len(consultas) == 3,
              f"con 4 estudios sigue en 3 consultas (sin N+1) -> hizo {len(consultas)}")
        check("bono_final" in claves_coord, "y ve la plantilla del estudio nuevo")

        claves_admin, consultas = _contar_consultas_de(db, admin)
        check(len(consultas) == 0,
              f"el superuser no consulta la base (catalogo completo) -> hizo {len(consultas)}")
        check(claves_admin == list(main.WHATSAPP_TEMPLATE_MAP),
              "el catalogo del superuser sigue completo")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} fallas.")
        sys.exit(1)
    print("\nTodo OK.")
