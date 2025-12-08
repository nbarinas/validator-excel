from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import pandas as pd
import io
import os
from typing import List

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Determine the directory of the current file to build absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Frontend is sibling to backend
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


def normalize_columns(df, manual_mapping=None):
    # If manual mapping is provided, apply it strictly
    if manual_mapping:
        rename_map = {v: k for k, v in manual_mapping.items() if v}
        missing = []
        for std, actual in manual_mapping.items():
            if actual and actual not in df.columns:
                 pass 
            elif not actual:
                 missing.append(std)
        if missing:
             return df, missing
        return df.rename(columns=rename_map), []

    # Map expected roughly to standard names if needed, or just strict check
    # User asked for: Id, Ciudad, Numero de celular, Codigo, and now Nombre (Enc_1)
    # We will try to find these columns case-insensitive
    cols = {str(c).strip().lower(): c for c in df.columns}
    
    # Required keys map to LIST of possible aliases
    required_map = {
        "Id": ["id", "censo", "identifier"],
        "Ciudad": ["ciudad", "ciu", "city"],
        "Numero de celular": ["numero de celular", "celular", "enc_3", "movil"],
        "Codigo": ["codigo", "cod", "code"],
        "Nombre": ["enc_1", "nombre", "encuestada", "name"],
        "Encuestador": ["encues_1"],
        "Nse": ["nse", "estrato", "nivel", "capa", "socioeconomico", "seg"],
        "Duration": ["duration", "duracion", "tiempo", "time"]
    }
    
    mapping = {}
    missing = []
    
    for standard_name, aliases in required_map.items():
        found = False
        for alias in aliases:
            if alias in cols:
                mapping[cols[alias]] = standard_name
                found = True
                break
        
        if not found:
            missing.append(standard_name)
    
    if missing:
        # If headers are completely different, this might fail.
        # Let's hope the user provides compliant files or we will error out with helpful message.
        return df, missing
        
    return df.rename(columns=mapping), []

