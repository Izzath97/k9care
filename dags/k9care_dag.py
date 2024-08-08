"""
This file defines an Apache Airflow DAG for the K9 Care ETL process.
"""

from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 0
}

dag = DAG(
    dag_id='k9care_DAG',
    default_args=default_args,
    start_date=datetime(2024, 8, 7),
    catchup=False,
    schedule_interval='@daily',
)

t1 = BashOperator(
    task_id='Bash_task',
    bash_command='python $AIRFLOW_HOME/dags/scripts/k9care_etl.py',
    dag=dag
)
