'''
script to plot the NLL
'''
import matplotlib
matplotlib.use('Agg')
import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def overviewplot(df, args):
    fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(30, 10))
    sns.histplot(df, x="limit1", ax=ax1)
    sns.histplot(df, x="limit2", ax=ax2)
    sns.histplot(df, x="m1", ax=ax3)
    sns.histplot(df, x="m2", ax=ax4)
    sns.histplot(df, x="limit2", hue="m1", ax=ax5, multiple="stack")
    sns.histplot(df, x="limit2", hue="m2", ax=ax6, multiple="stack")
    plt.tight_layout()
    fig.savefig('limits_'+args.Tag+'_'+args.Expectation+'.pdf', dpi=200)


def limit_asfun(df, x_tag, hue_tags, args):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 24))
    sns.lineplot(df, x=x_tag, y="limit2", hue=hue_tags[0], ax=ax1)
    sns.lineplot(df, x=x_tag, y="limit2", hue=hue_tags[1], ax=ax2)
    sns.lineplot(df, x=x_tag, y="limit2", hue=hue_tags[2], ax=ax3)
    plt.tight_layout()
    fig.savefig('limitsasfun_averageovermissingparserrorband_'+x_tag+"_"+args.Tag+'_'+args.Expectation+'.pdf', dpi=200)

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
    overviewplot(df, args)
    df_tags = ["m1", "m2", "w1", "w2"]
    for i, ikey in enumerate(df_tags):
       other_keys = [elem for j, elem in enumerate(df_tags) if j != i]
       limit_asfun(df, ikey, other_keys, args)




if __name__=="__main__":
    main()
