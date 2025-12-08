import pandas as pd

# File 1: Base - should pass with File 2
data1 = {
    "Id": [1, 2, 3],
    "Ciudad": ["Bogota", "Medellin", "Cali"],
    "Numero de celular": ["3001234567", "3109876543", "3201112233"],
    "Codigo": ["A", "B", "C"]
}
df1 = pd.DataFrame(data1)
df1.to_excel("test_file_1.xlsx", index=False)

# File 2: Valid pair (Same Id/Ciudad/Celular, Diff Codigo)
data2 = {
    "Id": [1, 2, 3],
    "Ciudad": ["Bogota", "Medellin", "Cali"],
    "Numero de celular": ["3001234567", "3109876543", "3201112233"],
    "Codigo": ["X", "Y", "Z"] # Different codes
}
df2 = pd.DataFrame(data2)
df2.to_excel("test_file_2_valid.xlsx", index=False)

# File 3: Invalid pair (Mismatch Ciudad)
data3 = {
    "Id": [1, 2, 3],
    "Ciudad": ["Bogota", "Pereira", "Cali"], # Mismatch row 2
    "Numero de celular": ["3001234567", "3109876543", "3201112233"],
    "Codigo": ["X", "Y", "Z"]
}
df3 = pd.DataFrame(data3)
df3.to_excel("test_file_3_invalid_ciudad.xlsx", index=False)

# File 4: Invalid pair (Same Codigo)
data4 = {
    "Id": [1, 2, 3],
    "Ciudad": ["Bogota", "Medellin", "Cali"],
    "Numero de celular": ["3001234567", "3109876543", "3201112233"],
    "Codigo": ["A", "B", "C"] # Same as file 1
}
df4 = pd.DataFrame(data4)
df4.to_excel("test_file_4_invalid_codigo.xlsx", index=False)

print("Test files created.")
