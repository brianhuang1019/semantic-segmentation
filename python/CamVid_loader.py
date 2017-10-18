# -*- coding: utf-8 -*-

from __future__ import print_function

from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import scipy.misc
import random
import os

import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import utils


root_dir   = "CamVid/"
train_file = os.path.join(root_dir, "train.csv")  # img_name & label_name

num_class = 32
means     = (0.4368, 0.2475, 0.3281)
stds      = (0.1681, 0.2247, 0.2743)
h, w      = 720, 960
crop_h    = int(int(h) / 32 * 32 * 2 / 3)
crop_w    = int(int(w) / 32 * 32 * 2 / 3)


class CamVidDataset(Dataset):

    def __init__(self, csv_file, n_class=num_class, crop=True, flip_rate=0.5):
        self.data      = pd.read_csv(csv_file)
        self.means     = means  # mean of three channels after divide to 255
        self.stds      = stds   # std of three channels after divide to 255
        self.n_class   = n_class

        self.crop      = crop
        self.crop_h    = crop_h
        self.crop_w    = crop_w
        self.flip_rate = flip_rate

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        img_name   = self.data.ix[idx, 0]
        img        = scipy.misc.imread(img_name, mode='RGB')
        label_name = self.data.ix[idx, 1]
        label      = np.load(label_name)

        if self.crop:
            h, w, _ = img.shape
            top   = np.random.randint(0, h - self.crop_h)
            left  = np.random.randint(0, w - self.crop_w)
            img   = img[top:top + self.crop_h, left:left + self.crop_w]
            label = label[top:top + self.crop_h, left:left + self.crop_w]

        if random.random() < self.flip_rate:
            img   = np.fliplr(img)
            label = np.fliplr(label)

        # convert to tensors
        h, w, _ = img.shape
        img = torch.from_numpy(img.copy()).permute(2, 0, 1).float().div(255)
        img[0].sub_(self.means[0]).div_(self.stds[0])
        img[1].sub_(self.means[1]).div_(self.stds[1])
        img[2].sub_(self.means[2]).div_(self.stds[2])
        label = torch.from_numpy(label.copy()).long()

        # create one-hot encoding
        target = torch.zeros(self.n_class, h, w)
        for c in range(self.n_class):
            target[c][label == c] = 1

        sample = {'X': img, 'Y': target, 'l': label}

        return sample


def show_batch(batch):
    img_batch = batch['X']
    img_batch[:,0,...].mul_(stds[0]).add_(means[0])
    img_batch[:,1,...].mul_(stds[1]).add_(means[1])
    img_batch[:,2,...].mul_(stds[2]).add_(means[2])
    batch_size = len(img_batch)

    grid = utils.make_grid(img_batch)
    plt.imshow(grid.numpy().transpose((1, 2, 0)))

    plt.title('Batch from dataloader')


if __name__ == "__main__":
    train_data = CamVidDataset(csv_file=train_file)

    # show a batch
    batch_size = 4
    for i in range(batch_size):
        sample = train_data[i]
        print(i, sample['X'].size(), sample['Y'].size())

    dataloader = DataLoader(train_data, batch_size=batch_size, shuffle=True, num_workers=4)

    for i, batch in enumerate(dataloader):
        print(i, batch['X'].size(), batch['Y'].size())
    
        # observe 4th batch
        if i == 3:
            plt.figure()
            show_batch(batch)
            plt.axis('off')
            plt.ioff()
            plt.show()
            break
