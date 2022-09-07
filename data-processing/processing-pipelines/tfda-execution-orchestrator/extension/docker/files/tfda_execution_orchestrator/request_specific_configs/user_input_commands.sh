#!/bin/bash
echo "Hello World"
results_folder='/home/ubuntu/results'
dir='/home/kaapana/minio/test-site-data'

for entry in "$dir"/*
do
  echo "$entry" >> "$results_folder"/out.txt
done
