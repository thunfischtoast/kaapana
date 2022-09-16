import glob
import os
from os.path import dirname
from pathlib import Path

# From the template
import pydicom

batch_folders = sorted(
    [f for f in glob.glob(os.path.join('/', os.environ['WORKFLOW_DIR'], os.environ['BATCH_NAME'], '*'))])

for batch_element_dir in batch_folders:

    element_input_dir = os.path.join(batch_element_dir, os.environ['OPERATOR_IN_DIR'])
    element_output_dir = os.path.join(batch_element_dir, os.environ['OPERATOR_OUT_DIR'])
    if not os.path.exists(element_output_dir):
        os.makedirs(element_output_dir)

    # The processing algorithm
    print(f'Checking {element_input_dir} for dcm files and writing results to {element_output_dir}')
    dcm_files = sorted(glob.glob(os.path.join(element_input_dir, "*.dcm"), recursive=True))

    if len(dcm_files) == 0:
        print("No dcm file found!")
        exit(0)
    else:
        for dcm_file in dcm_files:
            print(f'Validating DCM-file: {dcm_file}')
            target_file = str(Path(dcm_file.replace(dirname(dcm_file), element_output_dir)).with_suffix('.xml'))
            dcm = pydicom.dcmread(dcm_file)
            if not (dcm.get('Manufacturer') == 'Mint Medical GmbH' and dcm.get('Modality') == 'OT'):
                print(
                    'DICOM does not contain Manufacturer tag Mint Medical GmbH '
                    'and does not have the modality OT'
                )
                continue

            with open(target_file, "w") as xml_file:
                xml_file.write(dcm[0x9071, 0x1000].value.decode("UTF-8").replace("\x00", ""))

            print(f'Successfully extracted XML file: {dcm_file}')
