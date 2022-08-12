import os
import glob
import zipfile
from subprocess import PIPE, run
import re
import logging

from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapana.blueprints.kaapana_global_variables import BATCH_NAME, WORKFLOW_DIR


class LocalManageIsoInstanceOperator(KaapanaPythonBaseOperator):
    def start(self, ds, ti, **kwargs):
        if self.instanceState == "present":
            logging.info("Starting an isolated environment...")
        elif self.instanceState == "absent":
            logging.info("Deleting isolated environment...")

        request_config = kwargs["dag_run"].conf["request_config"]
        platform_type = request_config["request_config"]["platform_type"]
        platform_flavor = request_config["request_config"]["platform_flavor"]
        
        operator_dir = os.path.dirname(os.path.abspath(__file__))
        playbooks_dir = os.path.join(operator_dir, "ansible_playbooks")
        playbook_path = os.path.join(playbooks_dir, "00_manage_"+platform_type+"_instance.yaml")
        if not os.path.isfile(playbook_path):
            logging.error("Playbook yaml not found!! Exiting...")
            exit(1)
        
        playbook_args = f"instance_state={self.instanceState}"
        
        platform_config = kwargs["dag_run"].conf["platform_config"]        
        os_username = platform_config["configurations"]["username"]
        os_password = platform_config["configurations"]["password"]
        if (os_username is None or os_username == "") or (os_password is None or os_password == ""):
            logging.error(f"{platform_type.title()} platform credentials missing or incomplete!! Exiting...")
            exit(1)
        playbook_args += f" os_username={os_username} os_password={os_password}"
        
        if platform_type == "openstack":
            os_project_name = platform_config["configurations"]["platform"][platform_type]["os_project_name"]
            os_project_id = platform_config["configurations"]["platform"][platform_type]["os_project_id"]
            playbook_args += f" os_project_name={os_project_name} os_project_id={os_project_id}"
            for key, value in platform_config["configurations"]["platform"][platform_type]["dynamic_params"][platform_flavor].items():
                playbook_args += f" {key}={value}"
        else:
            print(f"Sorry!! {platform_type.title()} is not yet supported. Exiting...")
            exit(1)

        
        print(f"*****************************The EXTRA-VARS are: {playbook_args}************************************")
        command = ["ansible-playbook", playbook_path, "--extra-vars", playbook_args]
        output = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, timeout=6000)
        print(f'STD OUTPUT LOG is {output.stdout}')
        if output.returncode == 0:
            print(f'Iso Instance managed successfully!')
            if self.instanceState == "present":
                ip_addr_string = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', output.stdout)
                logging.info(f'IP address of new TFDA isolated instance is: {ip_addr_string[-1]}')
                ti.xcom_push(key="iso_env_ip", value=ip_addr_string[-1])
        else:
            print(f"Failed to manage isolated environment! ERROR LOGS:\n{output.stderr}")
        

    def __init__(self,
                 dag,
                 platformType = "openstack",
                 platformFlavor = "ubuntu_gpu",
                 instanceState = "present",
                 taskName = "",
                 **kwargs):

        super().__init__(
            dag=dag,
            # name="create-iso-inst",
            name=taskName,
            python_callable=self.start,
            **kwargs
        )
        self.instanceState = instanceState
