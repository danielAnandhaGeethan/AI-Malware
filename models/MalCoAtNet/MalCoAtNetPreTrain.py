'@Author:NavinKumarMNK'
import pytorch_lightning as pl
import torch
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
import utils.utils as utils

from PIL import Image
import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder
from torch.utils.data import random_split, DataLoader
import numpy as np

class MalBinImgDatasetBB(torch.utils.data.Dataset):
    def __init__(self, root_dir):
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            #transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5), (0.5, 0.5)),
            transforms.HorizontalFlip(p=0.25),  
            transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 2.0)),
            transforms.RandomAffine(degrees=15, translate=(0.1, 0.1), scale=(0.9, 1.1), shear=15)
        ])
        self.root_dir = root_dir
        self.beg_annotation = self.root_dir + '/malbinimgannotation_beg.txt'
        self.mal_annotation = self.root_dir + '/malbinimgannotation_mal.txt' 
        self.beg_annotation = open(self.beg_annotation, 'r').readlines()
        self.mal_annotation = open(self.mal_annotation, 'r').readlines() 
        self.alt = 0

    def __len__(self):
        return max(len(self.beg_annotation), len(self.mal_annotation))

    def __getitem__(self, index):
        if self.alt == 0:
            img1 = self.mal_annotation[index]    
            img2_index = np.random.choice(len(self.mal_annotation))
            img2 = self.mal_annotation[img2_index]    
            label = 1
            self.alt = 1
        else:
            index = index % len(self.beg_annotation)
            img1 = self.beg_annotation[index]
            img2_index = np.random.choice(len(self.beg_annotation))
            img2 = self.beg_annotation[img2_index]
            label = 0
            self.alt = 0

        byte_image1 = self.root_dir + "/byteplot_imgs_RxR/256/" + img1.split('/')[-1]
        bigram_image1 = self.root_dir + "/bigram_imgs/imgs_dct/" + img1.split('/')[-1]

        byte_image2 = self.root_dir + "/byteplot_imgs_RxR/256/" + img2.split('/')[-1]
        bigram_image2 = self.root_dir + "/bigram_imgs/imgs_dct/" + img2.split('/')[-1]

        try:
            byte_image1 = Image.open(byte_image1)
            bigram_image1 = Image.open(bigram_image1)
            byte_image2 = Image.open(byte_image2)
            bigram_image2 = Image.open(bigram_image2)

            byte_image1 = self.transform(byte_image1)
            bigram_image1 = self.transform(bigram_image1)
            byte_image2 = self.transform(byte_image2)
            bigram_image2 = self.transform(bigram_image2)
        except Exception as e:
            print(e)
            index +=1 
            return self.__getitem__(index)

        tensor1 = torch.from_numpy(np.array(byte_image1)).unsqueeze(0)
        tensor2 = torch.from_numpy(np.array(bigram_image1)).unsqueeze(0)
        combined_tensor = torch.cat((tensor1, tensor2), dim=0).float()
        img1 = self.transform(combined_tensor)            
        
        tensor1 = torch.from_numpy(np.array(byte_image2)).unsqueeze(0)
        tensor2 = torch.from_numpy(np.array(bigram_image2)).unsqueeze(0)
        combined_tensor = torch.cat((tensor1, tensor2), dim=0).float()
        img2 = self.transform(combined_tensor)

        label = int(label)
        return img1, img2, label
    

class MalBinImgDatasetRGB(torch.utils.data.Dataset):
    def __init__(self, root_dir):
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.beg_annotation = root_dir + '/malbinimgannotation_beg.txt'
        self.mal_annotation = root_dir + '/malbinimgannotation_mal.txt' 
        self.beg_annotation = open(self.beg_annotation, 'r').readlines()
        self.mal_annotation = open(self.mal_annotation, 'r').readlines() 
        self.alt = 0

    def __len__(self):
        return max(len(self.beg_annotation) , len(self.mal_annotation))

    def __getitem__(self, index):
        if self.alt == 0:
            img1 = self.mal_annotation[index]
            label = 1
            self.alt = 1
            img2_index = np.random.choice(len(self.mal_annotation))
            img2 = self.mal_annotation[img2_index]
        else:
            index = index % len(self.beg_annotation)
            img1 = self.beg_annotation[index]
            img2_index = np.random.choice(len(self.beg_annotation))
            img2 = self.beg_annotation[img2_index]

            label = 0
            self.alt = 0

        
        img1 = Image.open(img1[:-1])
        img2 = Image.open(img2[:-1])

        img1 = self.transform(img1)
        img2 = self.transform(img2)

        label = int(label)
        return img1, img2, label
    
      
class MalCoAtNetSSLDataModule(pl.LightningDataModule):
    def __init__(self, root_dir,  batch_size, num_workers, val_split=0.02, test_split=0.08):
        super().__init__()
        self.root_dir = root_dir
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.val_split = val_split
        self.test_split = test_split
        
    
    def prepare_data(self):
        pass
    
    def setup(self, stage=None):
        full_dataset = MalBinImgDatasetBB(self.root_dir)
        total_len = len(full_dataset)
        val_len = int(self.val_split * total_len)
        test_len = int(self.test_split * total_len)
        train_len = total_len - val_len - test_len

        self.train_dataset, self.val_dataset, self.test_dataset = random_split(
            full_dataset, [train_len, val_len, test_len]
        )

    def train_dataloader(self):
        train_loader = DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            persistent_workers=True,

            )
        # 
        return train_loader

    def val_dataloader(self):
        val_loader = DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            persistent_workers=True,
        )
        return val_loader
    
    def test_dataloader(self):
        test_loader = DataLoader(
            self.test_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers
        )
        return test_loader

if (__name__ == '__main__'):
    data_parmas = utils.config_parse('MALBINIMG_BB_DATASET')
    data = MalBinImgDatasetRGB(data_parmas['root_dir'])
    print(len(data))

    datamodule = MalCoAtNetSSLDataModule(data_parmas['root_dir'], data_parmas['batch_size'], data_parmas['num_workers'])
    datamodule.setup()
    data = datamodule.train_dataloader()
    for (x, y) in data:
        print(x, y)
        break

