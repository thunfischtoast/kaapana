import os
import sys
import glob
import zipfile
from subprocess import PIPE, run
import re

from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapana.blueprints.kaapana_global_variables import BATCH_NAME, WORKFLOW_DIR


class LocalCreateIsoInstanceOperator(KaapanaPythonBaseOperator):

    def start(self, ds, ti, **kwargs):
        print("Starting an isolated environment...")

        operator_dir = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.join(operator_dir, "scripts")
        playbooks_dir = os.path.join(operator_dir, "ansible_playbooks")
        # print(f'Playbooks directory is {playbooks_dir}, and scripts are in {scripts_dir}, and directory is {operator_dir}')

        playbook_path = os.path.join(playbooks_dir, "00_start_"+self.platformType+"_instance.yaml")
        if not os.path.isfile(playbook_path):
            print("playbook yaml not found.")
            exit(1)
        
        ### following is hardcoded, need to fix
        ## platform specific params
        os_project_name = "E230-TFDA"
        os_project_id = "f4a5b8b7adf3422d85b28b06f116941c"
        os_instance_name = "tfda-airflow-iso-envt"
        os_username = ""
        os_password = ""
        ## machine specific params, could be platform agnostic
        os_image = "c34f31bf-57a8-4189-9eee-d2efc18415eb"
        # os_ssh_key = "kaapana"
        os_volume_size = "200"
        os_instance_flavor = "dkfz.gpu-V100S-16CD"

        extra_vars = f"os_project_name={os_project_name} os_project_id={os_project_id} os_username={os_username} os_password={os_password} os_instance_name={os_instance_name} os_image={os_image} os_volume_size={os_volume_size} os_instance_flavor={os_instance_flavor}"        
        command = ["ansible-playbook", playbook_path, "--extra-vars", extra_vars]
        output = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, timeout=6000)
        print(f'STD OUTPUT LOG is {output.stdout}')
        if output.returncode == 0:
            print(f'Iso Instance created successfully!')
            ip_addr_string = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', output.stdout)
            print(f'IP address of new TFDA isolated instance is: {ip_addr_string[-1]}')
            ti.xcom_push(key="iso_env_ip", value=ip_addr_string[-1])
        else:
            print(f"Failed to create isolated environment! ERROR LOGS:\n{output.stderr}")
        

    def __init__(self,
                 dag,
                 platformType = "openstack",
                 **kwargs):

        super().__init__(
            dag=dag,
            name="create-iso-inst",
            python_callable=self.start,
            **kwargs
        )
