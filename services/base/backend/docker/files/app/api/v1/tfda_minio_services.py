from typing import MappingView
from flask import jsonify, abort, request

from . import api_v1

from minio import Minio
import os
import requests
import json
from datetime import datetime
import socket

import os
import sys
import getpass
from argparse import ArgumentParser
import traceback
import json
from subprocess import PIPE, run
import time

os.environ["HELM_EXPERIMENTAL_OCI"] = "1"

kaapana_int_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
kaapana_int_dir = os.path.join(kaapana_int_dir, "v1", "tfda-mvp1-iso-env-pipeline")
# print("////////////////////////////////////////////////////////////", kaapana_int_dir)
scripts_dir = os.path.join(kaapana_int_dir, "CI", "scripts")
# print("////////////////////////////////////////////////////////////", scripts_dir)
playbook_dir = os.path.join(kaapana_int_dir, "CI", "ansible_playbooks")
# print("////////////////////////////////////////////////////////////")
# print(sys.path)
sys.path.insert(1, scripts_dir)
import ci_playbooks


# defaults
""" os_image = "ubuntu"
volume_size = "100"
instance_flavor = "dkfz-8.16"
ssh_key = "kaapana"
os_project_name = "E230-DKTK-JIP"
os_project_id = "969831bf53424f1fb318a9c1d98e1941"
instance_name = "tfda-iso-env-test" """

# E230
os_image = "ubuntu"
volume_size = "100"
instance_flavor = "dkfz-8.16"
ssh_key = "kaapana"
os_project_name = "E230"
os_project_id = "1396d67192c24eb7ab606cfae1151208"
instance_name = "tfda-iso-env-test"

username = "s669m"
password = "Heidelberg2021!"
registry_user = "nU9A-xWex6tMzJzc5ksu"
registry_pwd = "tfdachartsregistrymaintainer"
registry_url = "registry.hzdr.de/santhosh.parampottupadam/tfdachartsregistry"
delete_instance = True

debug_mode = False

# Production
_minio_host = "minio-service.store.svc"


_minio_port = "9000"


delete_instance = delete_instance  # args.delete_instance
username = username if username is not None else username
password = password if password is not None else password
registry_user = registry_user if registry_user is not None else registry_user
registry_pwd = registry_pwd if registry_pwd is not None else registry_pwd
registry_url = registry_url if registry_url is not None else registry_url
instance_name = instance_name if instance_name is not None else instance_name
volume_size = volume_size
instance_flavor = instance_flavor
ssh_key = ssh_key
os_project_name = os_project_name if os_project_name is not None else os_project_name
os_image = os_image if os_image is not None else os_image


def handle_logs(logs):
    global debug_mode
    for log in logs:
        if "loglevel" in log and log["loglevel"].lower() != "info":
            print(json.dumps(log, indent=4, sort_keys=True))
            exit(1)
        elif debug_mode:
            print(json.dumps(log, indent=4, sort_keys=True))


def start_os_instance():
    return_value, logs = ci_playbooks.start_os_instance(
        username=username,
        password=password,
        instance_name=instance_name,
        project_name=os_project_name,
        project_id=os_project_id,
        os_image=os_image,
        volume_size=volume_size,
        instance_flavor=instance_flavor,
        ssh_key=ssh_key,
    )
    return return_value


def install_server_dependencies(target_hosts):
    return_value, logs = ci_playbooks.start_install_server_dependencies(
        target_hosts=target_hosts,
        remote_username=os_image,
        local_script=True,
        suite_name="Get new instance",
    )
    handle_logs(logs)
    return return_value


def deploy_platform(target_hosts):
    return_value, logs = ci_playbooks.deploy_platform(
        target_hosts=target_hosts,
        remote_username=os_image,
        registry_user=registry_user,
        registry_pwd=registry_pwd,
        registry_url=registry_url,
        local_script=True,
        platform_name="Kaapana platform",
    )
    handle_logs(logs)

    return return_value


