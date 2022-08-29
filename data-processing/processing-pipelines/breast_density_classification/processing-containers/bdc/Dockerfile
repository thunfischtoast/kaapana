FROM local-only/base-python-gpu:0.1.0 

LABEL IMAGE="breast-density-classification"
LABEL VERSION="0.1.0"
LABEL CI_IGNORE="False"

COPY files/requirements.txt /kaapanasrc/requirements.txt

RUN pip install --upgrade pip && pip install -r /kaapanasrc/requirements.txt

COPY files/* /kaapanasrc/
# COPY ddsm_data /

# WORKDIR /

CMD ["python3","-u","/kaapanasrc/centralized_main.py"]