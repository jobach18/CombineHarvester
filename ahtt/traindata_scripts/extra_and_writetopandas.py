'''
snippet that extracts the limits from the files and writes them to a pandas dataframe
'''

import os
import re
import uproot
import numpy as np
import pandas as pd



def main():
    # Root folder where the search begins
    root_folder = "../data1/"
    df = pd.DataFrame(columns=['m1', 'm2', 'w1', 'w2', 'limit1', 'limit2'])

    # Find all folders starting with "A" in the root folder
    matching_folders = [folder for folder in os.listdir(root_folder) if folder.startswith("A")]

    # Iterate over the matching folders
    for folder in matching_folders:
        subfolder_path = os.path.join(root_folder, folder)
	# Build the path to the subfolder starting with "fc-results"
        fc_results_folder = next((subfolder for subfolder in os.listdir(subfolder_path) if subfolder.startswith("fc-result")), None)
        print(fc_results_folder)
        final_folder = os.path.join(subfolder_path, fc_results_folder)
        # Check if the subfolder exists
        if os.path.exists(final_folder) and os.path.isdir(final_folder):
                # Find the .root file in the subfolder
                root_file = next((file for file in os.listdir(final_folder) if file.endswith(".root")), None)
        # Check if a .root file was found
        if root_file is not None:
            # Open the .root file and read data from the "limits" branch into a pandas dataframe
            root_file_path = os.path.join(final_folder, root_file)
            #with uproot.open(root_file_path) as file:
                #tree = file["limit"]
            dataframe = pd.concat(uproot.iterate(root_file_path, "limit", library='pd'))
            # Use regular expressions to extract the values
            pattern = r"A_(m\d+)_w(\d+p\d+)__H_(m\d+)_w(\d+p\d+)"
            matches = re.findall(pattern, folder)
            print(matches)
            # Extracted values
            m1_value = matches[0][0]  # m1000
            w1_value = matches[0][1]  # w5p0
            m2_value = matches[0][2]
            w2_value = matches[0][3]
            print(f"Dataframe from {root_file_path}")
            print(dataframe["limit"][0])
            new_row = { "m1" : m1_value,
                        "m2" : m2_value,
                        "w1" : w1_value,
                        "w2" : w2_value,
                        "limit1" : dataframe["limit"][0],
                        "limit2" : dataframe["limit"][1],}
            df.append(new_row, ignore_index=True)
            print(new_row)
            print(df)
            exit()   

if __name__=="__main__":
    main()
