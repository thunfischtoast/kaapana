FROM local-only/base-python-cpu:0.1.0

LABEL IMAGE="mint-xml-parser"
LABEL VERSION="0.1.0"
LABEL CI_IGNORE="True"

COPY files/mint-xml-parser.py /kaapanasrc/

CMD ["python3","-u","/kaapanasrc/mint-xml-parser.py"]