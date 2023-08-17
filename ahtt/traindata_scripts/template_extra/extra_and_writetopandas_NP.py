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
    parser.add_argument("-tag", "--Tag", help= "tag that the limits were calculated with before, gives the directory the roots are in.")
    parser.add_argument("-id", "--JobId", help= "Id of this job")
    parser.add_argument("-js", "--JobSize", help= "size of the job in #jobs")
    parser.add_argument("-m", '--Mode', help="mode that the NLL was calculated with by combine", default='nll')
    args = parser.parse_args()
    expectation = args.Expectation 
    # Root folder where the search begins
    root_folder = "./"
    i = 0
    fail_ind = 0
    matching_folders = []
    # Find all folders starting with "A" in the root folder
    for subfolder in os.listdir(root_folder):
        pattern = r"subfold_\d+"
        subfolder_path = os.path.join(root_folder, subfolder)
        # Check if the subfolder is a directory
        if os.path.isdir(subfolder_path) and re.match(pattern, subfolder):
            matching_folders.extend([os.path.join(subfolder_path, folder) for folder in os.listdir(subfolder_path) if folder.startswith("A")][:])

    print(matching_folders)

    #calculate the folders for this job
    if int(args.JobSize) != 1:
        fold_per_job = int(len(matching_folders)/int(args.JobSize))
        if int(args.JobId) < int(args.JobSize)-1:
            fold_of_job = matching_folders[int(args.JobId)*fold_per_job:(int(args.JobId)+1)*fold_per_job]
        else:
            fold_of_job = matching_folders[int(args.JobId)*fold_per_job:]
    else:
        fold_of_job = matching_folders

    print(f'there are {len(fold_of_job)} files in this job')

    # Iterate over the matching folders
    for folder in tqdm(fold_of_job):
        subfolder_path = os.path.join(root_folder, folder)
        if args.Mode == "contour":
                # Build the path to the subfolder starting with "fc-results"
                try:
                    fc_results_folder_arr = (subfolder for subfolder in os.listdir(subfolder_path) if subfolder.startswith("fc-result"))
                    for fc_results_folder in fc_results_folder_arr:
                        if len(os.listdir(os.path.join(subfolder_path, fc_results_folder))) == 0:
                            pass
                        else:
                            break
                except NotADirectoryError:
                    print('failed')
                    fail_ind += 1
                    continue
                final_folder = os.path.join(subfolder_path, fc_results_folder)
        elif args.Mode == "nll":
            final_folder = os.path.join(root_folder, folder)
        # Check if the subfolder exist)s
        if os.path.exists(final_folder) and os.path.isdir(final_folder):
                # Find the .root file in the subfolder
                expectation = args.Expectation 
                if args.Mode == "nll":
                     root_file = next((file for file in os.listdir(final_folder) if file.endswith(".root") and expectation in str(file)), None)
                elif args.Mode == "contour":
                     root_file = next((file for file in os.listdir(final_folder) if file.endswith(expectation+".root")), None)
        # Check if a .root file was found
        if root_file is not None:
            # Open the .root file and read data from the "limits" branch into a pandas dataframe
            root_file_path = os.path.join(final_folder, root_file)
            #print(root_file_path)
            with uproot.open(root_file_path) as file:
                tree = file["limit"]
                quantE = tree["quantileExpected"].array(library="pd")
		# Get the list of branch names
		branch_names = tree.keys()
		# Create an empty dictionary to store data
		data_dict = {branch_name: tree[branch_name].array(library="pd")[quantE!=-1] for branch_name in branch_names}

		# Convert the dictionary to a Pandas DataFrame
                m1_value, m2_value, w1_value, w2_value = extract_info_from_foldername(folder)
                data_dict["m1"] = np.zeros_like(tree['nll'].array(library="pd")[quantE!=-1]) + m1_value
                data_dict["m2"] = np.zeros_like(tree['nll'].array(library="pd")[quantE!=-1]) + m2_value
                data_dict["w1"] = np.zeros_like(tree['nll'].array(library="pd")[quantE!=-1]) + w1_value
                data_dict["w2"] = np.zeros_like(tree['nll'].array(library="pd")[quantE!=-1]) + w2_value
		df = pd.DataFrame(data_dict)
    print(f' this job successfully processed {i} folder')
    print(f' {fail_ind} folders were tar.gz files')
    df.to_hdf('train_data_NP_'+expectation+"_"+args.JobId+'.h5', key='df', mode='w')
if __name__=="__main__":
    main()
