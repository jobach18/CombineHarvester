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



if __name__=="__main__":
    main()
