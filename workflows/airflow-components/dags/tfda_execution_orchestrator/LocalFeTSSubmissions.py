import json
import os
import synapseclient as sc
import getpass
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from synapseclient import Project, Folder, File, Link
from challengeutils import permissions, utils
from minio import Minio

from subprocess import PIPE, run
from airflow.models import DagRun
from airflow.api.common.experimental.get_dag_run_state import get_dag_run_state
from airflow.api.common.experimental.trigger_dag import trigger_dag as trigger
from airflow.api.common.experimental.get_dag_run_state import get_dag_run_state
from kaapana.blueprints.kaapana_utils import generate_run_id
from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapana.blueprints.kaapana_global_variables import BATCH_NAME, WORKFLOW_DIR

class LocalFeTSSubmissions(KaapanaPythonBaseOperator):
    def send_email(self, email_address, cc_address, message, filepath, subm_id):
        assert(email_address != "", "Please specify the recipient of the Email")
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("SENDING EMAIL: {}".format(email_address))
        # print("MESSAGE: {}".format(message))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++")
        from_address = ""
        sending_ts = datetime.now()

        sub = f'BraTS Evaluation Result for Submission (ID: {subm_id})'
        
        msgRoot = MIMEMultipart('related')
        msgRoot['From'] = from_address
        msgRoot['To'] = email_address
        if cc_address is not None and cc_address != "":
            msgRoot['Cc'] = cc_address
        msgRoot['Subject'] = sub

        msgAlt = MIMEMultipart('alternative')
        msgRoot.attach(msgAlt)
        
        msgTxt = MIMEText(message, 'html')
        msgAlt.attach(msgTxt)
        
        if filepath is not None and filepath != "":
            with open(filepath,'rb') as file:
                attachment = MIMEApplication(file.read())
            attachment.add_header('Content-Disposition', 'attachment', filename=f"results_{subm_id}_{sending_ts.strftime('%Y-%m-%d')}.zip")
            msgRoot.attach(attachment)

        s = smtplib.SMTP(host='mailhost2.dkfz-heidelberg.de', port=25)
        s.sendmail(from_address, msgRoot["To"].split(", ") + msgRoot["Cc"].split(", "), msgRoot.as_string())
        s.quit()
    
    def get_most_recent_dag_run(self, dag_id):
        dag_runs = DagRun.find(dag_id=dag_id)
        dag_runs.sort(key=lambda x: x.execution_date, reverse=True)
        return dag_runs[0] if dag_runs else None

    def start(self, ds, ti, **kwargs):

        # Create client with access and secret key.
        client = Minio("s3.cos.dkfz-heidelberg.de", "", "")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        subm_logs_path = os.path.join(base_dir, "data", "subm_logs")
        subm_results_path = os.path.join(base_dir, "subm_results")
        singularity_images_path = os.path.join(base_dir, "singularity_images")

        subm_dict = {}
        subm_dict_path = os.path.join(subm_logs_path, "subm_dict.json")

        if os.path.exists(subm_dict_path):
            with open(subm_dict_path, "r") as fp_:
                subm_dict = json.load(fp_)

        print("Get BraTS containers list from DKFZ S3...")       
        objects = client.list_objects("e230-fets", prefix="extra_submissions/")
        for obj in objects:
            print("*********************************************")
            print(f"S3 Bucket name: {obj.bucket_name}")
            print(f"Container filename: {obj.object_name}")
            container_file = obj.object_name.split('/')[-1]
            container_name = container_file.split(".sif")[0]
            container_filepath = os.path.join(singularity_images_path, container_file)
            if os.path.exists(container_filepath):
                print(f"Container file already exists locally! Skipping download...")
            else:
                print(f"Downloading container: {container_name}...")
                try:
                    client.fget_object(obj.bucket_name, obj.object_name, file_path=container_filepath)
                except Exception as e:
                    print(f"Error while trying to download container: {e}!! Skipping...")
                    subm_dict[container_name] = "skipped"
                    continue

            if container_name not in subm_dict or subm_dict.get(container_name) != "success":                
                print("Triggering isolated execution orchestrator...")
                self.trigger_dag_id = "tfda-execution-orchestrator"
                self.conf = kwargs['dag_run'].conf
                self.conf["subm_id"] = container_name
                dag_run_id = generate_run_id(self.trigger_dag_id)
                try:
                    trigger(dag_id=self.trigger_dag_id, run_id=dag_run_id, conf=self.conf,
                                    replace_microseconds=False)
                except Exception as e:
                    print(f"Error while triggering isolated workflow for submission: {container_name}...")
                    print(e)
                    subm_dict[container_name] = "exception"

                dag_run = self.get_most_recent_dag_run(self.trigger_dag_id)
                if dag_run:
                    print(f"The latest isolated workflow has been triggered at: {dag_run.execution_date}!!!")

                dag_state = get_dag_run_state(dag_id="tfda-execution-orchestrator", execution_date=dag_run.execution_date)

                while dag_state["state"] != "failed" and dag_state['state'] != "success":
                    dag_run = self.get_most_recent_dag_run(self.trigger_dag_id)
                    dag_state = get_dag_run_state(dag_id="tfda-execution-orchestrator", execution_date=dag_run.execution_date)                        
                
                sending_ts = datetime.now()
                subm_results_file = f"{subm_results_path}/results_{container_name}_{sending_ts.strftime('%Y-%m-%d')}.zip"

                if os.path.exists(subm_results_file):
                    subm_results = subm_results_file
                else:
                    subm_results = None
                
                recipient = ""
                cc_address = ""

                if dag_state["state"] == "failed":
                    print(f"**************** The evaluation of submission {container_name} has FAILED ****************")
                    subm_dict[container_name] = "failed"
                    ## Email report
                    message = """
                    <html>
                        <head></head>
                        <body>
                            Dear {},<br><br>
                            Thank you for your submission (ID: {}) to the FeTS challenge 2022 task 2! We tested your container on the toy dataset and you can download the results from:<br>
                            Unfortunately, the evaluation of your container was not successful; please check the logs (medperf.log), which contain some debugging information. If you have problems identifying the issue, just respond to all from this email and we will do our best to get your submission running.<br>
                            <br><br>
                            Yours sincerely,<br>
                            The FeTS challenge organizers <br>
                        </body>
                    </html>
                    """.format(recipient, container_name)
                    self.send_email(email_address=recipient, cc_address=cc_address, message=message, filepath=subm_results, subm_id=container_name)
                if dag_state["state"] == "success":
                    print(f"**************** The evaluation of submission {container_name} was SUCCESSFUL ****************")
                    subm_dict[container_name] = "success"
                    ## Email report
                    message = """
                    <html>
                        <head></head>
                        <body>
                            Dear {},<br><br>
                            Thank you for your submission (ID: {}) to the FeTS challenge 2022 task 2! We tested your container on the toy dataset and you can download the results from:<br>
                            Looks like there were no fatal errors during the evaluation of your container, great! However, to make sure everything ran correctly, please check the results.yaml file and compare it with your local results. Watch out for discrepancies, as they may indicate reproducibility issues. If you have any questions, feel free to post them in the <a href="https://www.synapse.org/#!Synapse:syn28546456/discussion/default">discussion forum</a> or respond to all from this email directly.<br>
                            <br><br>
                            Cheers!<br>
                            The FeTS challenge organizers <br>
                        </body>
                    </html>
                    """.format(recipient, container_name)
                    self.send_email(email_address=recipient, cc_address=cc_address, message=message, filepath=subm_results, subm_id=container_name)
            else:
                print("Submission already SUCCESSFULLY evaluated!!!!")

            print(f"Saving submission dict...")
            with open(subm_dict_path, "w") as fp_:
                json.dump(subm_dict, fp_)

    def __init__(self,
                 dag,
                 **kwargs):

        super().__init__(
            dag=dag,
            name="evaluate-submissions",
            python_callable=self.start,
            **kwargs
        )