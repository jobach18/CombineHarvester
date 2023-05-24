'''
script to plot the NLL
'''
import matplotlib
matplotlib.use('Agg')
import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-exp", "--Expectation", help= "expectation that the limit was calculated with, can be either exp-s, exp-b, exp-10 or exp-01", default='exp-s')
    parser.add_argument("-tag", "--Tag", help= "tag that the limits were calculated with before, gives the directory the roots are in.")
    args = parser.parse_args()
    #load the data from a specified directory with pandas dataframes in h5 files
    file_path = "../data/" + args.Tag+"/train_data_"+ args.Expectation  + "_full.h5"
    with pd.HDFStore(file_path, mode='r') as store:
        if 'df' in store:
            df = store['df']
    fig, ax1 = plt.subplots(1, 1)
    sns.histplot(df, x="limit1", ax=ax1)
    fig.savefig('limit1_'+args.Tag+'_'+args.Expectation+'.pdf', dpi=200)



if __name__=="__main__":
    main()
