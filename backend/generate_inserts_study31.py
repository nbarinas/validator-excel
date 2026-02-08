
import os

# Define file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: Raw data files are in backend/
RAW_FILES = [
    os.path.join(BASE_DIR, "raw_data_part1.txt"),
    os.path.join(BASE_DIR, "raw_data_part2.txt"),
    os.path.join(BASE_DIR, "raw_data_part3.txt"),
    os.path.join(BASE_DIR, "raw_data_part4.txt") # Assuming 4 parts created
]
OUTPUT_FILE = os.path.join(BASE_DIR, "insert_calls_study31.sql")

def clean_text(text, max_len=None):
    if not text:
        return 'NULL'
    clean = text.strip().replace("'", "''") # Escape single quotes
    if max_len and len(clean) > max_len:
        clean = clean[:max_len]
    return f"'{clean}'"

def parse_line(line):
    parts = line.strip().split('\t')
    if len(parts) < 5: # Basic validation
        return None
    
    # Mapping based on user provided header:
    # ... (same comments)
    
    # Needs handling for missing columns if line is short
    def get_part(index):
        return parts[index] if index < len(parts) else ''

    return {
        'city': clean_text(get_part(0), 100),
        'census': clean_text(get_part(1), 50),
        'nse': clean_text(get_part(2), 50),
        'code': clean_text(get_part(3), 50),
        'person_name': clean_text(get_part(4), 100),
        'age': clean_text(get_part(5), 20),
        'phone_number': clean_text(get_part(6), 20),
        'whatsapp': clean_text(get_part(7), 50),
        'neighborhood': clean_text(get_part(8), 200),
        'address': clean_text(get_part(9), 300),
        'housing_description': clean_text(get_part(10), 300),
        'wash_frequency': clean_text(get_part(11), 100),
        'shampoo_brand': clean_text(get_part(12), 100),
        'shampoo_variety': clean_text(get_part(13), 100),
        'treatment_brand': clean_text(get_part(14), 100),
        'treatment_variety': clean_text(get_part(15), 100),
        'conditioner_brand': clean_text(get_part(16), 100),
        'conditioner_variety': clean_text(get_part(17), 100),
        'purchase_frequency': clean_text(get_part(18), 100),
        'hair_type': clean_text(get_part(19), 50),
        'hair_shape': clean_text(get_part(20), 50),
        'hair_length': clean_text(get_part(21), 50),
        'implantation_pollster': clean_text(get_part(22), 100),
        'supervisor': clean_text(get_part(23), 100),
        'implantation_date': clean_text(get_part(24), 50),
        'collection_date': clean_text(get_part(25), 50),
        'collection_time': clean_text(get_part(26), 50)
    }

def generate_sql():
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        # outfile.write("USE callcenter_db;\n\n") # Commented out to avoid permission errors
        
        count = 0
        for raw_file in RAW_FILES:
            if not os.path.exists(raw_file):
                print(f"Skipping missing file: {raw_file}")
                continue
                
            print(f"Processing {raw_file}...")
            with open(raw_file, 'r', encoding='utf-8') as infile:
                lines = infile.readlines()
                
                for i, line in enumerate(lines):
                    # Skip header in first file or any line starting with header keywords
                    if "CIUDAD" in line and "CENSO" in line:
                        continue
                        
                    data = parse_line(line)
                    if not data:
                        continue
                        
                    sql = f"""INSERT INTO calls (
                        study_id, city, census, nse, code, person_name, age, phone_number, whatsapp, 
                        neighborhood, address, housing_description, wash_frequency, shampoo_brand, 
                        shampoo_variety, treatment_brand, treatment_variety, conditioner_brand, 
                        conditioner_variety, purchase_frequency, hair_type, hair_shape, hair_length, 
                        implantation_pollster, supervisor, implantation_date, collection_date, collection_time,
                        status
                    ) VALUES (
                        31, {data['city']}, {data['census']}, {data['nse']}, {data['code']}, {data['person_name']}, 
                        {data['age']}, {data['phone_number']}, {data['whatsapp']}, {data['neighborhood']}, 
                        {data['address']}, {data['housing_description']}, {data['wash_frequency']}, 
                        {data['shampoo_brand']}, {data['shampoo_variety']}, {data['treatment_brand']}, 
                        {data['treatment_variety']}, {data['conditioner_brand']}, {data['conditioner_variety']}, 
                        {data['purchase_frequency']}, {data['hair_type']}, {data['hair_shape']}, 
                        {data['hair_length']}, {data['implantation_pollster']}, {data['supervisor']}, 
                        {data['implantation_date']}, {data['collection_date']}, {data['collection_time']},
                        'pending'
                    );\n"""
                    
                    outfile.write(sql)
                    count += 1
        
        print(f"Generated {count} INSERT statements in {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_sql()
