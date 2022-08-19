import os
import glob
import json

import torch
from torchvision import transforms
import nibabel as nib


# For local testing
# os.environ["WORKFLOW_DIR"] = "home/m391k/Documents/my_documents/Programming/RACOON_code/RACOON-UME_BCA/BasicTorchTransformationOperator/dev_image"
# os.environ["BATCH_NAME"] = "batch"
# os.environ["OPERATOR_IN_DIR"] = "get-input-data"
# os.environ["OPERATOR_OUT_DIR"] = "basic-transform"
# os.environ['CENTER_CROPPING'] = "false"
# os.environ['CENTER_CROPPING_SIZE'] = "400"

# get platform ui inputs as environmental variables in container
# CENTER_CROPPING = os.environ['CENTER_CROPPING']             # can be true or false (but as string)
# CENTER_CROPPING_SIZE = os.environ['CENTER_CROPPING_SIZE']

# for input parameter defined in Meta Dashboard's UI
with open(os.path.join('/', os.environ["WORKFLOW_DIR"], 'conf/conf.json'), 'r') as f:
    ui_confs = json.load(f)
    center_cropping = ui_confs['workflow_form']['image_transform_center_cropping']
    center_cropping_size = ui_confs['workflow_form']['image_transform_center_cropping_value']
    

def compose_transforms():
    transform_list = []

    if center_cropping:
        transform_list.append(transforms.CenterCrop(int(center_cropping_size)))
    # further transformations ...

    if len(transform_list) == 0:
        raise ValueError("C'mon, you've integrated that transformation operator into your pipeline but haven't specified a single transform?!")

    transformations = transforms.Compose(transform_list)

    return transformations

def main():

    # get specified transformations
    transformations = compose_transforms()

    batch_folders = sorted([f for f in glob.glob(os.path.join('/', os.environ['WORKFLOW_DIR'], os.environ['BATCH_NAME'], '*'))])
    for batch_element_dir in batch_folders:
    
        element_input_dir = os.path.join(batch_element_dir, os.environ['OPERATOR_IN_DIR'])
        element_output_dir = os.path.join(batch_element_dir, os.environ['OPERATOR_OUT_DIR'])
        if not os.path.exists(element_output_dir):
            os.makedirs(element_output_dir)

        # The processing algorithm
        print(f'Checking {element_input_dir} for nifti files.')
        nifti_files = sorted(glob.glob(os.path.join(element_input_dir, "*.nii.gz*"), recursive=True))
        nifti_file = nifti_files[0] # should be just one nifti file
        nifti_file_fname = nifti_file.split('/')[5]

        nifti_img = nib.load(nifti_file)                      # load input nifti file
        output_nifti_img = nib.load(nifti_file)               # load output nifti file
        image_data = nifti_img.get_fdata()                    # get image data from input nifti file
        output_image_data = output_nifti_img.get_fdata()      # get image data from output nifti file
        nifti_img_affine = nifti_img.affine                   # get affine data from input nifti file
        nifti_img_header = nifti_img.header                   # get header from input nifti file

        image_tensor = torch.tensor(image_data)         # convert to torch tensor
        image_tensor = image_tensor.permute(2, 0, 1)    # permute dims from (H, W, C) to (C, H, W) as torh expects the dims to be

        # apply transformations
        print("Applying selected transformations ...")
        transformed_image = transformations(image_tensor).permute(1, 2, 0)  # transformations and un-do the previously applied dim permutation

        transformed_image = transformed_image.cpu().numpy()     # convert back to numpy array
        output_image_data = transformed_image
        output_nifti_img = nib.Nifti1Image(output_image_data, affine=nifti_img_affine, header=nifti_img_header) # save to output nifti file with previoulsy saved affine and header attributes
        nib.save(output_nifti_img, os.path.join(element_output_dir, nifti_file_fname))  # save nifti to output_dir


if __name__ == "__main__":
    main()