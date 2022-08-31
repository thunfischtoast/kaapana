import os
import glob
import json
import datetime
import csv
import numpy as np
import pydicom as dicom
import shutil

from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapana.blueprints.kaapana_global_variables import BATCH_NAME, WORKFLOW_DIR
from kaapana.operators.HelperCaching import cache_operator_output

class LocalTrainValDataSplitOperator(KaapanaPythonBaseOperator):

    @cache_operator_output
    def start(self, ds, **kwargs):
        # load conf inputs
        conf = kwargs['dag_run'].conf

        # extract ratio_train_split from config
        ratio_train_split = float(conf['workflow_form']['train_split'])
        ratio_val_split = round((1.0 - ratio_train_split), 2)
        print(f"We are starting to split the data by the ratios: train_split={ratio_train_split}, val_split={ratio_val_split}")

        # load .csv-files from minio to metadata_all
        metadata_fnames = glob.glob(os.path.join('/data', kwargs['dag_run'].run_id, '*.csv'), recursive=True)
        if metadata_fnames != None:
            print("Yippie, we've found some metdadata_fnames :-)")
            metadata_all = []
            for i in range(len(metadata_fnames)):
                with open(metadata_fnames[i], 'r') as f:
                    reader = csv.reader(f)
                    header = next(reader)
                    if i==0:
                        metadata_all.append(header)
                    for row in reader:
                        metadata_all.append(row)

        # load unique names of selected data samples from input_operator
        img_data_dir = os.path.join('/data', kwargs['dag_run'].run_id, 'batch/')
        output_data_dir = os.path.join('/data', kwargs['dag_run'].run_id, self.operator_out_dir)
        os.makedirs(output_data_dir, exist_ok=True)
        print(f"img_data_dir = {img_data_dir} ; output_data_dir = {output_data_dir}")
        imagedata_fnames = glob.glob(os.path.join(img_data_dir, '**/*.dcm'), recursive=True)

        # find selected data samples in .csv and create a list
        metadata_all_t = np.array(metadata_all).T.tolist()
        selected_imgs = []
        for i in range(len(imagedata_fnames)):
            dcm_f = dicom.dcmread(imagedata_fnames[i])
            unique_dcm_name = os.path.join(dcm_f.PatientID.split('.')[0], dcm_f.StudyInstanceUID, dcm_f.SeriesInstanceUID, '000000.dcm')
            index_in_metadata = [i for i, s in enumerate(metadata_all_t[11]) if unique_dcm_name in s][0] if len([i for i, s in enumerate(metadata_all_t[11]) if unique_dcm_name in s])!=0 else None
            index_in_metadata = [i for i, s in enumerate(metadata_all_t[12]) if unique_dcm_name in s][0] if len([i for i, s in enumerate(metadata_all_t[12]) if unique_dcm_name in s])!=0 else index_in_metadata
            index_in_metadata = [i for i, s in enumerate(metadata_all_t[13]) if unique_dcm_name in s][0] if len([i for i, s in enumerate(metadata_all_t[13]) if unique_dcm_name in s])!=0 else index_in_metadata
            selected_imgs.append(metadata_all[index_in_metadata])

            # copy dcm files into train_val_datasplit operator's output dir
            print(f"imagedata_fname={imagedata_fnames[i]} ; target={output_data_dir}")
            shutil.copy(src=imagedata_fnames[i], dst=output_data_dir)

        # assigned selected data samples randomly to train and val dataset by adding another column to "selected_imgs" table (aka lists in list)
        # generate a vector which contains 0 = train and 1 = val dataset assignments
        # train_val_assigns = np.random.choice([0, 1], size=len(selected_imgs), p=[ratio_train_split, ratio_val_split]) # not accurate enough :(
        train_val_assigns = np.ones(len(selected_imgs))
        train_val_assigns[:int(ratio_train_split * len(selected_imgs))] = 0
        np.random.shuffle(train_val_assigns)
        # add assignments to datasamples
        count_train_samples = 0
        count_val_samples = 0
        for i in range(len(selected_imgs)):
            selected_imgs[i].append(str(train_val_assigns[i]))
            if train_val_assigns[i] == 0:
                count_train_samples += 1
            elif train_val_assigns[i] == 1:
                count_val_samples += 1

        print(f"Total number of selected images: {len(selected_imgs)}.")
        print(f"Data is divided into {count_train_samples} train samples and {count_val_samples} validation samples.")

        # convert select_imgs list to .csv and return it
        # with open(os.path.join(data_dir, f"train_val_splitted_samples-{kwargs['dag_run'].run_id}.csv"), "w", newline="") as f:
        with open(os.path.join(output_data_dir, f"train_val_splitted_samples.csv"), "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(selected_imgs)
        
        print("Data was successfully loaded and assigned to train and val datasets according to given ratios.")

        return selected_imgs


    def __init__(self,
                 dag,
                 input_operator=None,
                 minio_operator=None,
                 env_vars=None,
                 **kwargs
                 ):

        self.name = 'train_val_datasplit'
        self.input_operator_out_dir = input_operator.operator_out_dir
        # self.minio_operator_out_dir = minio_operator.operator_out_dir
        # self.minio_operator_bucketname = minio_operator.bucket_name
        # self.minio_operator_run_dir = minio_operator.run_dir
        
        super().__init__(
            dag=dag,
            name=self.name,
            python_callable=self.start,
            **kwargs
        )
