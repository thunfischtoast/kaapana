#!/bin/bash
echo "Hello World"
result_folder='/home/ubuntu/results'
dir='/home/kaapana/minio/test_site_data'

for entry in "$dir"/*
do
  echo "$entry" > "$result_folder"/out.txt
done


