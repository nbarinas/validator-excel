import pandas as pd
import datetime
import re

df = pd.read_excel('este_es.xlsx')
# Columns: ['Nombre', 'Celular', 'Fecha', 'Estudio', 'fdgf']

df.columns = [str(c).strip() for c in df.columns]

sql_statements = []

for index, row in df.iterrows():
    nombre = str(row['Nombre']).replace("'", "''").strip() if pd.notna(row['Nombre']) else ''
    celular = str(row['Celular']).strip() if pd.notna(row['Celular']) else ''
    if celular.endswith('.0'): celular = celular[:-2]
    
    # Handle multiple phone numbers
    parts = re.split(r'[-\/]| y ', celular)
    phone1 = re.sub(r'\D', '', parts[0])[:20]
    phone2 = re.sub(r'\D', '', parts[1])[:20] if len(parts) > 1 else ''
    if not phone1 and phone2:
        phone1, phone2 = phone2, ''
    
    fecha = str(row['Fecha']).replace("'", "''").strip() if pd.notna(row['Fecha']) else ''
    estudio = str(row['Estudio']).replace("'", "''").strip() if pd.notna(row['Estudio']) else ''
    fdgf = str(row['fdgf']).replace("'", "''").strip() if pd.notna(row['fdgf']) else ''
    if fdgf.endswith('.0'): fdgf = fdgf[:-2]
    
    # Optional formatting for fecha if it contains 00:00:00
    if ' ' in fecha:
        fecha = fecha.split(' ')[0]
        
    subquery = f"(SELECT id FROM studies WHERE name = '{estudio}' LIMIT 1)"
    
    # Include extra_phone in INSERT
    sql = f"INSERT INTO calls (person_name, phone_number, extra_phone, implantation_date, code, study_id, status) VALUES ('{nombre}', '{phone1}', '{phone2}', '{fecha}', '{fdgf}', {subquery}, 'pending');"
    
    sql_statements.append(sql)

with open('inserts_desde_excel.sql', 'w', encoding='utf-8') as f:
    f.write('\n'.join(sql_statements))

print(f'Generated {len(sql_statements)} statements in inserts_desde_excel.sql')
