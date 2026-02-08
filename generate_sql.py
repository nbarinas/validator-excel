
import os

file_path = r"c:\Users\Ciencia de DAtos\OneDrive - CONNECTA S.A.S\Escritorio\Varios\az\raw_data.txt"
output_path = r"c:\Users\Ciencia de DAtos\OneDrive - CONNECTA S.A.S\Escritorio\Varios\az\update_calls.sql"

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found")
    exit(1)

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

sql_statements = []

for line in lines:
    parts = line.strip().split("\t")
    # Clean parts
    parts = [p.strip() for p in parts]
    
    # Expected format: Phone_number, census, implantation_date, purchase_frequency, implantation_pollster
    # len >= 2 at least
    
    if len(parts) >= 2:
        phone = parts[0]
        # Skip header if present
        if not phone.isdigit():
             continue
             
        # Mapping based on user provided columns:
        # 0: phone, 1: census, 2: imp_date, 3: freq, 4: pollster
        
        # We start looking for data from index 2
        imp_date = None
        freq = None
        pollster = None
        
        if len(parts) > 2:
            imp_date = parts[2]
        if len(parts) > 3:
            freq = parts[3]
        if len(parts) > 4:
            pollster = parts[4]
            
        # Construct update
        updates = []
        if imp_date:
            updates.append(f"implantation_date = '{imp_date}'")
        if freq:
             updates.append(f"purchase_frequency = '{freq}'")
        if pollster:
             updates.append(f"implantation_pollster = '{pollster}'")
             
        if updates:
            set_clause = ", ".join(updates)
            # Use LIKE or strict equality? User said "tomo el numero", usually exact match is safer if cleaning is good.
            # But phone numbers might have issues. Assuming exact string match for now as per user data.
            sql = f"UPDATE calls SET {set_clause} WHERE phone_number = '{phone}';"
            sql_statements.append(sql)

# Write to file
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(sql_statements))

# Also print to stdout for me to read
print(f"Generated {len(sql_statements)} statements.")
# Print first 5 to verify
for s in sql_statements[:5]:
    print(s)
