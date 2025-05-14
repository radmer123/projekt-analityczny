import logging
from airflow.decorators import dag
from airflow.providers.http.operators.http import HttpOperator
from airflow.operators.python import PythonOperator
# from airflow.providers.standard.operators.python import PythonOperator
from shared_functions import upsert_player_data

def health_check_response(response):
    logging.info(f"Kod statusu odpowiedzi: {response.status_code}")
    logging.info(f"Treść odpowiedzi: {response.text}")
    return response.status_code == 200 and response.json() == {
        "message": "Test stanu API zakończony sukcesem"
    }

def insert_update_player_data(**context):
    player_json = context["ti"].xcom_pull(task_ids="api_player_query")
    if player_json:
        upsert_player_data(player_json)
    else:
        logging.warning("Nie znaleziono danych zawodnika.")

@dag(schedule_interval=None)
def recurring_player_api_insert_update_dag():
    api_health_check_task = HttpOperator(
        task_id="check_api_health_check_endpoint",
        http_conn_id="sportsworldcentral_url",
        endpoint="/",
        method="GET",
        headers={"Content-Type": "application/json"},
        response_check=health_check_response,
    )

    temp_min_last_change_date = "2024-04-01"
    api_player_query_task = HttpOperator(
       task_id="api_player_query",
       http_conn_id="sportsworldcentral_url",
       endpoint=(
           f"/v0/players/?skip=0&limit=100000&minimum_last_changed_date="

       f"{temp_min_last_change_date}"
       ),
       method="GET",
       headers={"Content-Type": "application/json"},
   )
    player_sqlite_upsert_task = PythonOperator(
        task_id="player_sqlite_upsert",
        python_callable=insert_update_player_data,
        provide_context=True,
    )
    # Kolejność wykonywania zadań
    api_health_check_task >> api_player_query_task >> player_sqlite_upsert_task
# Utworzenie egzemplarza DAG
dag_instance = recurring_player_api_insert_update_dag()
