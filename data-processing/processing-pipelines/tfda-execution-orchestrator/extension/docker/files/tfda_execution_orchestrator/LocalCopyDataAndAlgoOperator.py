import os
import glob
import zipfile
import logging
import subprocess
from subprocess import PIPE
from airflow.exceptions import AirflowFailException
from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapana.blueprints.kaapana_global_variables import BATCH_NAME, WORKFLOW_DIR


class LocalCopyDataAndAlgoOperator(KaapanaPythonBaseOperator):
    def start(self, ds, ti, **kwargs):
        logging.info("Copy data and algorithm to isolated environment...")
        airflow_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        minio_path = os.path.join(airflow_dir, "miniobuckets")
        operator_dir = os.path.dirname(os.path.abspath(__file__))
        request_specific_config_path = os.path.join(operator_dir, "request_specific_configs")
        user_input_commands_path = os.path.join(request_specific_config_path, "user_input_commands.sh")
        algorithm_files_path = os.path.join(operator_dir, "algorithm_files")
        playbooks_dir = os.path.join(operator_dir, "ansible_playbooks")
        playbook_path = os.path.join(playbooks_dir, "copy_algo_to_iso_env.yaml")
        
        if not os.path.isfile(playbook_path):
            raise AirflowFailException(f"Playbook '{playbook_path}' file not found!")
        if not os.path.isfile(user_input_commands_path):
            raise AirflowFailException("user_input_commands_path file not found!")


        platform_config = kwargs["dag_run"].conf["platform_config"]        
        request_config = kwargs["dag_run"].conf["request_config"]
        
        platform_type = request_config["request_config"]["platform_type"]
        platform_flavor = request_config["request_config"]["platform_flavor"]
        remote_username = platform_config["configurations"]["platform"][platform_type]["dynamic_params"][platform_flavor]["os_remote_username"]
        user_selected_algo = request_config["request_config"]["user_selected_algorithm"]
        user_selected_study_data = request_config["request_config"]["user_selected_study_data"]
        
        user_selected_algo_path = os.path.join(algorithm_files_path, user_selected_algo)
        study_data_src_path = os.path.join(minio_path, user_selected_study_data)

        iso_env_ip = ti.xcom_pull(key="iso_env_ip", task_ids="create-iso-inst")

        playbook_args = f"target_host={iso_env_ip} remote_username={remote_username} user_selected_algo_path={user_selected_algo_path} study_data_src_path={study_data_src_path} user_selected_study_data={user_selected_study_data} user_input_commands_path={user_input_commands_path}"        
        command = ["ansible-playbook", playbook_path, "--extra-vars", playbook_args]
        process = subprocess.Popen(command, stdout=PIPE, stderr=PIPE, encoding="Utf-8")
        while True:
            output = process.stdout.readline()
            if process.poll() is not None:
                break
            if output:
                print(output.strip())
        rc = process.poll()
        if rc == 0:
            logging.info(f"Files copied successfully!!")
        else:
            raise AirflowFailException("Playbook FAILED! Cannot proceed further...")


    def __init__(self,
                 dag,
                 **kwargs):

        super().__init__(
            dag=dag,
            name="copy-data-algo",
            python_callable=self.start,
            **kwargs
        )