@app.post("/validate")
async def validate_files(
    files: List[UploadFile] = File(...),
    mapping: str = Form(None)
):
    if len(files) != 2:
        raise HTTPException(status_code=400, detail="Exactly 2 files are required for Validation.")

    dfs = []
    filenames = []
    
    for file in files:
        content = await file.read()
        try:
            df = pd.read_excel(io.BytesIO(content))
            dfs.append(df)
            filenames.append(file.filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file {file.filename}: {str(e)}")

    # Parse mapping if provided
    manual_maps = [None, None]
    if mapping:
        try:
            parsed_map = json.loads(mapping)
            manual_maps[0] = parsed_map.get("file1")
            manual_maps[1] = parsed_map.get("file2")
        except:
            pass

    # Column Normalization
    df1, missing1 = normalize_columns(dfs[0], manual_maps[0])
    df2, missing2 = normalize_columns(dfs[1], manual_maps[1])

    if missing1 or missing2:
        return JSONResponse(
            status_code=409,
            content={
                "status": "missing_columns",
                "detail": "Could not auto-detect all required columns.",
                "file_1_name": filenames[0],
                # Return columns as simple strings to be JSON serializable
                "file_1_columns": [str(c) for c in dfs[0].columns],
                "missing_1": missing1,
                "file_2_name": filenames[1],
                "file_2_columns": [str(c) for c in dfs[1].columns],
                "missing_2": missing2,
                "required_fields": ["Id", "Ciudad", "Numero de celular", "Codigo", "Nombre", "Nse", "Duration", "Encuestador"]
            }
        )

    # --- CATEGORIZATION LOGIC ---
    
    # helper for cleaning strings
    def clean(s):
        return str(s).strip().lower()

    # NSE Normalization Helper
    def normalize_nse(val):
        s = clean(val)
        # 2 / BA / Baja Alta
        if s in ['2', 'dos', 'ba', 'baja alta', 'bajaalta']:
            return 'Baja Alta'
        # 3 / Tres / Media Baja / NSE 3
        if s in ['3', 'tres', 'media baja', 'nse 3', 'nse3', 'mediabaja']:
            return 'Media Baja'
        # 4 / Cuatro / Media Tipica
        if s in ['4', 'cuatro', 'media tipica', 'mediatipica', 'media típica']:
            return 'Media Típica'
        return s.title() # Return capitalized original if not matched

    # 1. ELIMINAR (Duplicates)
    # We identify duplicates BEFORE dropping them for the merge
    eliminar_rows = []
    
    # Duplicates in File 1
    dup1 = df1[df1.duplicated(subset=['Id'], keep=False)]
    if not dup1.empty:
        # Add to eliminar list. We flag them as "Duplicado en R1"
        for _, row in dup1.iterrows():
            r = row.to_dict()
            r['Motivo'] = "Duplicada en R1"
            eliminar_rows.append(r)
            
    # Duplicates in File 2
    dup2 = df2[df2.duplicated(subset=['Id'], keep=False)]
    if not dup2.empty:
        for _, row in dup2.iterrows():
            r = row.to_dict()
            r['Motivo'] = "Duplicada en RF"
            eliminar_rows.append(r)

    # Now drop duplicates to allow clean merge (keeping first as requested for the comparison)
    df1_clean = df1.drop_duplicates(subset=['Id'], keep='first')
    df2_clean = df2.drop_duplicates(subset=['Id'], keep='first')

    # --- INTERVIEWER METRICS ---
    def get_interviewer_stats(df, suffix):
        tmp = df.copy()
        if 'Encuestador' not in tmp.columns:
            tmp['Encuestador'] = 'Desconocido'
            
        # Specific Normalization Map
        name_map = {
            "armando zararte": "Armando Zarate",
            "fermada ramos": "Fernanda Ramos",
            "fermamda ramos": "Fernanda Ramos",
            "fernada ramos": "Fernanda Ramos",
            "fernanada ramos": "Fernanda Ramos",
            "fernanda": "Fernanda Ramos",
            "ingrid codoba": "Ingrid Cordoba",
            "johana benitez": "Johana Benitez", # Ensure standard
            "juan moreno": "Juan Moreno",
            "laura osorio": "Laura Osorio",
            "milena zarate": "Milena Zarate",
            "yraima rey": "Yraima Rey"
        }
        
        def norm_name(n):
            s = str(n).strip().lower()
            # Direct mapping
            if s in name_map:
                return name_map[s]
            # Fallback: Title case
            return s.title()

        tmp['Encuestador_Norm'] = tmp['Encuestador'].apply(norm_name)
        
        # Duration
        col_dur = 'Duration'
        if col_dur not in tmp.columns:
            tmp[col_dur] = 0
        
        # Convert to numeric
        tmp[col_dur] = pd.to_numeric(tmp[col_dur], errors='coerce').fillna(0)
        
        # Convert Excel Serial Time to Minutes if it looks like serial time (< 1 usually, or just assuming it is)
        # User example: 0.013576 (~19.5 min). 
        # Logic: If max duration is small (< 5?), x 1440. If > 5, assume minutes already?
        # Safe bet: User specifically mentioned "toma formato general...". Assuming ALL valid durations are Excel Time.
        # But if some files are already in minutes (e.g. 20, 30), multiplying by 1440 would be huge (28800 min).
        # Heuristic: If mean < 1.0, assume Days -> Minutes.
        
        mean_val = tmp[col_dur].mean()
        if 0 < mean_val < 1.0:
            tmp[col_dur] = tmp[col_dur] * 1440
        
        # Calculate Global Mean (excluding 0s) for Alert Baseline
        global_mean = tmp[tmp[col_dur] > 0][col_dur].mean() if not tmp.empty else 0
        
        stats = tmp.groupby('Encuestador_Norm').agg(
            Count=('Id', 'count'),
            Avg_Duration=('Duration', 'mean')
        ).reset_index()
        
        # Add Alert Column
        def get_alert(row):
            if row['Count'] == 0: return ""
            avg = row['Avg_Duration']
            if global_mean > 0:
                if avg < (global_mean * 0.4): # Less than 40% of average
                    return "Muy Bajo"
                if avg > (global_mean * 1.8): # More than 180% of average (approx 2x)
                    return "Muy Alto"
            return "Normal"

        stats[f'Alerta_{suffix}'] = stats.apply(get_alert, axis=1)
        
        return stats.rename(columns={'Count': f'Cantidad_{suffix}', 'Avg_Duration': f'Tiempo_{suffix}'})

    stats_r1 = get_interviewer_stats(df1_clean, 'R1')
    stats_rf = get_interviewer_stats(df2_clean, 'RF')
    
    interviewer_stats = pd.merge(stats_r1, stats_rf, on='Encuestador_Norm', how='outer').fillna({'Cantidad_R1':0, 'Cantidad_RF':0, 'Tiempo_R1':0, 'Tiempo_RF':0, 'Alerta_R1':'-', 'Alerta_RF':'-'})
    interviewer_stats['Cantidad_R1'] = interviewer_stats['Cantidad_R1'].astype(int)
    interviewer_stats['Cantidad_RF'] = interviewer_stats['Cantidad_RF'].astype(int)
    interviewer_stats['Tiempo_R1'] = interviewer_stats['Tiempo_R1'].round(2)
    interviewer_stats['Tiempo_RF'] = interviewer_stats['Tiempo_RF'].round(2)
    
    interviewer_stats = interviewer_stats.rename(columns={
        'Encuestador_Norm': 'Encuestador',
        'Tiempo_R1': 'Tiempo Promedio R1 (Min)',
        'Tiempo_RF': 'Tiempo Promedio RF (Min)',
        'Alerta_R1': 'Alerta Tiempos R1',
        'Alerta_RF': 'Alerta Tiempos RF'
    })

    # Merge
    merged = pd.merge(df1_clean, df2_clean, on='Id', suffixes=('_1', '_2'), how='outer', indicator=True)

    # 2. CAÍDAS (Only in R1)
    caidas_df = merged[merged['_merge'] == 'left_only'].copy()
    # Rename columns back to generic (remove _1)
    rename_cols = {c: c[:-2] for c in caidas_df.columns if c.endswith('_1')}
    caidas_df = caidas_df.rename(columns=rename_cols)
    # Filter to relevant columns if possible, or keep all
    
    # 3. ELIMINAR (Only in RF) - Append to existing eliminar list
    only_rf = merged[merged['_merge'] == 'right_only'].copy()
    if not only_rf.empty:
        for _, row in only_rf.iterrows():
            # Construct row dict. Columns have _2 suffix.
            r = {}
            for col in only_rf.columns:
                if col.endswith('_2'):
                    r[col[:-2]] = row[col]
                elif col == 'Id':
                    r['Id'] = row['Id']
            r['Motivo'] = "Sobra en RF"
            eliminar_rows.append(r)
            
    eliminar_df = pd.DataFrame(eliminar_rows)
    # Reorder Eliminar: Put 'Motivo' at the end
    if not eliminar_df.empty and 'Motivo' in eliminar_df.columns:
        cols = [c for c in eliminar_df.columns if c != 'Motivo'] + ['Motivo']
        eliminar_df = eliminar_df[cols]

    # ... (rest of code) ...
    # This replace_file_content modifies the early part of validate_files.
    # I need to ensure I don't break the flow. 
    # I will target the lines from "1. ELIMINAR" down to "eliminar_df = ..."
    
    # AND I need to update the Speech generation logic which uses str.contains('RF')/('R1').
    # I can do that in a second replace or try to cover all if they are close (they are not close enough).
    # I will do two replaces. First the creation logic.


    # 4. BUENOS vs SEMI BUENOS (Common)
    common = merged[merged['_merge'] == 'both'].copy()
    
    buenos_rows = []
    semi_buenos_rows = []
    
    for _, row in common.iterrows():
        reasons = []
        
        # Check Ciudad
        if clean(row['Ciudad_1']) != clean(row['Ciudad_2']):
            reasons.append(f"Cambia de Ciudad: {row['Ciudad_1']} vs {row['Ciudad_2']}")
            
        # Check Celular
        if clean(row['Numero de celular_1']) != clean(row['Numero de celular_2']):
            reasons.append(f"Cambia de Numero: {row['Numero de celular_1']} vs {row['Numero de celular_2']}")
            
        # Check Nombre
        if clean(row['Nombre_1']) != clean(row['Nombre_2']):
            reasons.append(f"Cambia de Nombre: {row['Nombre_1']} vs {row['Nombre_2']}")
            
        # Check Codigo (Should be DIFFERENT)
        if clean(row['Codigo_1']) == clean(row['Codigo_2']):
            reasons.append(f"No es el Cod (es igual): {row['Codigo_1']}")

        # Check NSE
        val_nse1 = row.get('Nse_1', '')
        val_nse2 = row.get('Nse_2', '')
        if normalize_nse(val_nse1) != normalize_nse(val_nse2):
             reasons.append(f"Cambia de NSE: {val_nse1} vs {val_nse2}")
            
        # Base Row
        base_row = {}
        for col in df1_clean.columns:
            if col in ['Id']:
                base_row[col] = row[col]
            else:
                if f"{col}_1" in row:
                    base_row[col] = row[f"{col}_1"]
        
        # ALWAYS capture RF context for Summary (and report)
        base_row['Codigo_RF'] = row.get('Codigo_2', '')
        base_row['Ciudad_RF'] = row.get('Ciudad_2', '')
        base_row['Celular_RF'] = row.get('Numero de celular_2', '')
        base_row['Nse_RF'] = row.get('Nse_2', '')

        if reasons:
            base_row['Motivo'] = "; ".join(reasons)
            semi_buenos_rows.append(base_row)
        else:
            buenos_rows.append(base_row)
            
    buenos_df = pd.DataFrame(buenos_rows)
    semi_buenos_df = pd.DataFrame(semi_buenos_rows)
    
    # Reorder Semi Buenos: Put 'Motivo' at the end
    if not semi_buenos_df.empty and 'Motivo' in semi_buenos_df.columns:
        cols = [c for c in semi_buenos_df.columns if c != 'Motivo'] + ['Motivo']
        semi_buenos_df = semi_buenos_df[cols]
        
    # --- BUILD SUMMARY DATAFRAME ---
    # We want specific ordering: 
    # 1. Buenas (Aggregated by Ciudad, Nse ONLY)
    # 2. Por arreglar (Semi Buenos) (Aggregated by Ciudad, Nse, Codes)
    # 3. Caídas (Aggregated by Ciudad, Nse, Codes)
    # 4. Eliminar (Aggregated by Ciudad, Tipo)

    final_summary_parts = []

    # 1. BUENAS
    if not buenos_df.empty:
        # Create temp df for aggregation
        temp_buenas = pd.DataFrame()
        temp_buenas['Ciudad'] = buenos_df['Ciudad'].apply(clean)
        temp_buenas['Nse'] = buenos_df['Nse'].apply(normalize_nse) if 'Nse' in buenos_df.columns else ''
        temp_buenas['Tipo'] = 'Buenas'
        
        # Group
        grp_buenas = temp_buenas.groupby(['Ciudad', 'Nse', 'Tipo']).size().reset_index(name='Cantidad')
        # Add missing columns for schema alignment
        grp_buenas['Codigo_R1'] = '-'
        grp_buenas['Codigo_RF'] = '-'
        
        final_summary_parts.append(grp_buenas)

    # 2. POR ARREGLAR (Semi Buenos)
    if not semi_buenos_df.empty:
        temp_semi = pd.DataFrame()
        temp_semi['Ciudad'] = semi_buenos_df['Ciudad'].apply(clean)
        temp_semi['Nse'] = semi_buenos_df['Nse'].apply(normalize_nse) if 'Nse' in semi_buenos_df.columns else ''
        temp_semi['Codigo_R1'] = semi_buenos_df['Codigo'].apply(clean) if 'Codigo' in semi_buenos_df.columns else ''
        temp_semi['Codigo_RF'] = semi_buenos_df['Codigo_RF'].apply(clean) if 'Codigo_RF' in semi_buenos_df.columns else ''
        temp_semi['Tipo'] = 'Por arreglar'
        
        grp_semi = temp_semi.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        final_summary_parts.append(grp_semi)
            
    # 3. CAÍDAS
    if not caidas_df.empty:
        temp_caidas = pd.DataFrame()
        temp_caidas['Ciudad'] = caidas_df['Ciudad'].apply(clean)
        temp_caidas['Nse'] = caidas_df['Nse'].apply(normalize_nse) if 'Nse' in caidas_df.columns else ''
        temp_caidas['Codigo_R1'] = caidas_df['Codigo'].apply(clean) if 'Codigo' in caidas_df.columns else ''
        temp_caidas['Codigo_RF'] = '-'
        temp_caidas['Tipo'] = 'Caídas'
        
        grp_caidas = temp_caidas.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        final_summary_parts.append(grp_caidas)

    # 4. ELIMINAR
    if not eliminar_df.empty:
        temp_elim = pd.DataFrame()
        temp_elim['Ciudad'] = eliminar_df['Ciudad'].apply(clean)
        temp_elim['Nse'] = '-'
        temp_elim['Codigo_R1'] = '-'
        temp_elim['Codigo_RF'] = '-'
        
        # Determine subtype
        def get_elim_type(row):
            m = str(row.get('Motivo', ''))
            return 'Eliminar RF' if 'RF' in m else 'Eliminar R1'
            
        temp_elim['Tipo'] = eliminar_df.apply(get_elim_type, axis=1)
        
        grp_elim = temp_elim.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        final_summary_parts.append(grp_elim)

    # Concat all parts
    if final_summary_parts:
        summary_pivot = pd.concat(final_summary_parts, ignore_index=True)
        # Ensure column order
        summary_pivot = summary_pivot[['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo', 'Cantidad']]
    else:
        summary_pivot = pd.DataFrame(columns=['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo', 'Cantidad'])

    # --- SPEECH GENERATION ---
    study_name = "Estudio"
    if filenames:
        # Try to get a clean name from the first filename
        # Remove extension
        base = os.path.splitext(filenames[0])[0]
        study_name = base

    speech_lines = []
    speech_lines.append(f"Saludos, de estudio {study_name}")
    speech_lines.append("")

    # 1. Terminamos efectivas bien
    if not buenos_df.empty:
        good_counts = buenos_df.groupby('Ciudad').size()
        good_str = ", ".join([f"{city}: {count}" for city, count in good_counts.items()])
        speech_lines.append(f"Terminamos efectivas bien de {good_str}.")
    else:
        speech_lines.append("No hay efectivas bien.")

    # 2. Favor corregir (Semi Buenos)
    # "favor corregir xxx que de los censos ... y respectivos r con el error"
    if not semi_buenos_df.empty:
        total_fix = len(semi_buenos_df)
        speech_lines.append(f"Favor corregir {total_fix} registros.")
        # List details as requested: "valores de censos a corregir y el porque"
        speech_lines.append(f"Favor corregir {total_fix} registros:")
        for _, row in semi_buenos_df.iterrows():
             # "Censo X: Motivo"
             speech_lines.append(f"  - Censo {row['Id']}: {row['Motivo']}")

    # 3. Caídas (Por ciudad solamente)
    if not caidas_df.empty:
        drop_counts = caidas_df.groupby('Ciudad').size()
        drop_str = ", ".join([f"{city}: {count}" for city, count in drop_counts.items()])
        speech_lines.append(f"Caídas: {drop_str}.")
    
    # 4. Eliminar
    # Deduplicate IDs for speech and include reason
    if not eliminar_df.empty:
        # Filter groups
        # RF: "Sobra en RF" or "Duplicada en RF"
        elim_rf = eliminar_df[eliminar_df['Motivo'].astype(str).str.contains('RF', na=False)]
        # R1: "Duplicada en R1"
        elim_r1 = eliminar_df[eliminar_df['Motivo'].astype(str).str.contains('R1', na=False)]
        
        # Helper to format list: "ID (Reason)" unique
        def format_elim_list(df):
            # deduplicate by ID, keeping first reason found (usually same reason for duplicates)
            deduped = df.drop_duplicates(subset=['Id'])
            items = []
            for _, row in deduped.iterrows():
                items.append(f"{row['Id']} ({row['Motivo']})")
            return ", ".join(items)

        if not elim_rf.empty:
            count = len(elim_rf.drop_duplicates(subset=['Id']))
            ids_str = format_elim_list(elim_rf)
            speech_lines.append(f"Favor eliminar de las RF ({count} casos únicos): Censos {ids_str}.")
            
        if not elim_r1.empty:
            count = len(elim_r1.drop_duplicates(subset=['Id']))
            ids_str = format_elim_list(elim_r1)
            speech_lines.append(f"Favor eliminar de R1 ({count} casos únicos): Censos {ids_str}.")

    speech_text = "\n".join(speech_lines)


    # Generate Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write Summary Table
        if not summary_pivot.empty:
            summary_pivot.to_excel(writer, sheet_name='Resumen', index=False)
        else:
             pd.DataFrame({'Info': ['Sin datos']}).to_excel(writer, sheet_name='Resumen', index=False)
        
        # Write Speech below Summary
        # We need to access the workbook/sheet to write text at specific position
        # Pandas allows writing to startrow/startcol but assumes DataFrame.
        # We can write a dataframe with the speech, or hook into the sheet.
        # Simplest: Write Summary, then write Speech DF below it.
        
        start_row_speech = len(summary_pivot) + 4
        speech_df = pd.DataFrame([l for l in speech_lines], columns=["Speech Draft"])
        speech_df.to_excel(writer, sheet_name='Resumen', startrow=start_row_speech, index=False, header=False)

        # Write Interviewer Metrics
        start_row_metrics = start_row_speech + len(speech_lines) + 2
        if not interviewer_stats.empty:
            interviewer_stats.to_excel(writer, sheet_name='Resumen', startrow=start_row_metrics, index=False)


        if not buenos_df.empty:
            buenos_df.to_excel(writer, sheet_name='Buenas', index=False)
        else:
            pd.DataFrame({'Info': ['No hay registros perfectos']}).to_excel(writer, sheet_name='Buenas', index=False)
            
        if not semi_buenos_df.empty:
            semi_buenos_df.to_excel(writer, sheet_name='Por arreglar', index=False)
        else:
             pd.DataFrame({'Info': ['No hay registros por arreglar']}).to_excel(writer, sheet_name='Por arreglar', index=False)
             
        if not caidas_df.empty:
            cols_to_save = [c for c in caidas_df.columns if not c.endswith(('_2', '_merge'))]
            caidas_df[cols_to_save].to_excel(writer, sheet_name='Caidas', index=False)
        else:
            pd.DataFrame({'Info': ['No hay caídas']}).to_excel(writer, sheet_name='Caidas', index=False)
            
        if not eliminar_df.empty:
            eliminar_df.to_excel(writer, sheet_name='Eliminar', index=False)
        else:
            pd.DataFrame({'Info': ['No hay registros para eliminar']}).to_excel(writer, sheet_name='Eliminar', index=False)

    output.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="Reporte_{study_name}.xlsx"'
    }
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.post("/fatiga")
async def fatiga_check(files: List[UploadFile] = File(...), mapping: str = Form(None)):
    if not (2 <= len(files) <= 10):
         raise HTTPException(status_code=400, detail="Fatiga mode requires between 2 and 10 files.")

    dfs = []
    filenames = []
    
    for file in files:
        content = await file.read()
        try:
            df = pd.read_excel(io.BytesIO(content))
            dfs.append(df)
            filenames.append(file.filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file {file.filename}: {str(e)}")

    # Parse mapping if provided (Assuming mapping structure handles list? Logic in frontend might need verification if it sends map for >2 files. 
    # For now, simplistic manual map or auto-detect.)
    # The current frontend mapping modal supports file1 and file2. 
    # Fatigue might imply standard headers usually.
    # We'll use auto-detect. N-file mapping UI is a complexity user didn't request yet.
    
    # helper for cleaning strings
    def clean(s):
        return str(s).strip().lower()
        
    # Helper for NSE
    def normalize_nse(val):
        s = clean(val)
        if s in ['2', 'dos', 'ba', 'baja alta', 'bajaalta']: return 'Baja Alta'
        if s in ['3', 'tres', 'media baja', 'nse 3', 'nse3', 'mediabaja']: return 'Media Baja'
        if s in ['4', 'cuatro', 'media tipica', 'mediatipica', 'media típica']: return 'Media Típica'
        return s.title()
    
    # Normalize all
    norm_dfs = []
    for i, df in enumerate(dfs):
        # We don't have per-file valid mapping from existing UI for files > 2.
        # Passing None for manual map safely.
        ndf, missing = normalize_columns(df, None)
        if missing:
             return JSONResponse(
                status_code=409,
                content={
                    "status": "missing_columns",
                    "detail": f"Missing columns in {filenames[i]}: {missing}",
                    "file_1_name": filenames[0], # Reuse format so UI might catch it, though specific UI update needed for N files 409. 
                                                 # For now fallback to simple error if headers bad.
                    "file_1_columns": [str(c) for c in df.columns],
                    "missing_1": missing,
                    # Hack: To prevent crash if UI expects file_2
                    "file_2_name": filenames[1] if len(filenames) > 1 else "",
                    "file_2_columns": [],
                    "missing_2": [],
                    "required_fields": ["Id", "Ciudad", "Numero de celular", "Codigo", "Nombre", "Nse", "Duration", "Encuestador"]
                }
            )
        # Deduplicate IDs in each file (keeping first)
        ndf = ndf.drop_duplicates(subset=['Id'], keep='first')
        norm_dfs.append(ndf)

    # MERGE LOGIC
    # Base is File 1 (R1)
    # We merge everything onto a master list of IDs?
    # Or strict Left Join on R1? 
    # User: "si esta en A la r1 todas las demas deben estar en A y sino error".
    # User: "si en r1 y r2 esta pero para rf no esta caida".
    # This implies we need to track everything.
    
    from functools import reduce
    
    # Rename columns to avoid collision: suffix _0, _1, ...
    renamed_dfs = []
    for i, df in enumerate(norm_dfs):
        # Rename all except Id
        cols = {c: f"{c}_{i}" for c in df.columns if c != 'Id'}
        renamed_dfs.append(df.rename(columns=cols))
        
    # Full Outer Join to catch "Sobra" (Eliminar) vs "Caída"
    merged = reduce(lambda left, right: pd.merge(left, right, on='Id', how='outer'), renamed_dfs)
    
    buenos_rows = []
    por_arreglar_rows = []
    caidas_rows = []
    eliminar_rows = []
    
    # Iterate
    for _, row in merged.iterrows():
        # Get R1 Data
        id_val = row['Id']
        in_r1 = pd.notna(row.get('Codigo_0')) # Check existence via a required column like Codigo
        
        # Base info from R1 (or first available if missing in R1)
        base_info = {}
        # Find first existing file index for this ID to get Ciudad/NSE info
        first_idx = -1
        for i in range(len(files)):
            if pd.notna(row.get(f'Codigo_{i}')):
                first_idx = i
                break
        
        if first_idx != -1:
            base_info['Ciudad'] = row.get(f'Ciudad_{first_idx}', '')
            base_info['Nse'] = row.get(f'Nse_{first_idx}', '')
            base_info['Id'] = id_val
            base_info['Codigo_R1'] = row.get(f'Codigo_0', '') # Might be NaN if not in R1
            # RF Code (Last File)
            last_idx = len(files) - 1
            base_info['Codigo_RF'] = row.get(f'Codigo_{last_idx}', '')
        else:
            continue # Should not happen

        # Checks
        if not in_r1:
            # Not in R1 -> ELIMINAR ("Sobra")
            # Determine where it appeared
            found_in = []
            for i in range(1, len(files)):
                if pd.notna(row.get(f'Codigo_{i}')):
                    found_in.append(filenames[i])
            
            r = base_info.copy()
            r['Motivo'] = f"Sobra en {', '.join(found_in)}"
            eliminar_rows.append(r)
            continue
            
        # In R1. Check Valid Flow.
        # 1. Existence in subsequent files
        # 2. Code Consistency
        
        error_msgs = []
        is_caida = False
        
        # Check against all subsequent files
        # Code reference is R1
        ref_code = clean(row.get('Codigo_0'))
        
        for i in range(1, len(files)):
            # Check existence
            if pd.isna(row.get(f'Codigo_{i}')):
                # Missing in File i
                # If it's the LAST file, it's definitively a "Caída" (Conceptually).
                # User: "si en r1 y r2 esta pero para rf no esta caida"
                # If missing in intermediate? e.g. R1=Yes, R2=No, R3=Yes.
                # Usually that's a "Caída en R2" implies broken flow.
                error_msgs.append(f"Caída en {filenames[i]}")
                is_caida = True 
                # Should we continue checking? Usually once dropped, it's dropped.
            else:
                # Exists. Check Code.
                curr_code = clean(row.get(f'Codigo_{i}'))
                if curr_code != ref_code:
                    error_msgs.append(f"Error Codigo {filenames[i]}: {curr_code} vs R1({ref_code})")
        
        # Construct Result
        if is_caida:
             # Add to Caídas
             r = base_info.copy()
             r['Motivo'] = "; ".join([e for e in error_msgs if "Caída" in e])
             r['Tipo'] = 'Caídas'
             caidas_rows.append(r)
             # If there were ALSO code errors, maybe flag? Caída usually prioritizes.
        elif error_msgs:
            # Code Mismatches -> Por Arreglar
            r = base_info.copy()
            r['Motivo'] = "; ".join(error_msgs)
            r['Tipo'] = 'Por arreglar'
            por_arreglar_rows.append(r)
        else:
            # Perfect
            r = base_info.copy()
            r['Tipo'] = 'Buenas'
            buenos_rows.append(r)

    # Convert to DFs
    buenos_df = pd.DataFrame(buenos_rows)
    por_arreglar_df = pd.DataFrame(por_arreglar_rows)
    caidas_df = pd.DataFrame(caidas_rows)
    eliminar_df = pd.DataFrame(eliminar_rows)
    
    # --- SUMMARY ---
    summary_parts = []
    
    if not buenos_df.empty:
        g = buenos_df.copy()
        g['Ciudad'] = g['Ciudad'].apply(clean)
        g['Nse'] = g['Nse'].apply(normalize_nse)
        g['Codigo_R1'] = '-'
        g['Codigo_RF'] = '-'
        summ = g.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        summary_parts.append(summ)

    if not por_arreglar_df.empty:
        g = por_arreglar_df.copy()
        g['Ciudad'] = g['Ciudad'].apply(clean)
        g['Nse'] = g['Nse'].apply(normalize_nse)
        g['Codigo_R1'] = g['Codigo_R1'].apply(clean)
        g['Codigo_RF'] = g['Codigo_RF'].apply(clean)
        summ = g.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        summary_parts.append(summ)
        
    if not caidas_df.empty:
        g = caidas_df.copy()
        g['Ciudad'] = g['Ciudad'].apply(clean)
        g['Nse'] = g['Nse'].apply(normalize_nse)
        g['Codigo_R1'] = g['Codigo_R1'].apply(clean)
        g['Codigo_RF'] = '-' # Caída doesn't reach end usually, or inconsistent. Keep simple.
        
        # Caídas 'Motivo' contains which file. user might want split? 
        # For now aggregate all 'Caídas'.
        summ = g.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        summary_parts.append(summ)

    if not eliminar_df.empty:
        g = eliminar_df.copy()
        g['Ciudad'] = g['Ciudad'].apply(clean)
        g['Nse'] = '-'
        g['Codigo_R1'] = '-'
        g['Codigo_RF'] = '-'
        g['Tipo'] = 'Eliminar' # Simplify
        summ = g.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        summary_parts.append(summ)

    if summary_parts:
        summary_pivot = pd.concat(summary_parts, ignore_index=True)
    else:
        summary_pivot = pd.DataFrame(columns=['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo', 'Cantidad'])


    # --- SPEECH ---
    study_name = os.path.splitext(filenames[0])[0]
    speech_lines = [f"Saludos, de estudio {study_name}", "", "FATIGA CHECK REPORT", ""]
    
    # 1. Buenas
    if not buenos_df.empty:
        c = buenos_df['Ciudad'].apply(clean).value_counts()
        s = ", ".join([f"{k}: {v}" for k,v in c.items()])
        speech_lines.append(f"Terminamos efectivas bien de {s}.")
    
    # 2. Por arreglar
    if not por_arreglar_df.empty:
        speech_lines.append(f"Favor corregir {len(por_arreglar_df)} registros (Errores de Código).")
        # List IDs?
        ids = ", ".join(por_arreglar_df['Id'].astype(str).unique())
        speech_lines.append(f"  Censos: {ids}")

    # 3. Caídas
    if not caidas_df.empty:
        speech_lines.append(f"Caídas detectadas: {len(caidas_df)}.")
        # Summary by File?
        # TODO

    # 4. Eliminar
    if not eliminar_df.empty:
        speech_lines.append(f"Favor eliminar (Sobra en archivos secundarios): {len(eliminar_df)} casos.")
        ids = ", ".join(eliminar_df['Id'].astype(str).unique())
        speech_lines.append(f"  Censos: {ids}")
    
    
    # GENERATE EXCEL
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if not summary_pivot.empty:
            summary_pivot.to_excel(writer, sheet_name='Resumen', index=False)
        else: 
            pd.DataFrame({'Info': ['Sin datos']}).to_excel(writer, sheet_name='Resumen', index=False)
            
        # Write speech
        start_row = len(summary_pivot) + 4
        pd.DataFrame(speech_lines).to_excel(writer, sheet_name='Resumen', startrow=start_row, index=False, header=False)
        
        if not buenos_df.empty: buenos_df.to_excel(writer, sheet_name='Buenas', index=False)
        if not por_arreglar_df.empty: por_arreglar_df.to_excel(writer, sheet_name='Por arreglar', index=False)
        if not caidas_df.empty: caidas_df.to_excel(writer, sheet_name='Caidas', index=False)
        if not eliminar_df.empty: eliminar_df.to_excel(writer, sheet_name='Eliminar', index=False)

    output.seek(0)
    headers = {'Content-Disposition': 'attachment; filename="Reporte_Fatiga.xlsx"'}
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
