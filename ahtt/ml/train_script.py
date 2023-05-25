'''
script for training a network with the machinery from network.py
'''

import torch
import network
import numpy as np
import pandas as pd


def main():
    #load the data from a specified directory with pandas dataframes in h5 files
    folder_path = "../data/try/"
    with pd.HDFStore(file_path, mode='r') as store:
        if 'df' in store:
            df = store['df']

    #make the x a vector of m1, w1, m2, w2 as an np array
    selected_cols = ["m1", "w1", "m2", "w2"]
    xs = df[selected_cols].values
    ys = df["limit2"].values
    #put this into a pytorch dataset
    dataset_loc = network.Dataset(xs, ys)
    model = network.Model((4,), 128)

    trainer = network.Trainer(model, dataset_loc, torch.nn.MSELoss())
    trainer.train(10, 0.001)
    print(model.parameters())




if __name__=="__main__":
    main()
