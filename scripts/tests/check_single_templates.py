#!/usr/bin/env python3
"""Verifica las plantillas "una por una" por estudio y la plantilla in_home_beta_385.

Importa la app con una base SQLite temporal y llama a las funciones reales de los
endpoints (sin servidor ni token). Comprueba:

  1. El catalogo expone `in_home_beta_385` (es, {{hora_asignada}}) y `fatiga_729_r3`
     (es, {{hora_agendada}}), y marca solo las 5 elegibles como `single_eligible`.
  2. El render sustituye encuestada/encuestador/hora_asignada y
     nombre_entrevistada/encuestador/hora_agendada.
  3. Se conectan/desconectan plantillas 1x1 por estudio, sin tocar las masivas.
  4. `GET /whatsapp/single-templates` resuelve el estudio por call_id, telefono y study_id.
  5. `POST /whatsapp/send-template` bloquea (403) una plantilla no conectada y un estudio
     sin 1x1, y acepta la conectada.
  6. El sembrado unico del arranque solo toca estudios activos y no se repite.

Uso:    python scripts/tests/check_single_templates.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

# La base temporal tiene que quedar seteada ANTES de importar la app (database.py conecta al importar).
DB_TEMP = RAIZ / "scratch" / "_ctrl" / "test_single_templates.db"
DB_TEMP.parent.mkdir(parents=True, exist_ok=True)
if DB_TEMP.exists():
    DB_TEMP.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_TEMP}"

from fastapi import HTTPException  # noqa: E402

import backend.main as main  # noqa: E402
from backend import auth, database, models  # noqa: E402

FALLAS = []


def check(cond, msg):
    if cond:
        print(f"  OK    {msg}")
    else:
        print(f"  FALLA {msg}")
        FALLAS.append(msg)


def correr():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = models.User(
            username="chk_admin",
            hashed_password=auth.get_password_hash("x"),
            role="superuser",
            full_name="Admin Check",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        study = models.Study(code="CHK1", name="Check 1x1", is_active=True)
        study2 = models.Study(code="CHK2", name="Check vacio", is_active=True)
        study_off = models.Study(code="CHK3", name="Check inactivo", is_active=False)
        db.add_all([study, study2, study_off])
        db.commit()
        for s in (study, study2, study_off):
            db.refresh(s)

        print("[1] Catalogo")
        catalogo = {t["key"]: t for t in main.whatsapp_templates_catalog(current_user=admin)}
        cfg = catalogo.get("in_home_beta_385")
        check(cfg is not None, "in_home_beta_385 esta en el catalogo")
        check(cfg and cfg["language"] == "es", "idioma 'es'")
        check(cfg and cfg["params"] == ["encuestada", "encuestador", "hora_asignada"],
              "parametros = encuestada, encuestador, hora_asignada")
        check(cfg and "{{hora_asignada}}" in (cfg["body"] or ""), "el cuerpo usa {{hora_asignada}}")
        check(cfg and "producto 358" in (cfg["body"] or ""), "el cuerpo menciona el producto 358")
        check(cfg and "Az-Marketing" in (cfg["body"] or ""), "el cuerpo arranca con Az-Marketing")
        check(cfg and cfg["single_eligible"] is True, "in_home_beta_385 es elegible 1x1")
        check(catalogo.get("bono_final", {}).get("single_eligible") is False, "bono_final NO es elegible 1x1")
        check(catalogo.get("shampo_segundo", {}).get("single_eligible") is True, "shampo_segundo es elegible 1x1")

        cfg729 = catalogo.get("fatiga_729_r3")
        check(cfg729 is not None, "fatiga_729_r3 esta en el catalogo")
        check(cfg729 and cfg729["name"] == "fatiga_729_r3", "fatiga_729_r3 name = fatiga_729_r3")
        check(cfg729 and cfg729["language"] == "es", "fatiga_729_r3 idioma 'es'")
        check(cfg729 and cfg729["params"] == ["nombre_entrevistada", "encuestador", "hora_agendada"],
              "fatiga_729_r3 parametros = nombre_entrevistada, encuestador, hora_agendada")
        check(cfg729 and "shampoo 729" in (cfg729["body"] or ""), "fatiga_729_r3 el cuerpo menciona shampoo 729")
        check(cfg729 and "{{hora_agendada}}" in (cfg729["body"] or ""), "fatiga_729_r3 el cuerpo usa {{hora_agendada}}")
        check(cfg729 and "{{nombre_entrevistada}}" in (cfg729["body"] or ""),
              "fatiga_729_r3 el cuerpo usa {{nombre_entrevistada}}")
        check(cfg729 and cfg729["single_eligible"] is True, "fatiga_729_r3 es elegible 1x1")

        print("[2] Render con hora_asignada")
        body = main._wa_render_template_body(
            "in_home_beta_385",
            {"encuestada": "Ana", "encuestador": "Luis", "hora_asignada": "3:30 pm"},
        )
        check(body is not None and "Ana" in body and "Luis" in body and "3:30 pm" in body,
              "sustituye encuestada / encuestador / hora_asignada")
        check(body is not None and "{{" not in body, "no deja variables sin sustituir")

        print("[2b] Render con hora_agendada")
        body729 = main._wa_render_template_body(
            "fatiga_729_r3",
            {"nombre_entrevistada": "Ana", "encuestador": "Luis", "hora_agendada": "3:30 pm"},
        )
        check(body729 is not None and "Ana" in body729 and "Luis" in body729 and "3:30 pm" in body729,
              "sustituye nombre_entrevistada / encuestador / hora_agendada")
        check(body729 is not None and "{{" not in body729, "fatiga_729_r3 no deja variables sin sustituir")

        print("[3] PUT/GET single-templates")
        main.set_study_single_templates(
            study.id,
            main.StudySingleTemplatesUpdate(template_keys=["manana_3", "in_home_beta_385", "fatiga_729_r3", "bono_final", "manana_3"]),
            db=db,
            current_user=admin,
        )
        keys = main.get_study_single_templates(study.id, db=db, current_user=admin)["single_template_keys"]
        check(keys == ["manana_3", "in_home_beta_385", "fatiga_729_r3"], f"solo elegibles, sin duplicados -> {keys}")
        check(main._study_template_keys(db, study.id) == [], "no toca el conjunto masivo")

        print("[3b] El masivo acepta in_home_beta_385")
        main.set_study_templates(
            study.id,
            main.StudyTemplatesUpdate(template_keys=["in_home_beta_385"]),
            db=db,
            current_user=admin,
        )
        check(main._study_template_keys(db, study.id) == ["in_home_beta_385"],
              "in_home_beta_385 conectada al masivo")
        check(sorted(main._study_single_template_keys(db, study.id)) == ["fatiga_729_r3", "in_home_beta_385", "manana_3"],
              "la conexion masiva no toca el conjunto 1x1")

        print("[4] Resolucion del destino")
        call = models.Call(study_id=study.id, phone_number="3001234567", person_name="Ana Gomez",
                           collection_time="3:30 pm")
        db.add(call)
        db.commit()
        db.refresh(call)
        by_call = main.whatsapp_single_templates_for_target(call_id=call.id, db=db, current_user=admin)
        check(by_call["study_id"] == study.id, "resuelve el estudio por call_id")
        by_phone = main.whatsapp_single_templates_for_target(phone_number="3001234567", db=db, current_user=admin)
        check(by_phone["study_id"] == study.id, "resuelve el estudio por telefono")
        by_study = main.whatsapp_single_templates_for_target(study_id=study.id, db=db, current_user=admin)
        check(by_study["study_id"] == study.id, "resuelve el estudio por study_id")
        check(main.whatsapp_single_templates_for_target(phone_number="3110000000", db=db, current_user=admin)["study_id"] is None,
              "telefono sin estudio -> sin estudio")

        print("[5] Validacion del envio 1x1")
        main._wa_require_send_window = lambda db, user: None
        main._wa_graph_request = lambda path, payload: {"messages": [{"id": "wamid.TEST"}]}

        call2 = models.Call(study_id=study2.id, phone_number="3009998888", person_name="Beto")
        db.add(call2)
        db.commit()
        db.refresh(call2)

        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(call_id=call.id, template_key="shampo_segundo"),
                db=db, current_user=admin,
            )
            check(False, "plantilla no conectada deberia ser 403")
        except HTTPException as e:
            check(e.status_code == 403, "plantilla no conectada al estudio -> 403")

        try:
            main.whatsapp_send_template(
                main.WhatsAppSendTemplateRequest(call_id=call2.id, template_key="manana_3"),
                db=db, current_user=admin,
            )
            check(False, "estudio sin plantillas 1x1 deberia ser 403")
        except HTTPException as e:
            check(e.status_code == 403, "estudio sin plantillas 1x1 -> 403")

        res = main.whatsapp_send_template(
            main.WhatsAppSendTemplateRequest(call_id=call.id, template_key="in_home_beta_385"),
            db=db, current_user=admin,
        )
        check(res.get("wa_status") == "sent" and res.get("template_key") == "in_home_beta_385",
              "plantilla conectada se envia (envio simulado)")

        res729 = main.whatsapp_send_template(
            main.WhatsAppSendTemplateRequest(call_id=call.id, template_key="fatiga_729_r3"),
            db=db, current_user=admin,
        )
        check(res729.get("wa_status") == "sent" and res729.get("template_key") == "fatiga_729_r3",
              "fatiga_729_r3 conectada se envia (envio simulado)")

        print("[6] Sembrado unico")
        db.query(models.StudySingleTemplate).delete()
        db.commit()
        sembrados = main._seed_single_templates(db)
        check(sembrados == 2, f"siembra solo los 2 estudios activos -> {sembrados}")
        check(sorted(main._study_single_template_keys(db, study.id)) == ["manana_3", "shampo_primer", "shampo_segundo"],
              "el estudio activo queda con las 3 historicas")
        check(main._study_single_template_keys(db, study_off.id) == [], "el estudio inactivo no se siembra")
        check(main._seed_single_templates(db) == 0, "un segundo arranque no vuelve a sembrar")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} falla(s).")
        sys.exit(1)
    print("\nTodo OK.")
