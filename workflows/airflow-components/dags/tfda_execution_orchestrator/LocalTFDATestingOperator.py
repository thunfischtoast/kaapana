import json
import os
import getpass
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import yaml
import logging

from subprocess import PIPE, run
from airflow.models import DagRun
from airflow.api.common.experimental.get_dag_run_state import get_dag_run_state
from airflow.api.common.experimental.trigger_dag import trigger_dag as trigger
from airflow.api.common.experimental.get_dag_run_state import get_dag_run_state
from kaapana.blueprints.kaapana_utils import generate_run_id
from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapana.blueprints.kaapana_global_variables import BATCH_NAME, WORKFLOW_DIR

class LocalTFDATestingOperator(KaapanaPythonBaseOperator):

    def get_most_recent_dag_run(self, dag_id):
        dag_runs = DagRun.find(dag_id=dag_id)
        dag_runs.sort(key=lambda x: x.execution_date, reverse=True)
        return dag_runs[0] if dag_runs else None

    def start(self, ds, ti, **kwargs):
        logging.info("Loading cloud platform config...")
        operator_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(operator_dir, "platform_specific_configs", "cloud_platform_config.yaml")
        with open(config_path, "r") as stream:
            try:
                platform_config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        
        self.trigger_dag_id = "tfda-execution-orchestrator"
        # self.dag_run_id = kwargs['dag_run'].run_id
        self.conf = kwargs['dag_run'].conf
        self.conf["platform_config"] = platform_config
        self.conf["user_selected_bucket"] = "test_site_data"
        dag_run_id = generate_run_id(self.trigger_dag_id)
        logging.info("Triggering isolated execution orchestrator...")
        try:
            trigger(dag_id=self.trigger_dag_id, run_id=dag_run_id, conf=self.conf,
                            replace_microseconds=False)
        except Exception as e:
            logging.error(f"Error while triggering isolated workflow...")
            print(e)

        dag_run = self.get_most_recent_dag_run(self.trigger_dag_id)
        if dag_run:
            logging.info(f"The latest isolated workflow has been triggered at: {dag_run.execution_date}!!!")

        dag_state = get_dag_run_state(dag_id="tfda-execution-orchestrator", execution_date=dag_run.execution_date)

        while dag_state["state"] != "failed" and dag_state['state'] != "success":
            dag_run = self.get_most_recent_dag_run(self.trigger_dag_id)
            dag_state = get_dag_run_state(dag_id="tfda-execution-orchestrator", execution_date=dag_run.execution_date)                        

        if dag_state["state"] == "failed":
            print(f"**************** The evaluation has FAILED ****************")
        if dag_state["state"] == "success":
            print(f"**************** The evaluation was SUCCESSFUL ****************")


    def __init__(self,
                 dag,
                 **kwargs):

        super().__init__(
            dag=dag,
            name="tfda-testing",
            python_callable=self.start,
            **kwargs
        )