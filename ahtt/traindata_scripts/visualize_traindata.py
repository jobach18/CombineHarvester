'''
visualize the train data
'''
import argparse
import seaborn as sns
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-in", "--Input", help= "input h5 file with the dataframe", default='train_data.h5')
    args = parser.parse_args()
    df = pd.read_hdf(args.Input, key='df')
    snfig = sns.lmplot('w1','limit1',data=df)
    plt.savefig(args.Input+"_vis.pdf", dpi=200)


if __name__=="__main__":
    main()
