import os
import sys
import glob
import zipfile
from subprocess import PIPE, run
import re

from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapana.blueprints.kaapana_global_variables import BATCH_NAME, WORKFLOW_DIR

import kaapana.CI.scripts.ci_playbook_execute as ci_execute


class LocalCreateIsoInstanceOperator(KaapanaPythonBaseOperator):

    def start(self, ds, ti, **kwargs):
        print("Starting an isolated environment...")
        print(kwargs)

        dags_dir = os.path.dirname(os.path.abspath(__file__)))
        scripts_dir = os.path.join(dags_dir, "tfda_execution_orchestrator", "scripts")
        playbooks_dir = os.path.join(dags_dir, "tfda_execution_orchestrator", "ansible_playbooks")
        print(f'Playbooks directory is {playbooks_dir}, and scripts are in {scripts_dir}, and kaapana dir is {kaapana_dir}')
        # run_dir = os.path.join(WORKFLOW_DIR, kwargs['dag_run'].run_id)
        # batch_input_dir = os.path.join(run_dir, self.operator_in_dir)
        # print('input_dir', batch_input_dir)

        # batch_output_dir = os.path.join(run_dir, self.operator_out_dir)  # , project_name)
        # if not os.path.exists(batch_output_dir):
        #     os.makedirs(batch_output_dir)

        # for file_path in glob.glob(os.path.join(batch_input_dir, '*.zip')):
        #     with zipfile.ZipFile(file_path, 'r') as zip_ref:
        #         zip_ref.extractall(batch_output_dir)

        playbook_path = os.path.join(
        playbooks_dir, "00_start_openstack_instance.yaml"
        )
        if not os.path.isfile(playbook_path):
            print("playbook yaml not found.")
            exit(1)
        
        # extra_vars = {
        #     "os_project_name": "E230-Kaapana-CI",
        #     "os_project_id": "2df9e30325c849dbadcc07d7ffd4b0d6",
        #     "os_instance_name": "tfda-airfl-iso-env-test",
        #     "os_username": os_username,
        #     "os_password": os_password,
        #     "os_image": "ubuntu",
        #     "os_ssh_key": "kaapana",
        #     "os_volume_size": "100",
        #     "os_instance_flavor": "dkfz-8.16",
        # }

        # instance_ip_address, logs = ci_execute.execute(
        #     playbook_path,
        #     testsuite="Setup Test Server",
        #     testname="Start OpenStack instance: {}".format("ubuntu"),
        #     hosts=["localhost"],
        #     extra_vars=extra_vars,
        # )
        
        os_project_name = "E230-Kaapana-CI"
        os_project_id = "2df9e30325c849dbadcc07d7ffd4b0d6"
        os_instance_name = "tfda-airfl-iso-env-test"
        os_username = ""
        os_password = ""
        os_image = "bd2a2141-9e1d-484c-85ce-3d40222c1682"
        # os_ssh_key = "kaapana"
        # os_volume_size = "100"
        # os_instance_flavor = "dkfz-8.16"

        extra_vars = f"os_project_name={os_project_name} os_project_id={os_project_id} os_username={os_username} os_password={os_password} os_instance_name=tfda_iso_inst, os_instance_name={os_instance_name} os_image={os_image}"
        command = ["ansible-playbook", playbook_path, "--extra-vars", extra_vars]
        output = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, timeout=6000)
        print(f'STD OUTPUT LOG is {output.stdout}')
        if output.returncode == 0:
            print(f'Iso Instance created successfully!')
            ## extract ip address from stdout
            # ip_addr_string = re.findall('isolated_env_ip: \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', output.stdout)
            ip_addr_string = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', output.stdout)
            # ip_address = re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ip_addr_string)
            print(f'IP address of new TFDA isolated instance is: {ip_addr_string[-1]}')
            ti.xcom_push(key="iso_env_ip", value=ip_addr_string[-1])
        else:
            print(f"Failed to create isolated environment! ERROR LOGS:\n{output.stderr}")
        
        # print(f'IP address is {instance_ip_address} and logs are {logs}')

    def __init__(self,
                 dag,
                 **kwargs):

        super().__init__(
            dag=dag,
            name="create-iso-inst",
            python_callable=self.start,
            **kwargs
        )
