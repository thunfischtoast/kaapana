#!/usr/bin/env python3
# -*- coding: utf-8; mode: python; indent-tabs-mode: nil; -*-

import os
from opensearchpy import OpenSearch
import requests
import traceback
import json
import logging

# TODO https://discuss.elastic.co/t/reloading-the-index-field-list-automatically/116687
# https://<domain>/meta/api/index_patterns/_fields_for_wildcard?pattern=meta-index&meta_fields=%5B%22_source%22%2C%22_id%22%2C%22_type%22%2C%22_index%22%2C%22_score%22%5D


def import_dashboards():
    global dashboards_url, dashboards_json, osd_xsrf
    print("#")
    print(f"# -> Importing dashboards from {dashboards_json} ...")
    print("#")
    with open(dashboards_json) as f:
        jsonObj = json.load(f)

    for anObject in jsonObj:
        try:
            s_ource = anObject['_source']
            resp = requests.post(f"{dashboards_url}/api/saved_objects/{anObject['_type']}/{anObject['_id']}?overwrite=true",
                                 data='{"attributes":' + json.JSONEncoder().encode(s_ource) + '}', verify=False, headers=osd_xsrf)
            if resp.status_code == 200:
                print(f"# {s_ource['title']}: OK!")
                print("#")

            else:
                print("#")
                print(f"# Could not import dashboard: {s_ource['title']}")
                print(resp.text)
                print(resp.content)
                print("#")
                exit(1)
        except Exception as e:
            logging.error(traceback.format_exc())
            print("#")
            print(f"# Could not import dashboard: {s_ource['title']} -> Exception")
            print("#")
            exit(1)

    print("#")
    print("#")
    print("# Dashboard import successful!")
    print("#")
    print("#")


def set_ohif_template():
    global dashboards_url, domain, https_port, index, osd_xsrf
    print("#")
    print(f"# -> Creating OHIF template ...")
    print("#")
    index_pattern = {
        "attributes": {"title": "{}".format(index),
                       "fieldFormatMap": "{\"0020000D StudyInstanceUID_keyword.keyword\":{\"id\":\"url\",\"params\":{\"urlTemplate\":\"https://"+domain+":"+https_port+"/ohif/IHEInvokeImageDisplay?requestType=STUDY&studyUID={{value}}\",\"labelTemplate\":\"{{value}}\"}}}",
                       }
    }
    try:
        resp = requests.post(f"{dashboards_url}/api/saved_objects/index-pattern/{index}?overwrite=true", data=json.dumps(index_pattern), verify=False, headers=osd_xsrf)
        print(f"# response_code: {resp.status_code}")
        if resp.status_code == 200:
            print('# OHIF-template: OK!')
        else:
            print('# OHIF-template: Error!')
            print(resp.text)
            print(resp.content)
            exit(1)

    except Exception as e:
        logging.error(traceback.format_exc())
        print('# OHIF-template: Error!')
        exit(1)


def create_index():
    global os_client, index
    print("#")
    print(f"# -> Creating index: {index} ...")
    print("#")
    index_name = index
    index_body = {
        "settings": {
            "index": {
                "number_of_shards": 4,
                # "index.mapper.dynamic": True,
                # "number_of_replicas": 0,
                # "index.mapping.total_fields.limit": 6000,
                # "index.max_docvalue_fields_search": 150,
            }
        },
        "mappings":
        {
            "dynamic": 'true',
            "date_detection": 'false',
            "numeric_detection": 'false',
            "dynamic_templates": [
                {
                    "check_integer": {
                        "match_pattern": "regex",
                        "match": "^.*_integer.*$",
                        "mapping": {
                            "type": "long"
                        }
                    }
                },
                {
                    "check_float": {
                        "match_pattern": "regex",
                        "match": "^.*_float.*$",
                        "mapping": {
                            "type": "float"
                        }
                    }
                },
                {
                    "check_datetime": {
                        "match_pattern": "regex",
                        "match": "^.*_datetime.*$",
                        "mapping": {
                            "type": "date",
                                    "format": "yyyy-MM-dd HH:mm:ss.SSSSSS"
                        }
                    }
                },
                {
                    "check_date": {
                        "match_pattern": "regex",
                        "match": "^.*_date.*$",
                        "mapping": {
                            "type": "date",
                                    "format": "yyyy-MM-dd"
                        }
                    }
                },
                {
                    "check_time": {
                        "match_pattern": "regex",
                        "match": "^.*_time.*$",
                        "mapping": {
                            "type": "date",
                                    "format": "HH:mm:ss.SSSSSS"
                        }
                    }
                },
                {
                    "check_timestamp": {
                        "match_pattern": "regex",
                        "match": "^.*timestamp.*$",
                        "mapping": {
                            "type": "date",
                                    "format": "yyyy-MM-dd HH:mm:ss.SSSSSS"
                        }
                    }
                },
                {
                    "check_object": {
                        "match_pattern": "regex",
                        "match": "^.*_object.*$",
                        "mapping": {
                            "type": "object"
                        }
                    }
                },
                {
                    "check_boolean": {
                        "match_pattern": "regex",
                        "match": "^.*_boolean.*$",
                        "mapping": {
                            "type": "boolean"
                        }
                    }
                },
                {
                    "check_array": {
                        "match_pattern": "regex",
                        "match": "^.*_array.*$",
                        "mapping": {
                            "type": "array"
                        }
                    }
                }
            ],
        }
    }
    try:
        response = os_client.indices.create(index_name, body=index_body)
        print("#")
        print("# Response:")
        print(response)
    except Exception as e:
        if str(e.error) == "resource_already_exists_exception":
            print("#")
            print("# Index already exists ...")
            print("#")
        else:
            print("# ")
            print("# Unknown issue while creating the META index ...")
            print("# Error:")
            print(str(e))
            print("#")

    print("#")
    print("# Success! ")
    print("#")


