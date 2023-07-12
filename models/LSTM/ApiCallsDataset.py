"@author: NavinKumarMNK"
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from torch.utils.data import random_split, Dataset, DataLoader
import pytorch_lightning as pl
import torch
import utils.utils as utils
import numpy as np
import pandas as pd

class ApiCallsDataset(Dataset):
    def __init__(self, annotation:str, data_dir_path:str):
        self.data_dir_path = utils.ROOT_PATH + data_dir_path
        self.dataset = pd.read_csv(self.data_dir_path + annotation)
        
    def __len__(self):
        return len(self.dataset)
    
    def __getitem__(self, index:int):
        while True:
            file_name = self.dataset.iloc[index, 1] + '.npy'
            label = self.dataset.iloc[index, 2]
            file_path = self.data_dir_path + "samples/"+ file_name
            try:
                data = np.load(file_path)
            except FileNotFoundError:
                if (index >= len(self.dataset)):
                    index = 0
                index+=1
                continue
                
            data = torch.tensor(data)
            
            break
        return data, label

class ApiCallsDataModule(pl.LightningDataModule):
    def __init__(self, annotation, data_dir_path, batch_size, num_workers):
        super(ApiCallsDataModule, self).__init__()
        self.batch_size = batch_size
        self.num_workers = num_workers 
        self.annotation = annotation
        self.data_dir = data_dir_path

    def setup(self, stage=None):
        dataset = ApiCallsDataset(self.annotation, self.data_dir)
        total_len = len(dataset)        
        val_len = int(0.1 * total_len)
        test_len = int(0.1 * total_len)
        train_len = total_len - val_len - test_len

        self.train_dataset, self.val_dataset, self.test_dataset = random_split(
            dataset, [train_len, val_len, test_len]
        )
    
    def train_dataloader(self):
        
        train_loader = DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            collate_fn=self.collate_fn
        )
        return train_loader

    def val_dataloader(self):
        val_loader = DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            collate_fn=self.collate_fn
        )
        return val_loader

    def test_dataloader(self):
        test_loader = DataLoader(
            self.test_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            collate_fn=self.collate_fn
        )
        return test_loader

    def collate_fn(self, batch):
        max_length = 1000
        # Pad the sequences to the maximum length
        padded_seqs = torch.nn.utils.rnn.pad_sequence(
            [item[0] for item in batch],
            batch_first=True,
            padding_value=0,
        )
        # Get the labels for the sequences
        labels = torch.tensor([item[1] for item in batch])
        return padded_seqs, labels

if __name__ == '__main__':
    params = utils.config_parse('APICALLS_DATASET')
    data_module = ApiCallsDataModule(
        annotation=params['annotation'],
        data_dir_path=params['data_dir_path'],
        batch_size=params['batch_size'],
        num_workers=params['num_workers']
    )
    data_module.setup()
    train_loader = data_module.train_dataloader()
    for data, label in train_loader:
        print(data.shape, label.shape)
        break
