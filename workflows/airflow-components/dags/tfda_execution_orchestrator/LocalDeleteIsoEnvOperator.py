import os
import glob
import zipfile
from subprocess import PIPE, run

from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapana.blueprints.kaapana_global_variables import BATCH_NAME, WORKFLOW_DIR


class LocalDeleteIsoEnvOperator(KaapanaPythonBaseOperator):
    def start(self, ds, **kwargs):
        print("Delete isolated environment...")

        operator_dir = os.path.dirname(os.path.abspath(__file__))
        playbooks_dir = os.path.join(operator_dir, "ansible_playbooks")
        playbook_path = os.path.join(playbooks_dir, "05_delete_"+self.platformType+"_instance.yaml")
        if not os.path.isfile(playbook_path):
            print("playbook yaml not found.")
            exit(1)
        
        platform_config = kwargs["dag_run"].conf["platform_config"]
        print(f"**************************Platform config is: {platform_config}**************************")
        
        extra_vars = ""
        os_username = platform_config["configurations"]["username"]
        os_password = platform_config["configurations"]["password"]
        extra_vars += f"os_username={os_username} os_password={os_password}"
        if self.platformType == "openstack":
            os_project_name = platform_config["configurations"]["platform"][self.platformType]["os_project_name"]
            os_project_id = platform_config["configurations"]["platform"][self.platformType]["os_project_id"]
            extra_vars += f" os_project_name={os_project_name} os_project_id={os_project_id}"
            for key, value in platform_config["configurations"]["platform"][self.platformType]["dynamic_params"][self.platformFlavor].items():
                extra_vars += f" {key}={value}"
        else:
            print(f"Sorry!! {self.platformType} is not yet supported. Exiting now...")
            exit(1)

        
        print(f"*****************************The EXTRA-VARS are: {extra_vars}************************************")
        command = ["ansible-playbook", playbook_path, "--extra-vars", extra_vars]
        output = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, timeout=6000)
        print(f'STD OUTPUT LOG is {output.stdout}')
        if output.returncode == 0:
            print(f'Instance deleted successfully! See full logs above...')
        else:
            print(f"FAILED to delete instance! See ERROR LOGS:\n{output.stderr}")
            exit(1)

    def __init__(self,
                 dag,
                 platformType = "openstack",
                 platformFlavor = "ubuntu_gpu",
                 **kwargs):

        super().__init__(
            dag=dag,
            name="delete-iso-env",
            python_callable=self.start,
            **kwargs
        )
        self.platformType = platformType
        self.platformFlavor = platformFlavor