def delete_index(index):
    global os_client
    print("#")
    print(f"# -> Deleting index: {index} ...")
    print("#")
    response = os_client.indices.delete(
        index=index
    )

    print("# Response: ")
    print(response)
    print("#")


print("#")
print("# Started init-container")
print("#")

# os.environ["INIT_DASHBOARDS"] = "True"
# os.environ["INIT_OPENSEARCH"] = "True"
# os.environ["DOMAIN"] = "jip-dktk.dkfz-heidelberg.de"
# os.environ["HTTPS_PORT"] = "443"
# os.environ["INDEX"] = "index-meta"
# os.environ["OS_HOST"] = "jip-dktk"
# os.environ["OS_PORT"] = "80"
# os.environ["DASHBOARDS_URL"] = "https://jip-dktk.dkfz-heidelberg.de/meta"
# os.environ["DASHBOARDS_JSON"] = "/home/jonas/projects/kaapana/services/meta/meta-init/meta-init-chart/files/kibana-dashboard.json"

if __name__ == "__main__":
    print("provisioning...")
    init_dashboards = True if os.getenv('INIT_DASHBOARDS', False).lower() == "true" else False
    init_os = True if os.getenv('INIT_OPENSEARCH', False).lower() == "true" else False

    osd_xsrf = {'osd-xsrf': "true"}

    # stack_version = os.getenv('STACKVERSION', '6.8.12')
    domain = os.getenv('DOMAIN', None)
    https_port = os.getenv('HTTPS_PORT', None)
    index = os.getenv('INDEX', None)
    os_host = os.getenv('OS_HOST', None)
    os_port = os.getenv('OS_PORT', None)
    dashboards_url = os.getenv('DASHBOARDS_URL', None)
    dashboards_json = os.getenv('DASHBOARDS_JSON', None)

    print("#")
    print("# Configuration:")
    print("#")
    print(f"# domain:          {domain}")
    print(f"# https_port:      {https_port}")
    print(f"# index:           {index}")
    print(f"# os_host:         {os_host}")
    print(f"# os_port:         {os_port}")
    print(f"# dashboards_url:  {dashboards_url}")
    print(f"# dashboards_json: {dashboards_json}")
    print(f"# init_dashboards: {init_dashboards}")
    print(f"# init_os:         {init_os}")
    print("#")
    print("#")

    if domain is None:
        print("DOMAIN env not set -> exiting..")
        exit(1)

    # auth = ('admin', 'admin')
    auth = None
    os_client = OpenSearch(
        hosts=[{'host': os_host, 'port': os_port}],
        http_compress=True,  # enables gzip compression for request bodies
        http_auth=auth,
        # client_cert = client_cert_path,
        # client_key = client_key_path,
        use_ssl=False,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        timeout=10,
        # ca_certs = ca_certs_path
    )

    if init_os:
        create_index()

    if init_dashboards:
        import_dashboards()
        set_ohif_template()

    print("#")
    print("#")
    print("# All done - End of init-container.")
    print("#")
    print("#")
