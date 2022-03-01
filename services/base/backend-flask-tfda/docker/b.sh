#!/bin/bash

sudo docker build -t registry.hzdr.de/santhosh.parampottupadam/tfdamvp1/kaapana-backend:0.0.1 .
sudo docker push registry.hzdr.de/santhosh.parampottupadam/tfdamvp1/kaapana-backend:0.0.1
microk8s kubectl delete pods -l app-name=backend -n base