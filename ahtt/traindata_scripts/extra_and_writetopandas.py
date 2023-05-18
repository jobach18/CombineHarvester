'''
snippet that extracts the limits from the files and writes them to a pandas dataframe
'''

import os
import re
import argparse
import uproot
import numpy as np
import pandas as pd
from tqdm import tqdm


def extract_info_from_foldername(folder_name):
    '''
     function to extract the info in the folder name:
     A_mX1_wX1__H_mX2_wX2
     returns:
        m1      float
        m2      float 
        w1      float 
        w2      float
    '''
    # Use regular expressions to extract the values
    pattern = r"A_(m\d+)_w(\d+p\d+)__H_(m\d+)_w(\d+p\d+)"
    matches = re.findall(pattern, folder_name)
    # Extracted values
    m1_value = float(matches[0][0][1:])  # m1000
    w1_value = matches[0][1]  # w5p0
    w1_value = float(re.findall(r'\d+', w1_value)[0]+'.'+re.findall(r'\d+', w1_value)[1])
    m2_value = float(matches[0][2][1:])
    w2_value = matches[0][3]
    w2_value = float(re.findall(r'\d+', w2_value)[0]+'.'+re.findall(r'\d+', w2_value)[1])
    return m1_value, m2_value, w1_value, w2_value 


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-exp", "--Expectation", help= "expectation that the limit was calculated with, can be either exp-s, exp-b, exp-10 or exp-01", default='exp-s')
    args = parser.parse_args()
    # Root folder where the search begins
    root_folder = "../run2/"
    df = pd.DataFrame(columns=['m1', 'm2', 'w1', 'w2', 'limit1', 'limit2'])
    i = 0 
    # Find all folders starting with "A" in the root folder
    matching_folders = [folder for folder in os.listdir(root_folder) if folder.startswith("A")]

    # Iterate over the matching folders
    for folder in tqdm(matching_folders):
        subfolder_path = os.path.join(root_folder, folder)
	# Build the path to the subfolder starting with "fc-results"
        fc_results_folder = next((subfolder for subfolder in os.listdir(subfolder_path) if subfolder.startswith("fc-result")), None)
        final_folder = os.path.join(subfolder_path, fc_results_folder)
        # Check if the subfolder exist)s
        if os.path.exists(final_folder) and os.path.isdir(final_folder):
                # Find the .root file in the subfolder
                expectation = args.Expectation 
                root_file = next((file for file in os.listdir(final_folder) if file.endswith(expectation+".root")), None)
        # Check if a .root file was found
        if root_file is not None:
            # Open the .root file and read data from the "limits" branch into a pandas dataframe
            root_file_path = os.path.join(final_folder, root_file)
            #with uproot.open(root_file_path) as file:
                #tree = file["limit"]
            dataframe = pd.concat(uproot.iterate(root_file_path, "limit", library='pd'))
            m1_value, m2_value, w1_value, w2_value = extract_info_from_foldername(folder)
            new_row = { "m1" : m1_value,
                        "m2" : m2_value,
                        "w1" : w1_value,
                        "w2" : w2_value,
                        "limit1" : dataframe["limit"][0],
                        "limit2" : dataframe["limit"][1],}
            df.loc[i] = new_row
            i = i +1
    df.to_hdf('train_data_'+expectation+'.h5', key='df', mode='w')
if __name__=="__main__":
    main()
