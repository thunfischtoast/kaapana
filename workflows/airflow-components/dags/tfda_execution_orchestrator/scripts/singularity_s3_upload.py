import os
import glob
from subprocess import run, PIPE
import json

"""
    Steps before running the script:
    
    Download Minio Client
    wget https://dl.min.io/client/mc/release/linux-amd64/mc
    chmod +x mc
    
    Configure Minio
    ./mc alias set dkfz-s3 https://s3.cos.dkfz-heidelberg.de  (use read-write keys)
    ./mc alias set dkfz-s3-pub https://s3.dkfz.de  (use read only keys)

    Credentials/keys are on slack
"""

directory = os.path.dirname(os.path.abspath(__file__))
singularity_dir = os.path.join(directory, "singularity_images")

subm_dict = {}
subm_dict_path = os.path.join(directory, "singularity_dict.json")
for filename in glob.iglob(f"{directory}/*.sif"):
    print(filename)
    print("Uploading singularity image file to S3")
    command = ["./mc", "cp", filename, "dkfz-s3-int/e230-fets/singularity_containers/"]
    output = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, timeout=6000)
    print(f'STD OUTPUT LOG is {output.stdout}')
    if output.returncode == 0:
        print(f'File uploaded successfully! See full logs above...')
        print("Generating share URL...")
        filename = filename.split("/")[-1]
        command2 = ["./mc", "share", "download", f"dkfz-s3-pub/e230-fets/singularity_containers/{filename}"]
        output2 = run(command2, stdout=PIPE, stderr=PIPE, universal_newlines=True, timeout=6000)
        url = output2.stdout.partition("Share: ")[2].rstrip("\r\n")
        subm_dict[filename] = url

        with open(subm_dict_path, "w") as fp_:
            json.dump(subm_dict, fp_)
        
    else:
        print(f"FAILED to upload file! See ERROR LOGS:\n{output.stderr}")