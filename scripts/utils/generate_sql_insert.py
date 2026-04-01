
import os

file_path = r"c:\Users\Ciencia de DAtos\OneDrive - CONNECTA S.A.S\Escritorio\Varios\az\raw_data.txt"
output_path = r"c:\Users\Ciencia de DAtos\OneDrive - CONNECTA S.A.S\Escritorio\Varios\az\insert_calls.sql"

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found")
    exit(1)

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

sql_statements = []
# Assuming columns: Phone_number, census, implantation_date, purchase_frequency, implantation_pollster

for line in lines:
    parts = line.strip().split("\t")
    # Clean parts
    parts = [p.strip() for p in parts]
    
    if len(parts) >= 2:
        phone = parts[0]
        # Skip header if present
        if not phone.isdigit():
             continue
             
        # Optional defaults
        census = 'NULL'
        imp_date = 'NULL'
        freq = 'NULL'
        pollster = 'NULL'
        
        if len(parts) > 1:
            census = f"'{parts[1]}'" if parts[1] else 'NULL'
        if len(parts) > 2:
            imp_date = f"'{parts[2]}'" if parts[2] else 'NULL'
        if len(parts) > 3:
            freq = f"'{parts[3]}'" if parts[3] else 'NULL'
        if len(parts) > 4:
            pollster = f"'{parts[4]}'" if parts[4] else 'NULL'
            
        study_id = 30
        status = "'pending'"
        
        # INSERT INTO calls (study_id, phone_number, census, implantation_date, purchase_frequency, implantation_pollster, status, created_at)
        # VALUES (30, 'phone', 'census', 'date', 'freq', 'pollster', 'pending', NOW());
        
        sql = f"INSERT INTO calls (study_id, phone_number, census, implantation_date, purchase_frequency, implantation_pollster, status, created_at) VALUES ({study_id}, '{phone}', {census}, {imp_date}, {freq}, {pollster}, {status}, NOW());"
        sql_statements.append(sql)

# Write to file
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(sql_statements))

# Also print to stdout for me to read
print(f"Generated {len(sql_statements)} INSERT statements.")
# Print first 5 to verify
for s in sql_statements[:5]:
    print(s)
