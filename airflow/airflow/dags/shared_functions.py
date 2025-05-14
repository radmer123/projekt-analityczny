import logging
import json
from airflow.hooks.base import BaseHook 

def upsert_player_data(player_json):
    import sqlite3                       
    import pandas as pd

# Pobierz obiekt połączenia
    database_conn_id = 'analytics_database'
    connection = BaseHook.get_connection(database_conn_id)
    
    sqlite_db_path = connection.schema

    if player_json:

        player_data = json.loads(player_json)
        
        # Użyj menedżera kontekstu dla połączenia SQLite
        with sqlite3.connect(sqlite_db_path) as conn:
            cursor = conn.cursor()

            # Wstaw każdy rekord zawodnika do tabeli 'player'
            for player in player_data:
                try:
                    cursor.execute("""
                        INSERT INTO player (
                            player_id, gsis_id, first_name, last_name, 
                            position, last_changed_date
                        ) 
                        VALUES (?, ?, ?, ?, ?, ?) 
                        ON CONFLICT(player_id) DO UPDATE
                        SET
                            gsis_id = excluded.gsis_id,
                            first_name = excluded.first_name,
                            last_name = excluded.last_name,
                            position = excluded.position,
                            last_changed_date = excluded.last_changed_date
                    """, (
                        player['player_id'], player['gsis_id'], 
                        player['first_name'], 
                        player['last_name'], 
                        player['position'], 
                        player['last_changed_date']
                    ))
                except Exception as e:
                    logging.error(f"Nie udało się wstawić danych zawodnika {player['player_id']}: {e}")
                    raise
                    
    else:
        logging.warning("Nie znaleziono danych zawodnika.")
        raise ValueError("Nie znaleziono danych gracza. Zadanie nie powiodło się z powodu braku danych.")