def run_algo_on_data(target_hosts, user_request_file):
    bucket_chart_details_dict = _extract_user_request(file_path=user_request_file)
    compressed_chart_details_dict = _pull_chart_and_compress(
        registry_user=registry_user,
        registry_pwd=registry_pwd,
        chart_details=bucket_chart_details_dict["chart_details"],
    )
    return_value, logs = ci_playbooks.copy_data_algo(
        target_hosts=target_hosts,
        bucket_name=bucket_chart_details_dict["bucket_name"],
        chart_path=compressed_chart_details_dict["compressed_chart_path"],
        chart_filename=compressed_chart_details_dict["compressed_chart_name"],
    )
    return_value, logs = (
        ci_playbooks.run_algo_and_send_result(
            target_hosts=target_hosts,
            chart_filename=compressed_chart_details_dict["compressed_chart_name"],
        )
        if return_value != "FAILED"
        else "FAILED"
    )


def _extract_user_request(file_path=""):
    f = open(file_path)
    user_request = json.load(f)
    bucket_name = user_request["minio"]["bucket_name"]
    chart_details = user_request["charts"]
    f.close()
    return {"bucket_name": bucket_name, "chart_details": chart_details}


def _pull_chart_and_compress(registry_user, registry_pwd, chart_details=""):
    chart_name = chart_details["chart_name"]
    chart_version = chart_details["chart_version"]
    ##TODO: the following part can also be implemented in Ansible, but is only executed in localhost
    print("Logging into the Helm registry...")
    command = [
        "helm",
        "registry",
        "login",
        "-u",
        "{}".format(registry_user),
        "-p",
        "{}".format(registry_pwd),
        "{}".format(registry_url),
    ]
    output = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, timeout=5)

    loop = 6
    for i in range(loop):
        print("Pulling chart...")
        command2 = [
            "helm",
            "chart",
            "pull",
            "{}/{}:{}".format(registry_url, chart_name, chart_version),
        ]
        output2 = run(
            command2, stdout=PIPE, stderr=PIPE, universal_newlines=True, timeout=5
        )
        if output2.returncode != 0 and i < (loop - 1):
            print("Failed to pull chart, will try again")
            time.sleep(2)
        elif output2.returncode == 0:
            print("Chart successfully pulled!")
            break
        elif i == (loop - 1):
            print("Chart could not be pulled, exiting...")
            exit(1)

    print("Creating compressed chart file...")
    command3 = [
        "helm",
        "chart",
        "export",
        "{}/{}:{}".format(registry_url, chart_name, chart_version),
        "-d",
        "{}".format(os.path.dirname(os.path.abspath(__file__))),
    ]
    output3 = run(
        command3, stdout=PIPE, stderr=PIPE, universal_newlines=True, timeout=5
    )
    command4 = [
        "tar",
        "-cvzf",
        "{}-{}.tgz".format(chart_name, chart_version),
        "{}".format(chart_name),
    ]
    output4 = run(
        command4, stdout=PIPE, stderr=PIPE, universal_newlines=True, timeout=5
    )
    if output4.returncode != 0:
        print("Could not create compressed chart file, exiting...")
        exit(1)
    else:
        print("Compressed chart successfully!")
        return {
            "compressed_chart_path": "{}".format(
                os.path.dirname(os.path.abspath(__file__))
            ),
            "compressed_chart_name": "{}-{}.tgz".format(chart_name, chart_version),
        }


def remove_platform(target_hosts):
    return_value, logs = ci_playbooks.delete_platform_deployment(
        target_hosts=target_hosts, platform_name="Kaapana platform"
    )
    handle_logs(logs)

    return return_value


def purge_filesystem(target_hosts):
    return_value, logs = ci_playbooks.purge_filesystem(
        target_hosts=target_hosts, platform_name="Kaapana platform"
    )
    handle_logs(logs)

    return return_value


def delete_os_instance():
    return_value, logs = ci_playbooks.delete_os_instance(
        username=username,
        password=password,
        instance_name=instance_name,
        os_project_name=os_project_name,
        os_project_id=os_project_id,
    )
    handle_logs(logs)

    return return_value


def print_success(host):
    print(
        """
    The installation was successfull!

    visit https://{}

    Default user credentials:
    username: kaapana
    password: kaapana

    """.format(
            host
        )
    )

    return "OK"


