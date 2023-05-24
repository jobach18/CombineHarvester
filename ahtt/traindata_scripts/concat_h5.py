'''
script to concatenate the resulting h5 arrays
'''
import os
import pandas as pd
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-tag", "--TAG", help= "tag of the folder the h5s are in")
    parser.add_argument("-exp", "--Expectation", help= "expectation that the limit was calculated with, can be either exp-s, exp-b, exp-10 or exp-01", default='exp-s')
    args = parser.parse_args()
    #load the data from a specified directory with pandas dataframes in h5 files
    folder_path = "../data/"+args.TAG
    file_list = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.h5'):
            file_list.append(os.path.join(folder_path, file_name))

    dataframes = []
    for file_path in file_list:
        with pd.HDFStore(file_path, mode='r') as store:
            if 'df' in store:
                df = store['df']
                dataframes.append(df)

    concatenated_df = pd.concat(dataframes, ignore_index=True)
    concatenated_df.to_hdf('../data/'+args.TAG+'/train_data_'+args.Expectation+"_full.h5", key='df', mode='w')


if __name__=="__main__":
    main()
