FROM local-only/base-python-gpu:0.1.0 

LABEL IMAGE="basic-transformations"
LABEL VERSION="0.1.0"
LABEL CI_IGNORE="False"

COPY files/requirements.txt /kaapanasrc/requirements.txt
RUN pip install --upgrade pip && pip install -r /kaapanasrc/requirements.txt

COPY files/basic_transforms.py /kaapanasrc/basic_transforms.py

CMD ["python3","-u","/kaapanasrc/basic_transforms.py"]
