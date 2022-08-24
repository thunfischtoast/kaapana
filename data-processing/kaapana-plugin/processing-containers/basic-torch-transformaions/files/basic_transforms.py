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

# for input parameter defined in Meta Dashboard's UI
with open(os.path.join('/', os.environ["WORKFLOW_DIR"], 'conf/conf.json'), 'r') as f:
    ui_confs = json.load(f)
    dim_of_processed_image = ui_confs['workflow_form']['dim_of_processed_image']
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

        image_tensor = torch.tensor(image_data)               # convert to torch tensor
        image_tensor = image_tensor.squeeze()                 # squeeze dims of size 1 
        print(f"Dimensions of current input image: {image_tensor.size()}.")
        if image_tensor.dim() == dim_of_processed_image:
            image_tensor = image_tensor.permute(2, 0, 1) if dim_of_processed_image == 3 else image_tensor   # permute dims from (H, W, C) to (C, H, W) as torch expects the dims to be, BUT only if tensor is 3D

            # apply transformations
            print(f"Applying selected transformations on (permuted) input tensor with shape: {image_tensor.size()}")
            transformed_image = transformations(image_tensor)     # apply composed transformations
            transformed_image = transformed_image.permute(1, 2, 0) if dim_of_processed_image == 3 else transformed_image  # un-do the previously applied dim permutation if tensor is 3D
            print(f"Shape of output tensor: {transformed_image.size()}")

            transformed_image = transformed_image.cpu().numpy().astype('int16')     # convert back to numpy array
            output_image_data = transformed_image
            output_nifti_img = nib.Nifti1Image(output_image_data, affine=nifti_img_affine, header=nifti_img_header) # save to output nifti file with previoulsy saved affine and header attributes
            nib.save(output_nifti_img, os.path.join(element_output_dir, nifti_file_fname))  # save nifti to output_dir
        
        else:   # dims of sqeezed image_tensor do not match the desired dims of the processed tensor --> write an error log file
            print(f"The dimensions of the current input image and the given dimensions of processed images do NOT match: current image dims = {image_tensor.dim()}; given image dims = {dim_of_processed_image}.")
            
            with open(os.path.join(element_output_dir, "error_log.txt"), "w") as f:
                f.write(f"The dimensions of {nifti_file_fname} in {nifti_file} do not match the specified input dimension of {dim_of_processed_image}." \
                    f"==> {nifti_file_fname} is skipped in the further processing pipeline!")


if __name__ == "__main__":
    main()