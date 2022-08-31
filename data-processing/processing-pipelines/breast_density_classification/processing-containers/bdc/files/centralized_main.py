# general
import argparse
from tqdm import tqdm
import os
import glob
import json
from distutils.dir_util import copy_tree

# ml stuff
import torch
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter


# from files
from resnet import ResNet50
from ddsm_data import DDSMDataset


# default variables, might be overwritten !
BATCH_SIZE = 1
NUM_WORKERS = 2
NUM_EPOCHS = 5
DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'   # use "local-only/base-python-gpu"
# DEVICE = 'cpu'    # for debugging; use "local-only/base-python-cpu"
VAL_FREQ = 5

# instantiate tensorboard's SummaryWriter
writer = SummaryWriter()


def train_epoch(network, loss_fn, optimizer, scheduler, data_loader, epoch):

    # set network into train mode
    network.train()
    print(f"Network in training mode? {network.training}")

    # iterate over batches
    loop = tqdm(data_loader)
    losses = []
    running_loss = 0
    for batch_idx, data_sample in enumerate(loop):
        image = data_sample['image'].to(DEVICE) # .squeeze(1)
        label = data_sample['label'].to(DEVICE)
        optimizer.zero_grad()

        # forward
        preds = network(image.float())

        # loss calculation
        loss = loss_fn(preds, label)
        losses.append(loss.item())

        # backward
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

        if batch_idx % 100 == 0 and batch_idx > 0:
            print(f'Loss [{epoch+1}, {batch_idx}](epoch, minibatch): ', running_loss / 100)
            running_loss = 0.0

    avg_loss = sum(losses)/len(losses)
    scheduler.step(avg_loss)

    return avg_loss, network


def val_epoch(network, loss_fn, data_loader, epoch):

    # set network into eval mode
    network.eval()
    print(f"Network in training mode? {network.training}")

    # iterate over batches
    loop = tqdm(data_loader)
    losses = []
    correct = 0
    total = 0
    with torch.no_grad():
        for batch_idx, data_sample in enumerate(loop):
            image = data_sample['image'].to(DEVICE) # .squeeze(1)
            label = data_sample['label'].to(DEVICE)

            # forward
            preds = network(image.float())

            # loss calculation
            loss = loss_fn(preds, label)
            losses.append(loss.item())

            _, predicted = torch.max(preds.data, 1)
            total += label.size(0)
            correct += (predicted == label).sum().item()
    
    avg_loss = sum(losses)/len(losses)
    acc = 100 * (correct / total)

    return avg_loss, acc

