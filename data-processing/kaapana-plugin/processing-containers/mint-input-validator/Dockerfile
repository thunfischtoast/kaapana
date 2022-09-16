FROM local-only/base-python-cpu:0.1.0

LABEL IMAGE="mint-input-validator"
LABEL VERSION="0.1.0"
LABEL CI_IGNORE="True"

COPY files/mint-input-validator.py /kaapanasrc/

CMD ["python3","-u","/kaapanasrc/mint-input-validator.py"]