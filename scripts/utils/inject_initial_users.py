import sqlite3
import sys

# Agregamos la ruta temporal para poder importar get_password_hash si es necesario
# Pero como ya tenemos un sistema funcionando, simplemente usaremos un hash por defecto pre-calculado
# para 'admin123'. Este hash es de bcrypt y es seguro.
default_hash = '$2b$12$QRuOw.wMAqcT/jb2obi2bO8uGb64CF/5.TSoM6Sa/qo8a9T5hS8D2'

users_data = [
    {
        "id": 1,
        "username": "admin",
        "role": "superuser",
        "full_name": "Armando Zarate",
        "bank": "Banco Caja Social",
        "account_type": "Ahorros",
        "account_number": "24517416433",
        "birth_date": "1985-09-08",
        "phone_number": "3234968972",
        "address": "carrera 53 # 37 38 sur",
        "city": "Bogotá",
        "neighborhood": "Alqueria las telas",
        "last_seen": "2026-03-01 02:43:30",
        "cedula_ciudadania": None
    },
    {
        "id": 7,
        "username": "3124571375",
        "role": "auxiliar",
        "full_name": "Felipe Monsalve",
        "last_seen": "2026-01-20 21:34:38"
    },
    {
        "id": 9,
        "username": "3173852576",
        "role": "bizage",
        "full_name": "Milena Zarate",
        "bank": "Banco Caja Social",
        "account_type": "Ahorros",
        "account_number": "24150874791",
        "phone_number": "3173852676",
        "address": "carrera 1 H # 37 38 sur",
        "city": "Bogotá",
        "neighborhood": "Guacamayas",
        "account_holder": "Milena Zarate",
        "account_holder_cc": "51155850",
        "last_seen": "2026-02-28 22:42:58",
        "cedula_ciudadania": "51155850"
    },
    {
        "id": 10,
        "username": "3237332804",
        "role": "agent",
        "full_name": "Andrés Rivas",
        "city": "FUSAGASUFA",
        "last_seen": "2026-01-26 23:15:45",
        "cedula_ciudadania": "13050271"
    },
    {
        "id": 14,
        "username": "3118880055",
        "role": "supervisor",
        "full_name": "Nubia Garcia",
        "bank": "Banco Caja Social",
        "account_type": "Ahorros",
        "account_number": "24131630868",
        "birth_date": "1959-06-17",
        "phone_number": "3118880055",
        "address": "cll 59 a sur $ 75 h 18",
        "city": "Bogotá",
        "neighborhood": "Estancia",
        "blood_type": "A+",
        "account_holder": "Nubia Garcia",
        "account_holder_cc": "51605052",
        "last_seen": "2026-01-21 23:11:45",
        "cedula_ciudadania": "51605052"
    },
    {
        "id": 18,
        "username": "3203513376",
        "role": "superuser",
        "full_name": "Johana Benitez",
        "account_type": "Ahorros",
        "birth_date": "1985-09-03",
        "phone_number": "3203513376",
        "address": "cll 71 sur # 98 b 50",
        "city": "Bogotá",
        "neighborhood": "ciudad de la recreo",
        "blood_type": "O+",
        "last_seen": "2026-03-01 02:26:01",
        "cedula_ciudadania": "53102227"
    },
    {
        "id": 19,
        "username": "3113232015",
        "role": "agent",
        "full_name": "Yraima Coromoto Rey",
        "bank": "Banco Caja Social",
        "account_type": "Ahorros",
        "account_number": "24131693852",
        "phone_number": "3113232015",
        "city": "Bogotá",
        "last_seen": "2026-01-21 14:54:50",
        "cedula_ciudadania": "ppt 63502232"
    }
]

conn = sqlite3.connect('az_marketing.db')
cursor = conn.cursor()

# Borrar el admin temporal que creamos antes para evitar choques
cursor.execute("DELETE FROM users WHERE username = 'admin'")

for u in users_data:
    # Borrar si el ID ya existe incidentalmente
    cursor.execute("DELETE FROM users WHERE id = ?", (u['id'],))
    
    cols = ['id', 'username', 'role', 'full_name', 'hashed_password']
    vals = [u['id'], u['username'], u['role'], u['full_name'], default_hash]
    
    for k in ['bank', 'account_type', 'account_number', 'birth_date', 'phone_number', 'address', 'city', 'neighborhood', 'blood_type', 'account_holder', 'account_holder_cc', 'last_seen', 'cedula_ciudadania']:
        if k in u:
            cols.append(k)
            vals.append(u[k])
            
    placeholders = ','.join(['?']*len(cols))
    col_str = ','.join([f'"{c}"' for c in cols])
    
    sql = f"INSERT INTO users ({col_str}) VALUES ({placeholders})"
    cursor.execute(sql, tuple(vals))

conn.commit()
conn.close()
print("¡Usuarios insertados con éxito!")