def main():
    # for inputs from "get_input" operator
    MY_BATCHES_INPUT_DIR = os.environ['BATCHES_INPUT_DIR']  # data/batch
    MY_BATCH_NAME = os.environ['BATCH_NAME']                # batch
    MY_DAG_ID = os.environ['DAG_ID']                        # breast-density-classification
    MY_OPERATOR_IN_DIR = os.environ['OPERATOR_IN_DIR']      # get-input-data or train_val_split
    MY_OPERATOR_OUT_DIR = os.environ['OPERATOR_OUT_DIR']    # breast-density-classifier
    MY_RUN_ID = os.environ['RUN_ID']                        # breast-density-classification-220705...
    MY_WORKFLOW_DIR = os.environ['WORKFLOW_DIR']            # data

    # for inputs from "get_from_minio" operator
    # MY_MINIO_DIR = os.path.join('/minio', os.environ['MINIO_OPERATOR_OUT_DIR'])
    # my_minio_bucket_dir = os.path.join('/minio', os.environ['MINIO_OPERATOR_BUCKETNAME'])
    # my_metadata_path = os.path.join(my_minio_bucket_dir, 'batch', str('train_val_splitted_samples-' + MY_RUN_ID + '.csv'))        # old w/ run_id in .csv-name
    # my_metadata_path = os.path.join('/', MY_WORKFLOW_DIR, os.environ['SECOND_OPERATOR_OUT_DIR'], 'train_val_splitted_samples.csv')  # with train_val_splitted_data.csv from second_input_operator
    my_metadata_path = os.path.join('/', MY_WORKFLOW_DIR, MY_OPERATOR_IN_DIR, 'train_val_splitted_samples.csv')                     # new: w/ train_val_splitted_data.csv and .dcm image data from train_val_split-operator
    my_model_out_dir = os.path.join("/", MY_WORKFLOW_DIR, MY_OPERATOR_OUT_DIR)

    # for input parameter defined in Meta Dashboard's UI
    with open(os.path.join('/', MY_WORKFLOW_DIR, 'conf/conf.json'), 'r') as f:
        ui_confs = json.load(f)
    BATCH_SIZE = ui_confs['workflow_form']['batch_size']
    NUM_EPOCHS = ui_confs['workflow_form']['num_epochs']

    # for input parameter defined in Meta Dashboard's UI
    with open(os.path.join('/', MY_WORKFLOW_DIR, 'conf/conf.json'), 'r') as f:
        ui_confs = json.load(f)
    BATCH_SIZE = ui_confs['workflow_form']['batch_size']
    NUM_EPOCHS = ui_confs['workflow_form']['num_epochs']
    VAL_FREQ = ui_confs['workflow_form']['val_frequency']
    CROP_SIZE = ui_confs['workflow_form']['crop_size']

    # print hyperparameter
    print(f"Hyperparameter: batch_size={BATCH_SIZE} ; num_workers={NUM_WORKERS} ; num_epochs={NUM_EPOCHS} ; device={DEVICE} ; val_freq={VAL_FREQ} !")
    
    # data
    train_transforms = transforms.Compose([
        # transforms.ToPILImage(),
        transforms.ToTensor(),
        transforms.RandomHorizontalFlip(),
        transforms.RandomCrop(CROP_SIZE, padding=4),
        transforms.Normalize(0.5, 0.5),
    ])
    val_transforms = transforms.Compose([
        transforms.ToTensor(),
        transforms.CenterCrop(CROP_SIZE),
        transforms.Normalize(0.5, 0.5),
    ])

    imagedata_dir=os.path.join('/', MY_WORKFLOW_DIR, MY_OPERATOR_IN_DIR)
    train_ddsm_dataset = DDSMDataset(data_transforms=train_transforms,
                               data_dir=MY_WORKFLOW_DIR,
                               # imagedata_dir=MY_BATCHES_INPUT_DIR,
                               imagedata_dir=imagedata_dir,
                               metadata_path=my_metadata_path,
                               mode='train')
    val_ddsm_dataset = DDSMDataset(data_transforms=val_transforms,
                               data_dir=MY_WORKFLOW_DIR,
                               # imagedata_dir=MY_BATCHES_INPUT_DIR,
                               imagedata_dir=imagedata_dir,
                               metadata_path=my_metadata_path,
                               mode='val')
    print("Datasets are ready!")
    train_loader = DataLoader(train_ddsm_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS, drop_last=True)
    val_loader = DataLoader(val_ddsm_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS, drop_last=True)
    print(f"Data preparation is finished with train dataset of {train_ddsm_dataset.__len__()} samples and val dataset of {val_ddsm_dataset.__len__()} samples.")
    
    # ML stuff
    net = ResNet50(num_classes=4, channels=1)
    print("Network defined: ResNet50.")
    pretrained_models = glob.glob(os.path.join(my_model_out_dir, '**/*.model'), recursive=True)
    if os.path.exists(my_model_out_dir) and len(pretrained_models) > 0:
        print(f"Loading model weights from pretrained model weight checkpoint: {pretrained_models[0]}")
        # net.load_from_state_dict(torch.load(pretrained_models[0]))
        # net = torch.load(pretrained_models[0])
        checkpoint = torch.load(pretrained_models[0])
        state_dict = checkpoint['state_dict']
        net.load_state_dict(state_dict)
    net = net.to(DEVICE)
    print(f"Set NN to device: {DEVICE}")
    loss_fn = nn.CrossEntropyLoss()
    print("Loss function defined: Cross-Entropy Loss.")
    optimizer = optim.SGD(net.parameters(), lr=0.1, momentum=0.9, weight_decay=0.0001)
    print("Optimizer defined: SGD.")
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, factor = 0.1, patience=5)
    print("Learning rate scheduler defined.")

    print(f"ML stuff defined! Start Training on device: {DEVICE}")

    # iterate over epochs to train and eval
    for epoch in range(NUM_EPOCHS):

        if DEVICE != 'cpu':
            print('Clear cache!')
            torch.cuda.empty_cache()

        # train
        avg_train_loss, net = train_epoch(net, loss_fn, optimizer, scheduler, train_loader, epoch)
        print(f"Average training loss after {epoch+1} training epochs: {avg_train_loss}")
        writer.add_scalar("Loss/train", avg_train_loss, epoch)

        # eval
        if ((epoch + 1) % VAL_FREQ) == 0:
            avg_val_loss, val_accuracy = val_epoch(net, loss_fn, val_loader, epoch)
            print(f"Average validation loss after {epoch+1} training epochs: {avg_val_loss}")
            print(f"Average validation accuracy after {epoch+1} training epochs: {val_accuracy}")
            writer.add_scalar("Loss/val", avg_val_loss, epoch)
            writer.add_scalar("Accuracy/val", val_accuracy, epoch)
  
    print("Training finished!")

    # save trained model to out_dir
    os.makedirs(my_model_out_dir, exist_ok=True)
    out_fname1 = os.path.join(my_model_out_dir, "model_final_checkpoint.model.pkl")
    out_fname2 = os.path.join(my_model_out_dir, "model_final_checkpoint.model")
    print(f"Save final model to {out_fname1} and to {out_fname2}.")
    net.to('cpu')
    torch.save({'epoch': epoch,
                'state_dict': net.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                },
                out_fname1)
    torch.save({'epoch': epoch,
                'state_dict': net.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                },
                out_fname2)

    # save tensorboard's event.out.tfevent-file to out_dir and to minio-bucket 'tensorboard'
    minio_tensorboard_dir = os.path.join('/minio/tensorboard', MY_RUN_ID, MY_OPERATOR_OUT_DIR)
    os.makedirs(minio_tensorboard_dir, exist_ok=True)
    copy_tree('/kaapanasrc/runs', minio_tensorboard_dir)    # copy to minio
    copy_tree('/kaapanasrc/runs', my_model_out_dir)         # copy to operator out_dir

    print("Processing finished!")


if __name__ == "__main__":
    main()