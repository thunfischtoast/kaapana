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

    def extract_config(self, config_filepath):
        with open(config_filepath, "r") as stream:
            try:
                config_dict = yaml.safe_load(stream)
                return config_dict
            except yaml.YAMLError as exc:
                logging.error(f"Could not extract configuration due to error: {exc}!! Exiting...")
                exit(1)
    
    def get_most_recent_dag_run(self, dag_id):
        dag_runs = DagRun.find(dag_id=dag_id)
        dag_runs.sort(key=lambda x: x.execution_date, reverse=True)
        return dag_runs[0] if dag_runs else None

    def start(self, ds, ti, **kwargs):
        operator_dir = os.path.dirname(os.path.abspath(__file__))
        platform_config_path = os.path.join(operator_dir, "platform_specific_configs", "platform_config.yaml")
        request_config_path = os.path.join(operator_dir, "request_specific_configs", "request_config.yaml")
        
        logging.info("Loading platform and request specific configurations...")
        platform_config = self.extract_config(platform_config_path)
        request_config = self.extract_config(request_config_path)
        
        self.trigger_dag_id = "tfda-execution-orchestrator"
        # self.dag_run_id = kwargs['dag_run'].run_id
        self.conf = kwargs['dag_run'].conf
        self.conf["platform_config"] = platform_config
        self.conf["request_config"] = request_config
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