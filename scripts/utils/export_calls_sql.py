import sqlite3

def export_to_sql(db_filename, sql_filename):
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    
    # Pragma Info para nombres de columnas
    cursor.execute("PRAGMA table_info(calls)")
    columns_info = cursor.fetchall()
    col_names = [info[1] for info in columns_info]
    col_str = "`, `".join(col_names)
    
    cursor.execute("SELECT * FROM calls")
    rows = cursor.fetchall()
    
    with open(sql_filename, 'w', encoding='utf-8') as f:
        f.write("-- Exportacion filtrada y reconstruida de la tabla `calls`\n")
        f.write(f"-- Total de registros: {len(rows)}\n\n")
        
        # Limpiar tabla original antes de cargar (si se requiere)
        f.write("TRUNCATE TABLE `calls`;\n\n")
        
        batch_size = 100
        for i in range(0, len(rows), batch_size):
            batch = rows[i:min(i+batch_size, len(rows))]
            
            f.write(f"INSERT INTO `calls` (`{col_str}`) VALUES\n")
            
            val_strings = []
            for row in batch:
                formatted_vals = []
                for val in row:
                    if val is None:
                        formatted_vals.append("NULL")
                    elif isinstance(val, (int, float)):
                        formatted_vals.append(str(val))
                    else:
                        # Reemplaza todo de una para limpiar inyeccion y strings SQL
                        val_str = str(val)
                        val_str = val_str.replace('\\', '\\\\')
                        val_str = val_str.replace("'", "\\'")
                        val_str = val_str.replace('\n', '\\n')
                        val_str = val_str.replace('\r', '\\r')
                        formatted_vals.append(f"'{val_str}'")
                
                val_strings.append("    (" + ", ".join(formatted_vals) + ")")
            
            f.write(",\n".join(val_strings) + ";\n\n")
            
    conn.close()
    print(f"Exportacion de {len(rows)} llamadas exitosa: {sql_filename}")

export_to_sql('az_marketing.db', 'calls_reparadas_para_produccion.sql')
