import matplotlib
matplotlib.use('Agg')
import argparse
import pandas as pd
import pandas.plotting
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
            #df.convert_dtypes(convert_floating=True)
            df = df.apply(pd.to_numeric, errors='coerce')
    print(f'the dataset has {len(df)} entries')
    fig, (ax1) = plt.subplots(1,1, figsize=(10,10))
    pd.plotting.scatter_matrix(df, ax=ax1)
    fig.savefig('plots/scattermatrix_'+args.Tag+'_'+args.Expectation+'.png',dpi=100)

if __name__=="__main__":
    main()

