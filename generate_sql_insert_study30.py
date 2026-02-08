
import os
import datetime

file_path = r"c:\Users\Ciencia de DAtos\OneDrive - CONNECTA S.A.S\Escritorio\Varios\az\raw_data_insert.txt"
output_path = r"c:\Users\Ciencia de DAtos\OneDrive - CONNECTA S.A.S\Escritorio\Varios\az\insert_calls_study30.sql"

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found")
    exit(1)

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

sql_statements = []

def clean(text):
    if not text or text.lower() == 'null':
        return 'NULL'
    # Escape quotes
    text = text.replace("'", "\\'")
    return f"'{text}'"

# Column Mapping based on review:
# 0: CIUDAD -> city
# 1: CENSO -> census
# 2: NSE -> nse
# 3: CODIGO -> code
# 4: NOMBRE Y APELLIDO -> person_name
# 5: EDAD -> age
# 6: CELULAR -> phone_number
# 7: WHASSAPP -> whatsapp
# 8: BARRIO -> neighborhood
# 9: DIRECCION -> address
# 10: DESCRIPCION VIVIENDA -> housing_description
# 11: FRECUENCIA DE LAVADO -> wash_frequency
# 12: MARCA DE SHAMPOO -> shampoo_brand
# 13: CARIEDAD SHAMPOO -> shampoo_variety
# 14: MARCA TRATAMIENTO -> treatment_brand
# 15: CARIEDAD TRATAMIENTO -> treatment_variety
# 16: MARCA ACONDICIONADOR -> conditioner_brand
# 17: VARIEDAD ACONDICIONADOR -> conditioner_variety
# 18: CON QUE FRECUENCIA COMPRA SHAMPOO -> purchase_frequency
# 19: TIPO DE CABELLO -> hair_type
# 20: FORMA DE CABELLO -> hair_shape
# 21: pLARGO DE CABELLO -> hair_length
# 22: ENCUESTADOR -> implantation_pollster
# 23: SUPERVISOR -> supervisor
# 24: FECHA DE IMPLANTACION -> implantation_date
# 25: FECHA DE RECOGIDA -> collection_date
# 26: HORA DE RECOGIDA -> collection_time
# 27: ENCUESTADOR (duplicate or next step?) -> Ignore or map if distinct? User data shows empty mostly or rep? Row 1: Gretta Perez (22) and Gretta Perez (22). Wait, let's re-read data.
# Row 1: ... | Gretta Perez | Veronica Cifuentes | 22/1/2026 | 1/2/2026 | Durante el dia | | |
# Col 22: Gretta
# Col 23: Veronica
# Col 24: 22/1/2026
# Col 25: 1/2/2026
# Col 26: Durante el dia
# Col 27: Empty (ENCUESTADOR #2)
# Col 28: Empty (ESTADO)
# Col 29: Empty (FECHA R1)
# ...

study_id = 30

for line in lines:
    parts = line.strip().split("\t")
    # Pad to ensure minimum length if needed, but dict access is safer
    # Convert to strict mapping
    
    if len(parts) < 5: continue # Skip empty lines
    
    # Header skip
    if "CIUDAD" in parts[0] or "CENSO" in parts[1]:
        continue
        
    def get_part(idx):
        if idx < len(parts):
            val = parts[idx].strip()
            return clean(val) if val else 'NULL'
        return 'NULL'

    city = get_part(0)
    census = get_part(1)
    nse = get_part(2)
    code = get_part(3)
    person_name = get_part(4)
    age = get_part(5)
    phone_number = get_part(6)
    whatsapp = get_part(7)
    neighborhood = get_part(8)
    address = get_part(9)
    housing_description = get_part(10)
    wash_frequency = get_part(11)
    shampoo_brand = get_part(12)
    shampoo_variety = get_part(13)
    treatment_brand = get_part(14)
    treatment_variety = get_part(15)
    conditioner_brand = get_part(16)
    conditioner_variety = get_part(17)
    # The user header had "MARCA ACONDICIONADOR" then "VARIEDAD ACONDICIONADOR" then "CON QUE FRECUENCIA"
    # Wait, in the data ROW 1:
    # 12: 3 veces a la semana (Wash freq)
    # 13: NUtribela (Shampoo brand)?
    # Let's re-verify index 12 in header: "FRECUENCIA DE LAVADO" is index 11 (0-based: CIUDAD=0).
    # YES.
    # 16: MARCA ACONDICIONADOR -> conditioner_brand
    # 17: VARIEDAD ACONDICIONADOR -> conditioner_variety
    # 18: CON QUE FRECUENCIA COMPRA SHAMPOO -> purchase_frequency
    
    purchase_frequency = get_part(18)
    hair_type = get_part(19)
    hair_shape = get_part(20)
    hair_length = get_part(21)
    implantation_pollster = get_part(22)
    supervisor = get_part(23)
    implantation_date = get_part(24)
    collection_date = get_part(25)
    collection_time = get_part(26)
    
    # Defaults
    status = "'pending'"
    
    fields = [
        "study_id", "city", "census", "nse", "code", "person_name", "age",
        "phone_number", "whatsapp", "neighborhood", "address", "housing_description",
        "wash_frequency", "shampoo_brand", "shampoo_variety", "treatment_brand",
        "treatment_variety", "conditioner_brand", "conditioner_variety",
        "purchase_frequency", "hair_type", "hair_shape", "hair_length",
        "implantation_pollster", "supervisor", "implantation_date",
        "collection_date", "collection_time", "status", "created_at"
    ]
    
    values = [
        str(study_id), city, census, nse, code, person_name, age,
        phone_number, whatsapp, neighborhood, address, housing_description,
        wash_frequency, shampoo_brand, shampoo_variety, treatment_brand,
        treatment_variety, conditioner_brand, conditioner_variety,
        purchase_frequency, hair_type, hair_shape, hair_length,
        implantation_pollster, supervisor, implantation_date,
        collection_date, collection_time, status, "NOW()"
    ]
    
    # Construct SQL
    cols_str = ", ".join(fields)
    vals_str = ", ".join(values)
    
    sql = f"INSERT INTO calls ({cols_str}) VALUES ({vals_str});"
    sql_statements.append(sql)

# Write to file
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(sql_statements))

print(f"Generated {len(sql_statements)} INSERT statements for Study 30.")
