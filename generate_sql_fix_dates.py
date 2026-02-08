
import os
import datetime

file_path = r"c:\Users\Ciencia de DAtos\OneDrive - CONNECTA S.A.S\Escritorio\Varios\az\raw_data_dates.txt"
output_path = r"c:\Users\Ciencia de DAtos\OneDrive - CONNECTA S.A.S\Escritorio\Varios\az\update_dates.sql"

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found")
    exit(1)

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

sql_statements = []

def parse_date(date_str):
    # Try parsing d/m/yyyy and return YYYY-MM-DD
    try:
        dt = datetime.datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None

for line in lines:
    parts = line.strip().split("\t")
    if len(parts) < 2:
        continue
        
    phone = parts[0]
    raw_date = parts[1]
    
    # Skip header
    if not phone.isdigit():
        continue
        
    new_date = parse_date(raw_date)
    
    if new_date:
        # Generate UPDATE statement
        # Using phone_number and study_id=30 to be specific
        sql = f"UPDATE calls SET collection_date = '{new_date}' WHERE phone_number = '{phone}' AND study_id = 30;"
        sql_statements.append(sql)

# Write to file
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(sql_statements))

print(f"Generated {len(sql_statements)} UPDATE statements.")
