
import os
import sys
import pandas as pd
from datetime import datetime
from sqlalchemy import inspect

# Add backend to path to import database
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from backend.database import engine
except ImportError:
    # Try local import if running from root
    sys.path.append(os.path.join(os.path.dirname(__file__)))
    from backend.database import engine

def backup_database():
    print("Iniciando respaldo de base de datos...")
    
    # Create backups folder
    if not os.path.exists('backups'):
        os.makedirs('backups')
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"backups/backup_completo_{timestamp}.xlsx"
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"Tablas encontradas: {', '.join(tables)}")
    
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        for table in tables:
            print(f"Respaldando tabla: {table}...", end=" ", flush=True)
            try:
                df = pd.read_sql_table(table, engine)
                df.to_excel(writer, sheet_name=table[:31], index=False) # Sheet names limited to 31 chars
                print(f"OK ({len(df)} registros)")
            except Exception as e:
                print(f"ERROR: {e}")
                
    print(f"\nRespaldo completado exitosamente: {filename}")
    print(f"Ubicación: {os.path.abspath(filename)}")

if __name__ == "__main__":
    backup_database()
