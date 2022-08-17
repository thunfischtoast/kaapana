import os
import glob
import zipfile
import logging
import subprocess
from subprocess import PIPE
from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapana.blueprints.kaapana_global_variables import BATCH_NAME, WORKFLOW_DIR


class LocalCopyDataAndAlgoOperator(KaapanaPythonBaseOperator):
    def start(self, ds, ti, **kwargs):
        print("Copy data and algorithm to isolated environment...")
        operator_dir = os.path.dirname(os.path.abspath(__file__))
        airflow_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        minio_dir = os.path.join(airflow_dir, "miniobuckets")
        request_specific_config_path = os.path.join(operator_dir, "request_specific_configs")

        scripts_dir = os.path.join(operator_dir, "scripts")
        playbooks_dir = os.path.join(operator_dir, "ansible_playbooks")
        print(f'Playbooks directory is {playbooks_dir}, and scripts are in {scripts_dir}, and directory is {operator_dir}')
        
        platform_install_playbook_path = os.path.join(
        playbooks_dir, "copy_algo_to_iso_env.yaml"
        )
        user_input_commands_path = os.path.join(
        request_specific_config_path, "user_input_commands.sh"
        )
        if not os.path.isfile(platform_install_playbook_path):
            print("Playbook yaml file not found.")
            exit(1)
        if not os.path.isfile(user_input_commands_path):
            print("user_input_commands_path file not found.")
            exit(1)

        request_config = kwargs["dag_run"].conf["request_config"]
        user_selected_data = request_config["request_config"]["user_selected_study_data"]
        user_selected_data_path = os.path.join(minio_dir, user_selected_data)

        iso_env_ip = ti.xcom_pull(key="iso_env_ip", task_ids="create-iso-inst")
        tarball_path = os.path.join(operator_dir, "tarball")

        playbook_args = f"target_host={iso_env_ip} remote_username=root tarball_path={tarball_path} user_selected_data={user_selected_data_path} user_input_commands_path={user_input_commands_path}"        
        command = ["ansible-playbook", platform_install_playbook_path, "--extra-vars", playbook_args]
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
            logging.error("Playbook FAILED! Cannot proceed further...")
            exit(1)
            

    def __init__(self,
                 dag,
                 **kwargs):

        super().__init__(
            dag=dag,
            name="copy-data-algo",
            python_callable=self.start,
            **kwargs
        )
