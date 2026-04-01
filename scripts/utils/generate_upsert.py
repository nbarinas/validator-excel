import sqlite3

def export_to_upsert_sql(db_filename, sql_filename):
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(calls)")
    # Get all columns EXCEPT 'segundo_codigo'
    cols_info = cursor.fetchall()
    cols = []
    col_indices = []
    
    for i, info in enumerate(cols_info):
        col_name = info[1]
        if col_name != 'segundo_codigo':
            cols.append(col_name)
            col_indices.append(i)
            
    col_str = '`, `'.join(cols)
    
    cursor.execute("SELECT * FROM calls")
    rows = cursor.fetchall()
    
    with open(sql_filename, 'w', encoding='utf-8') as f:
        f.write('-- Exportacion ON DUPLICATE UPDATE de la tabla `calls`\n')
        f.write(f'-- Total de registros a actualizar/insertar: {len(rows)}\n\n')
        f.write('SET FOREIGN_KEY_CHECKS = 0;\n\n')
        
        batch_size = 50
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            
            f.write(f'INSERT INTO `calls` (`{col_str}`) VALUES\n')
            
            val_strings = []
            for row in batch:
                formatted_vals = []
                # Only iterate over the indices we care about
                for idx in col_indices:
                    val = row[idx]
                    if val is None:
                        formatted_vals.append('NULL')
                    elif isinstance(val, (int, float)):
                        formatted_vals.append(str(val))
                    else:
                        val_str = str(val).replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
                        formatted_vals.append(f"'{val_str}'")
                
                val_strings.append('    (' + ', '.join(formatted_vals) + ')')
            
            f.write(',\n'.join(val_strings))
            
            f.write('\nON DUPLICATE KEY UPDATE\n')
            
            update_clauses = [f'`{col}` = VALUES(`{col}`)' for col in cols if col != 'id']
            f.write(',\n'.join(update_clauses) + ';\n\n')
            
        f.write('SET FOREIGN_KEY_CHECKS = 1;\n')
    conn.close()

export_to_upsert_sql('az_marketing.db', 'calls_reparadas_para_produccion.sql')
print('Script SQL generado exitosamente EXCLUYENDO segundo_codigo.')