def launch():
    print(
        " !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!   Lanuch Method called from user_choice_submission API !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    )
    global os_image, volume_size, instance_flavor, ssh_key, os_project_name, instance_name, username, password, registry_user, registry_pwd, registry_url

    os.chdir(playbook_dir)
    if username is None:
        username_template = "kaapana-ci"
        username = input("OpenStack username [{}]:".format(username_template))
        username = (
            username_template if (username is None or username == "") else username
        )

    if password is None:
        password = getpass.getpass("OpenStack password: ")

    if registry_user is None:
        registry_user = input("GitLab username:")
        # TODO: throw error if no input from user

    if registry_pwd is None:
        registry_pwd = getpass.getpass("GitLab password: ")

    if os_project_name is None:
        os_project_template = "E230-DKTK-JIP"
        os_project_name = input("OpenStack project [{}]:".format(os_project_template))
        os_project_name = (
            os_project_template
            if (os_project_name is None or os_project_name == "")
            else os_project_name
        )

    if registry_url is None:
        registry_url_template = "registry.hzdr.de/kaapana/kaapana"
        registry_url = input("OpenStack project [{}]:".format(registry_url_template))
        registry_url = (
            registry_url_template
            if (registry_url is None or registry_url == "")
            else registry_url
        )

    if instance_name is None:
        instance_name_template = "{}-kaapana-instance".format(getpass.getuser())
        instance_name = input(
            "OpenStack instance name [{}]:".format(instance_name_template)
        )
        instance_name = (
            instance_name_template
            if (instance_name is None or instance_name == "")
            else instance_name
        )

    ## Get user request path
    cwd = os.path.dirname(os.path.abspath(__file__))
    user_request_file = os.path.join(cwd, "user_requests", "user_request.json")

    # instance_ip_address = "10.128.130.133"
    # instance_ip_address = "10.128.129.58"
    instance_ip_address = start_os_instance()
    result = (
        install_server_dependencies(target_hosts=[instance_ip_address])
        if instance_ip_address != "FAILED"
        else "FAILED"
    )
    result = (
        deploy_platform(target_hosts=[instance_ip_address])
        if result != "FAILED"
        else "FAILED"
    )
    result = print_success(instance_ip_address) if result != "FAILED" else "FAILED"
    result = run_algo_on_data(
        target_hosts=[instance_ip_address], user_request_file=user_request_file
    )  # if result != "FAILED" else "FAILED"
    result = delete_os_instance() if delete_instance else "SKIPPED"
    # flask post status to host instances


# tfdatodo: add charts values fetched from registry instead custom values
def returnChartsDetails():

    return json.dumps({"chart_name": "test", "url": "www.test.com"})


# Initializing Minio Client
minioClient = Minio(
    _minio_host + ":" + _minio_port,
    access_key="kaapanaminio",
    secret_key="Kaapana2020",
    secure=False,
)
# test runs
FEDERATED_HOSTS = ["10.128.129.221", "10.128.128.153"]


@api_v1.route("/minio/bucketsandhosts/")
def tfda_collect_all_site_buckets():
    """Return List of Minio buckets
    To List Buckets from all participating sites
    ---
    tags:
      - TFDA Services

    responses:
      200:
        description: Return List of Minio buckets
    """
    all_buckets = {}
    all_buckets["minio"] = []
    _minio_port = "9000"
    for i in FEDERATED_HOSTS:

        _minio_host = i
        client = Minio(
            _minio_host + ":" + _minio_port,
            access_key="kaapanaminio",
            secret_key="Kaapana2020",
            secure=False,
        )
        buckets = client.list_buckets()
        for bucket in buckets:

            all_buckets["minio"].append({"bucket_name": str(bucket.name), "host": i})
            # print(bucket.name, bucket.creation_date)

    print(all_buckets)

    return json.dumps(all_buckets)


@api_v1.route("/minio/charts/getcharts/")
def tfda_get_charts():
    """Return List of Charts
    Return  List of Charts
    ---
    tags:
      - TFDA Services

    responses:
      200:
        description: Return List of Charts
    """

    return returnChartsDetails()


@api_v1.route("/minio/tfda-get-request/<string:reqData>", methods=["GET", "POST"])
def query_example(reqData):
    """Serving Get Requests
    ---
    tags:
      - TFDA Services
    parameters:
      - name: reqData
        in: path
        type: string
        required: true
        description: Serving get requests
    responses:
      200:
        description: Serving get requests
    """
    # language = request.args.get(reqData)

    return """<h1>The test value for from post response is : {}</h1>""".format(reqData)


@api_v1.route("/minio/tfda/userchoicesubmission", methods=["GET", "POST"])
def user_choice_submission():

    data = json.loads(request.data)
    print(
        "!!!!!!!!!!!!!!!!!!!!!!! user choice submission API Triggered from frond end !!!!!!!!!!!!!!!!!!!!!"
    )
    print(data)
    launch()
    return data

    # return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
