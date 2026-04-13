
import pandas as pd

file_path = "scratch/temp_data.xlsx"

try:
    df = pd.read_excel(file_path)
    obs_col = "Observaciones" if "Observaciones" in df.columns else None
    
    if obs_col:
        obs_list = df[obs_col].dropna().astype(str).tolist()
        
        channels = ["sms", "whatsapp", "whapsap", "llamada", "video", "mensaje"]
        no_contesta_keywords = ["no contesta", "no responde", "no respondio", "no contesto"]
        
        results = {}
        for c in channels:
            results[c] = []
            
        specific_no_contesta = []
        
        for obs in obs_list:
            lower_obs = obs.lower()
            if any(k in lower_obs for k in no_contesta_keywords):
                specific_no_contesta.append(obs)
                for c in channels:
                    if c in lower_obs:
                        results[c].append(obs)
        
        print(f"Total 'No Contesta' style observations: {len(specific_no_contesta)}")
        for c, matches in results.items():
            print(f"Channel '{c}': {len(matches)} matches")
            # Show a few examples
            if matches:
                print(f"  Examples: {matches[:3]}")
                
except Exception as e:
    print(f"Error: {e}")
