
import pandas as pd
import sys

file_path = "llamadas_export_2026-04-12.xlsx"
file_path = "scratch/temp_data.xlsx"
try:
    df = pd.read_excel(file_path)
    print("Column names found:")
    print(df.columns.tolist())
    
    # Identify the observation column (could be "Observaciones", "observation", etc.)
    # The user said "Observaciones"
    obs_col = "Observaciones" if "Observaciones" in df.columns else None
    if not obs_col:
        # Fallback search
        for col in df.columns:
            if "obs" in col.lower():
                obs_col = col
                break
    
    if obs_col:
        print(f"\nAnalyzing column: {obs_col}")
        obs_counts = df[obs_col].value_counts().head(50)
        print("\nTop 50 most common observations:")
        print(obs_counts)
        
        # Save unique values for later IA processing if needed
        uniques = df[obs_col].dropna().unique().tolist()
        with open("scratch/observations_list.txt", "w", encoding="utf-8") as f:
            for item in uniques:
                f.write(str(item) + "\n")
        print(f"\nSaved {len(uniques)} unique observations to scratch/observations_list.txt")
    else:
        print("Could not find 'Observaciones' column.")

except Exception as e:
    print(f"Error: {e}")
