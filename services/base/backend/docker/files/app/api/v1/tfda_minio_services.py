
from flask import jsonify, abort

from . import api_v1

from minio import Minio
import os
import requests
import json
from datetime import datetime
import socket



#Production
_minio_host='minio-service.store.svc'


_minio_port='9000'

#todo: add charts values fetched from registry instead custom values
def returnChartsDetails():
  return json.dumps({'chart_name': 'test', 'url': 'www.test.com'})

#Initializing Minio Client
minioClient = Minio(_minio_host+":"+_minio_port,
                            access_key="kaapanaminio",
                        secret_key="Kaapana2020",
                        
                        secure=False)
# test runs
FEDERATED_HOSTS = ['10.128.129.221','10.128.128.153']

@api_v1.route('/minio/bucketsandhosts/')
def tfda_collect_all_site_buckets():
    """Return List of Minio buckets
    To List Buckets from all participating sites
    ---
    tags:
      - TFDA Minio
   
    responses:
      200:
        description: Return List of Minio buckets
    """
    all_buckets = {}
    all_buckets['minio'] = []
    _minio_port = "9000"
    for i in FEDERATED_HOSTS:
      #print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$  INSIDE ITERATION $$$$$$$$$$$$$$$$$$')
      #test runs
      _minio_host = i
      client = Minio(_minio_host+":"+_minio_port,
                            access_key="kaapanaminio",
                        secret_key="Kaapana2020",
                        
                        secure=False)
      buckets = client.list_buckets()
      for bucket in buckets:
        
        all_buckets['minio'].append({'bucket_name':str(bucket.name),'host':i})
        #print(bucket.name, bucket.creation_date)
        
    print(all_buckets)
    
       
        
        
    return json.dumps(all_buckets)

@api_v1.route('/minio/charts/getcharts/')
def tfda_get_charts():
    """Return List of Charts
    Return  List of Charts
    ---
    tags:
      - TFDA Charts
   
    responses:
      200:
        description: Return List of Charts
    """
   
    return returnChartsDetails()