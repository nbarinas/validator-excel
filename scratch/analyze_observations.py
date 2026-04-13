import sqlite3
import pandas as pd

def get_common_observations():
    conn = sqlite3.connect('az_marketing.db')
    
    # Check observations table
    try:
        df_obs = pd.read_sql_query("SELECT text, COUNT(*) as count FROM observations GROUP BY text ORDER BY count DESC LIMIT 30", conn)
        print("Most common from 'observations' table:")
        print(df_obs)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Error reading observations table: {e}")

    # Check calls table
    try:
        df_calls = pd.read_sql_query("SELECT observation, COUNT(*) as count FROM calls WHERE observation IS NOT NULL AND observation != '' GROUP BY observation ORDER BY count DESC LIMIT 30", conn)
        print("Most common from 'calls' table (observation column):")
        print(df_calls)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Error reading calls table: {e}")

    conn.close()

if __name__ == "__main__":
    get_common_observations()
