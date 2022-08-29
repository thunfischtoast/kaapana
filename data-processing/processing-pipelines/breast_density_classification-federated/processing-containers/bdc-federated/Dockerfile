FROM local-only/base-python-cpu:0.1.0 

LABEL IMAGE="bdc-federated"
LABEL VERSION="0.1.0"
LABEL CI_IGNORE="False"

COPY files/ /kaapanasrc/

CMD ["python3","-u","/kaapanasrc/run_bdc_federated.py"]